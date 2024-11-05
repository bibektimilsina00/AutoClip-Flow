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

            with SB(uc=True, xvfb=True) as sb:

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

        # Set the start time to now
        start_time = now

        # Number of runs per day
        num_runs_per_day = random.randint(10, 15)

        # Time interval between tasks (5-6 minutes)
        task_interval = timedelta(minutes=random.randint(5, 6))

        for run in range(num_runs_per_day):
            for account in accounts:
                # Calculate the scheduled time for this task
                scheduled_time = (
                    start_time
                    + (run * len(accounts) + accounts.index(account)) * task_interval
                )

                # Create a new UserTask
                user_task_in = UserTaskCreate(
                    title=f"Automation for account {account.email}",
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

        session.commit()

    # Schedule the next day's automation
    next_day_start = start_time + timedelta(days=1)
    celery_worker.send_task(
        "celery_worker.task.run_user_automation", args=[user_id], eta=next_day_start
    )

    logger.info(
        f"Scheduled next day's automation for user_id: {user_id} at {next_day_start} UTC"
    )


@celery_worker.task
def schedule_next_day(user_id: int):
    run_user_automation(user_id)


def schedule_task_automation(task_id: str, eta: datetime) -> Task:
    return celery_worker.send_task(
        "celery_worker.task.process_task", args=[task_id], eta=eta
    )
