from flask import current_app
import os
import schedule
from time import sleep
from threading import Thread

from config import Config
from app.modules.management_suggestions import generate_suggestions
from app.modules.inventory_cleanup import remove_empty_lots

TASKS = {
    "auto_suggestions": generate_suggestions,
    "auto_cleanup": remove_empty_lots
}


class TaskScheduler:
    def __init__(self):
        self.runner_thread = None
        self.instant_tasks = []
        self.app_context = current_app.app_context()

    def run_pending(self, app_context):
        if os.path.exists(".task_scheduler_running"):
            print(
                "[TASK SCHEDULER] Another instance of task scheduler is already running! Exiting...")
            return

        with open(".task_scheduler_running", "w") as file:
            file.write(
                "This file is used to check if the task scheduler is running.\nIf the task scheduler refuses to start, delete this file manually.")

        if app_context is None:
            print("[TASK SCHEDULER] Failed to start due to missing app context!")
        else:
            print("[TASK SCHEDULER] Started scheduled task runner!")
            with app_context:
                while len(schedule.jobs) > 0 or len(self.instant_tasks) > 0:
                    if len(self.instant_tasks) > 0:
                        tasks = self.instant_tasks.copy()
                        for task in tasks:
                            TASKS[task]()
                            self.instant_tasks.remove(task)
                    schedule.run_pending()
                    sleep(1)

        os.remove(".task_scheduler_running")
        print("[TASK SCHEDULER] Stopped scheduled task runner!")

    def queue_task_asap(self, task: str):
        if task not in TASKS.keys():
            raise Exception("[TASK SCHEDULER] Invalid task name")

        self.instant_tasks.append(task)

        if self.runner_thread is None:
            print(
                "[TASK SCHEDULER] WARNING: Instant task scheduled but task scheduler is not running!")

    def start(self):
        if os.path.exists(".task_scheduler_running"):
            print("[TASK SCHEDULER] Task scheduler is already running!")
            return

        print("[TASK SCHEDULER] Adding scheduled tasks...")
        try:
            for task in Config.CONFIG_DATA.get("scheduled_tasks"):
                if Config.CONFIG_DATA["scheduled_tasks"][task] != "disabled" and task in TASKS.keys():
                    schedule.every().day.at(Config.CONFIG_DATA["scheduled_tasks"][task]).do(
                        TASKS[task]).tag(task)
                    print(f"[TASK SCHEDULER] Queued task '{task}'")
                else:
                    print(
                        f"[TASK SCHEDULER] Task '{task}' is disabled or invalid, skipping...")

            if self.runner_thread is None:
                self.runner_state = True
                self.runner_thread = Thread(
                    target=self.run_pending, daemon=True, args=(self.app_context,))
                self.runner_thread.start()

        except Exception as e:
            print("[TASK SCHEDULER] Error starting scheduled tasks:", str(e))

    def stop(self, job: str = None):
        if job is None:
            print("[TASK SCHEDULER] Removing all scheduled tasks...")
            schedule.clear()
            self.instant_tasks.clear()
        else:
            print(f"[TASK SCHEDULER] Removing scheduled task '{job}'...")
            if (job not in TASKS.keys()):
                raise Exception("[TASK SCHEDULER] Invalid job name")

            schedule.clear(job)

        if len(schedule.jobs) == 0 and len(self.instant_tasks) == 0 and self.runner_thread is not None:
            self.runner_thread.join()
