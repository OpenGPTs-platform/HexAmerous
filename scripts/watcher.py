import os
import signal
import subprocess
import platform
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class ChangeHandler(PatternMatchingEventHandler):
    def __init__(
        self,
        restart,
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=True,
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self.restart = restart

    def on_any_event(self, event):
        self.restart()


class Watcher:
    def __init__(self, command):
        self.command = command
        self.process = None
        self.observer = Observer()

    def run(self):
        event_handler = ChangeHandler(
            self.restart,
            ignore_patterns=[
                "*.log",
                "*.pyc",
                "__pycache__/*",
                "*.swp",
                "*.swo",
            ],
        )
        self.observer.schedule(event_handler, path='./src', recursive=True)
        self.observer.start()
        self.start_process()
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.observer.stop()
            self.observer.join()
            self.stop_process()
            print("Shutting down gracefully...")

    def start_process(self):
        if platform.system() == 'Windows':
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            self.process = subprocess.Popen(
                self.command, shell=True, preexec_fn=os.setsid
            )

    def stop_process(self):
        if self.process:
            if platform.system() == 'Windows':
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()

    def restart(self):
        print("File change detected. Restarting process...")
        self.stop_process()
        self.start_process()


if __name__ == "__main__":
    command = "python ./src/consumer.py"
    watcher = Watcher(command)
    watcher.run()
