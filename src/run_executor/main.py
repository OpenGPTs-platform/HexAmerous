from typing import Dict, Any, Optional, List
from constants import PromptKeys
from utils.tools import ActionItem, Actions, tools_to_map
from utils.ops_api_handler import create_message_runstep, update_run
from data_models import run
from openai.types.beta.threads import ThreadMessage
from utils.openai_clients import assistants_client
from openai.types.beta.thread import Thread
from openai.types.beta import Assistant
from openai.pagination import SyncCursorPage
from agents import router, coala
import json

# TODO: add assistant and base tools off of assistant


class ExecuteRun:
    def __init__(self, thread_id: str, run_id: str, run_config: Dict[str, Any] = {}):
        self.run_id = run_id
        self.thread_id = thread_id
        self.assistant_id: Optional[str] = None
        self.run_config = run_config

        self.run: Optional[run.Run] = None
        self.messages: Optional[SyncCursorPage(ThreadMessage)] = None
        self.thread: Optional[Thread] = None
        self.assistant: Optional[Assistant] = None
        self.tools_map: Optional[dict[str, ActionItem]] = None
        self.runsteps: Optional[SyncCursorPage[run.RunStep]] = None
        # TODO: add assistant and base tools off of assistant

    def execute(self):
        # Create an instance of the RunUpdate schema with the new status
        run_update = run.RunUpdate(status=run.RunStatus.IN_PROGRESS.value)

        # Call the API handler to update the run status
        updated_run = update_run(self.thread_id, self.run_id, run_update)

        if not updated_run:
            print(f"Error updating run status for {self.run_id}. Aborting execution.")
            return

        self.run = updated_run
        print("Run: ", self.run, "\n\n")

        # Get the thread messages
        # TODO: should only populate these entities once
        thread = assistants_client.beta.threads.retrieve(
            thread_id=self.thread_id,
        )
        self.thread = thread

        assistant = assistants_client.beta.assistants.retrieve(
            assistant_id=self.run.assistant_id,
        )
        self.assistant_id = assistant.id
        self.assistant = assistant
        self.tools_map = tools_to_map(self.assistant.tools)

        messages = assistants_client.beta.threads.messages.list(
            thread_id=self.thread_id, order="asc"
        )
        self.messages = messages
        print("\n\nMain Messages: ", self.messages, "\n\n")

        router_agent = router.RouterAgent()
        router_response = router_agent.generate(self.tools_map, self.messages)
        print("Response: ", router_response, "\n\n")
        if router_response != PromptKeys.TRANSITION.value:
            create_message_runstep(
                self.thread_id, self.run_id, self.run.assistant_id, router_response
            )
            update_run(
                self.thread_id,
                self.run_id,
                run.RunUpdate(status=run.RunStatus.COMPLETED.value),
            )
            print("Generating response")
            print(f"Finished executing run {self.run_id}")
            return
        print("Transitioning")

        coala_class = coala.CoALA(self.run_id, self.thread_id, self.assistant_id)
        self.assistant = coala_class.retrieve_assistant()
        self.messages = coala_class.retrieve_messages()
        self.runsteps = coala_class.retrieve_runsteps()
        coala_class.set_assistant_tools()

        coala_class.generate_question()

        max_steps = 5
        curr_step = 0
        while coala_class.react_steps[-1].step_type != coala.ReactStepType.FINAL_ANSWER:
            self.messages = coala_class.retrieve_messages()
            self.runsteps = coala_class.retrieve_runsteps()
            coala_class.generate_thought()
            coala_class.generate_action()
            coala_class.execute_action(Actions(coala_class.react_steps[-1].content))
            print(f"""\n\nStep {curr_step} completed.
with react steps:
{json.dumps([step.model_dump() for step in coala_class.react_steps], indent=2)}""")
            curr_step += 1
            if curr_step >= max_steps:
                break
        # if while completes from the if statement, then print("success") else if it breaks from the while loop, print("failure")
        if coala_class.react_steps[-1].step_type == coala.ReactStepType.FINAL_ANSWER:
            run_update = run.RunUpdate(status=run.RunStatus.COMPLETED.value)
        else:
            run_update = run.RunUpdate(status=run.RunStatus.FAILED.value)
        updated_run = update_run(self.thread_id, self.run_id, run_update)

        print(f"""\n\nFinished executing run with status {run_update.status} after {curr_step} steps.""")

    def get_run_id(self) -> str:
        return self.run_id

    def get_run_config(self) -> Dict[str, Any]:
        return self.run_config

    def get_run_state(self) -> str:
        return "RUNNING"

    def get_run_logs(self) -> str:
        return "Logs for run"

    def get_run_result(self) -> Dict[str, Any]:
        return {"result": "result"}

    def get_run_artifacts(self) -> Dict[str, Any]:
        return {"artifacts": "artifacts"}
