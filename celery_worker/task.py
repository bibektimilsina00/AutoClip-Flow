import random
import uuid
from datetime import datetime, timedelta
from typing import cast

import pytz
from celery import Task, states
from celery.exceptions import Ignore
from seleniumbase import SB, BaseCase
from sqlalchemy.exc import OperationalError
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
    try:
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

                # Load user to get optional per-user Google credentials file
                from app.models.user_model import User

                user = session.get(User, user_task.user_id)
                user_google_key = None
                if user and getattr(user, "google_service_account_file", None):
                    user_google_key = user.google_service_account_file

                app = MainApp(
                    user_task.user_id, user_google_credentials=user_google_key
                )
                # Support both legacy 'platforms' CSV and new single 'platform' enum field
                if hasattr(account, "platforms") and account.platforms:
                    platforms = account.platforms.split(",")
                else:
                    # account.platform may be an enum or a string
                    p = getattr(account, "platform", None)
                    if p is None:
                        platforms = []
                    elif isinstance(p, str):
                        platforms = [p]
                    else:
                        # Enum value
                        try:
                            platforms = [p.name.lower()]
                        except Exception:
                            platforms = [str(p).lower()]

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
                            account,
                        )

                        sb_utils.random_delay()

                        self.update_state(
                            state="COMPLETED",
                            meta={"status": "Automation completed", "progress": 100},
                        )
                        user_task.status = TaskStatus.COMPLETED
                        user_task.progress = 100

                    except Exception as e:
                        logger.error(
                            f"Error processing account {account.email}: {str(e)}"
                        )
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
    except OperationalError as oe:
        # Transient DB error: ask Celery to retry the task with backoff
        logger.warning(
            "OperationalError while trying to access DB for task %s: %s. Retrying...",
            task_id,
            oe,
        )
        raise self.retry(exc=oe, countdown=30)


@celery_worker.task(bind=True)
def run_user_automation(self, user_id: str | uuid.UUID):
    try:
        # Normalize user_id to uuid.UUID when possible (accept str or UUID)
        if isinstance(user_id, (str, uuid.UUID)):
            try:
                user_id_uuid = uuid.UUID(str(user_id))
            except Exception:
                logger.warning(
                    "Invalid user_id passed to run_user_automation: %s", user_id
                )
                return
        else:
            # If a non-str/UUID is passed, we can't proceed safely
            logger.warning(
                "Unsupported user_id type passed to run_user_automation: %r", user_id
            )
            return

        with next(get_db()) as session:
            # Get all accounts for the user
            statement = select(Account).where(Account.owner_id == user_id_uuid)
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
                    user_id=user_id_uuid,
                    account_id=account.id,
                    status=TaskStatus.PENDING,
                    scheduled_time=scheduled_time,
                )
                user_task = crud.create_task(session=session, task_in=user_task_in)

                # Schedule the task and record the Celery task id on the DB row
                celery_result = schedule_task_automation(
                    str(user_task.id), eta=scheduled_time
                )
                try:
                    # celery_result may be a AsyncResult-like or task id string depending on backend
                    celery_id = getattr(celery_result, "id", None) or str(celery_result)
                    user_task.task_id = celery_id
                    session.add(user_task)
                    session.commit()
                except Exception:
                    logger.exception(
                        "Failed to store celery task id for usertask %s",
                        str(user_task.id),
                    )

                logger.info(
                    f"Scheduled task for account {account.email} at {scheduled_time} UTC"
                )

        session.commit()

    except OperationalError as oe:
        logger.warning(
            "OperationalError while preparing run_user_automation for user %s: %s. Retrying...",
            user_id,
            oe,
        )
        raise self.retry(exc=oe, countdown=60)

    # Schedule the next day's automation
    next_day_start = start_time + timedelta(days=1)
    celery_worker.send_task(
        "celery_worker.task.run_user_automation",
        args=[str(user_id)],
        eta=next_day_start,
    )

    logger.info(
        f"Scheduled next day's automation for user_id: {user_id} at {next_day_start} UTC"
    )


@celery_worker.task
def schedule_next_day(user_id: int | str):
    # Schedule the next day's run via the broker to avoid calling the bound task directly
    celery_worker.send_task(
        "celery_worker.task.run_user_automation", args=[str(user_id)]
    )


def schedule_task_automation(task_id: str, eta: datetime) -> Task:
    return celery_worker.send_task(
        "celery_worker.task.process_task", args=[task_id], eta=eta
    )
