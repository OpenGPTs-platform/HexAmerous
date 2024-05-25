import os
import signal
import subprocess
import platform
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, restart):
        self.restart = restart

    def on_any_event(self, event):
        self.restart()


class Watcher:
    def __init__(self, command):
        self.command = command
        self.process = None
        self.observer = Observer()

    def run(self):
        event_handler = ChangeHandler(self.restart)
        self.observer.schedule(event_handler, path='.', recursive=True)
        self.observer.start()
        self.start_process()
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

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

    def restart(self):
        print("File change detected. Restarting process...")
        if self.process:
            if platform.system() == 'Windows':
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()
        self.start_process()


if __name__ == "__main__":
    command = "python ./src/consumer.py"
    watcher = Watcher(command)
    watcher.run()
