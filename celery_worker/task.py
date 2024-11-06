import random
from datetime import datetime, timedelta

import pytz
from celery import Task, states
from celery.exceptions import Ignore
from seleniumbase import SB, BaseCase
from sqlmodel import Session, select

from app import crud
from app.api.deps import get_db
from app.models.account_model import Account
from app.models.task_model import TaskStatus, UserTask, UserTaskCreate
from automation.main import MainApp
from automation.utils.logging_utils import logger
from automation.utils.sb_utils import sb_utils
from celery_worker.celery_worker import celery_worker


@celery_worker.task(
    bind=True,
    track_started=True,
)
def process_task(self, task_id: str):
    """
    Process a single account's task with enhanced undetection measures.
    """
    with next(get_db()) as session:
        try:
            # Database operations
            user_task = session.get(UserTask, task_id)
            if not user_task:
                raise ValueError("Task not found")
            account = session.get(Account, user_task.account_id)
            if not account:
                raise ValueError("Associated account not found")

            user_task.status = TaskStatus.PROCESSING
            session.add(user_task)
            session.commit()

            self.update_state(
                state=states.STARTED,
                meta={
                    "account": account.email,
                    "status": "Processing started",
                    "progress": 0,
                },
            )

            app = MainApp(user_task.user_id)
            platforms = account.platforms.split(",")

            options = sb_utils.get_undetectable_options()

            with SB(uc=True) as sb:
                # make full screen
                sb.driver.maximize_window()
                sb.driver.set_window_size(1920, 1080)
                # zoom out to 80%
                sb.driver.execute_script("document.body.style.zoom='80%'")

                try:
                    self.update_state(
                        state="PROCESSING",
                        meta={
                            "status": f"Running automation for {account.email}",
                            "progress": 25,
                        },
                    )

                    # Execute task with human-like behavior
                    app.run_for_account(
                        sb,
                        account.google_drive_folder_id,
                        account.email,
                        account.password,
                        platforms,
                    )

                    sb_utils.random_delay()

                    self.update_state(
                        state="COMPLETED",
                        meta={"status": "Automation completed", "progress": 100},
                    )
                    user_task.status = TaskStatus.COMPLETED
                    user_task.progress = 100

                except Exception as e:
                    logger.error(f"Error processing account {account.email}: {str(e)}")
                    self.update_state(
                        state=states.FAILURE,
                        meta={
                            "exc_type": type(e).__name__,
                            "exc_message": str(e),
                            "account": account.email,
                            "progress": 100,
                        },
                    )
                    user_task.status = TaskStatus.FAILED
                    user_task.progress = 100
                    session.add(user_task)
                    session.commit()
                    raise Ignore()

            session.add(user_task)
            session.commit()

        finally:
            session.close()


@celery_worker.task
def run_user_automation(user_id: int):
    with next(get_db()) as session:
        # Get all accounts for the user
        statement = select(Account).where(Account.owner_id == user_id)
        accounts = session.exec(statement).all()

        if not accounts:
            logger.warning(f"No accounts found for user_id: {user_id}")
            return

        # Get the current time in UTC
        now = datetime.now(pytz.utc)

        # Initialize scheduled_time to now
        scheduled_time = now

        # Number of runs per day
        num_rounds_per_day = random.randint(10, 15)

        # Task duration and buffer time (in minutes)
        min_task_duration = 5
        max_task_duration = 6
        buffer_minutes = 1  # Time between tasks to prevent overlap

        for round_number in range(num_rounds_per_day):
            logger.info(f"Starting scheduling for round {round_number + 1}")
            for account in accounts:
                # Calculate the scheduled time for this task
                # Randomize the task duration between min and max
                task_duration_minutes = random.randint(
                    min_task_duration, max_task_duration
                )
                task_duration = timedelta(minutes=task_duration_minutes)

                # Create a new UserTask
                user_task_in = UserTaskCreate(
                    title=f"Automation for account {account.email} - Round {round_number + 1}",
                    user_id=user_id,
                    account_id=account.id,
                    status=TaskStatus.PENDING,
                    scheduled_time=scheduled_time,
                )
                user_task = crud.create_task(session=session, task_in=user_task_in)

                # Schedule the task
                schedule_task_automation(user_task.id, eta=scheduled_time)

                logger.info(
                    f"Scheduled task for account {account.email} at {scheduled_time} UTC"
                )
                # Update scheduled_time for the next task
                # Add task duration plus a buffer to prevent overlap
                scheduled_time += task_duration + timedelta(minutes=buffer_minutes)
                # Optional: Add a break between rounds
            round_break_minutes = random.randint(
                1, 5
            )  # Random break between 1 to 5 minutes
            scheduled_time += timedelta(minutes=round_break_minutes)

        session.commit()

    # Schedule the next day's automation at midnight UTC
    next_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )

    celery_worker.send_task(
        "celery_worker.task.run_user_automation",
        args=[user_id],
        eta=next_day_start,
    )

    logger.info(
        f"Scheduled next day's automation for user_id: {user_id} at {next_day_start} UTC"
    )


def schedule_task_automation(task_id: str, eta: datetime) -> Task:
    return celery_worker.send_task(
        "celery_worker.task.process_task", args=[task_id], eta=eta
    )
