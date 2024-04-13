# api_handler.py
import requests
import os
from dotenv import load_dotenv
from data_models import run

# TODO: create run script that imports env vars
load_dotenv()
BASE_URL = os.getenv("ASSISTANTS_API_URL")


def update_run(thread_id: str, run_id: str, run_update: run.RunUpdate) -> run.Run:
    """
    Update the status of a Run.

    Parameters:
    thread_id (str): The ID of the thread.
    run_id (str): The ID of the run.
    new_status (str): The new status to set for the run.

    Returns:
    bool: True if the status was successfully updated, False otherwise.
    """
    update_url = f"{BASE_URL}/ops/threads/{thread_id}/runs/{run_id}"
    update_data = run_update.model_dump(exclude_none=True)

    response = requests.post(update_url, json=update_data)

    if response.status_code == 200:
        return run.Run(**response.json())
    else:
        return None


# You can add more API functions as
