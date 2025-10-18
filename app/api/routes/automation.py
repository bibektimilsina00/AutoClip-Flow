import os
import random
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models.account_model import Account
from app.models.task_model import TaskStatus, UserTask, UserTaskCreate, UserTaskUpdate
from automation.config.config import Config
from automation.utils.logging_utils import fast_api_logger as logger
from celery_worker.celery_worker import celery_worker
from celery_worker.task import schedule_task_automation

# Create a router for automation
router = APIRouter()


class AutomationStatus(BaseModel):
    account_id: str
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


@router.get("/automation_status/", response_model=List[AutomationStatus])
async def get_automation_status(current_user: CurrentUser, session: SessionDep):

    # Query tasks from the database for the current user
    statement = select(UserTask).where(UserTask.user_id == current_user.id)
    user_tasks = session.exec(statement).all()

    automation_statuses = []
    for task in user_tasks:
        # Prefer DB-stored status so the dashboard continues to show records even
        # after we revoke tasks. Only query Celery for live runtime info when
        # we have an associated Celery task id stored.
        err_msg = None
        runtime_status = None
        runtime_result = None
        if getattr(task, "task_id", None):
            try:
                result = celery_worker.AsyncResult(str(task.task_id))
                info = result.info
                if info and isinstance(info, dict):
                    err_msg = (
                        info.get("exc_message") or info.get("exc_type") or str(info)
                    )
                elif info:
                    err_msg = str(info)

                runtime_status = result.status
                runtime_result = result.result if result.successful() else None
            except Exception:
                # If querying Celery fails, fall back to the DB status
                logger.exception("Failed to query celery for task %s", str(task.id))

        automation_statuses.append(
            AutomationStatus(
                account_id=str(task.account_id),
                task_id=str(task.id),
                status=(runtime_status or task.status.value),
                result=runtime_result,
                error=err_msg,
            )
        )

    return automation_statuses


@router.post("/stop_automation")
async def stop_automation(
    session: SessionDep,
    current_user: CurrentUser,
):
    # Cancel all scheduled Celery tasks belonging to the user by revoking each task id
    # We avoid revoking by user id (which the broker may interpret differently) and
    # instead revoke per-scheduled `task_id` stored on the UserTask rows.
    statement = (
        select(UserTask)
        .where(UserTask.status == TaskStatus.PROCESSING)
        .where(UserTask.user_id == current_user.id)
    )
    processing_tasks = session.exec(statement).all()
    for task in processing_tasks:
        # Revoke the individual Celery task by its task id (task.task_id may be None)
        try:
            if getattr(task, "task_id", None):
                celery_worker.control.revoke(str(task.task_id), terminate=True)
        except Exception:
            # Log and continue; revocation failure shouldn't block updating DB state
            logger.exception(
                "Failed to revoke celery task for usertask %s", str(task.id)
            )

        # Mark the task as stopped so the dashboard still shows its record
        task.status = TaskStatus.STOPPED
        session.add(task)
    try:
        session.commit()
    except Exception as e:
        # Rollback and return a clear error so the API doesn't surface a stack trace
        session.rollback()
        logger.exception("Failed to update task statuses when stopping automation")
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update task statuses when stopping automation. "
                "Check the database enum `taskstatus` includes configured values or inspect server logs."
            ),
        )
    return {"message": "Automation stopped for all accounts."}


@router.post("/start_automation")
async def start_automation(
    session: SessionDep,
    current_user: CurrentUser,
):
    # Check if there are any active tasks already running for the user
    statement = (
        select(UserTask)
        .where(UserTask.status == TaskStatus.PROCESSING)
        .where(UserTask.user_id == current_user.id)
    )
    user_tasks = session.exec(statement).all()
    if user_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"Automation already running for {current_user.full_name}.",
        )

    logger.info(f"Starting automation for user {current_user.full_name}")
    # Retrieve all accounts for the user
    statement = select(Account).where(Account.owner_id == current_user.id)
    accounts = session.exec(statement).all()

    if not accounts:
        raise HTTPException(
            status_code=400,
            detail=f"No accounts found for {current_user.full_name}.\nPlease add accounts to your profile.",
        )

    # Pre-start validation: ensure critical runtime dependencies are available
    try:
        cfg = Config()
        creds_path = cfg.GOOGLE_APPLICATION_CREDENTIALS
        # Allow a per-user uploaded Google key to be used if the global creds file
        # is not configured. Many users upload their own service account JSON and
        # we store the path on the User model (google_service_account_file). The
        # worker tasks will use the per-user key when available.
        use_creds_path = None
        if creds_path and os.path.exists(creds_path):
            use_creds_path = creds_path
        else:
            # Fallback to per-user uploaded key if present. Resolve a few
            # plausible locations so relative paths work when the app is run
            # from a different working directory.
            user_key = getattr(current_user, "google_service_account_file", None)
            resolved_user_key = None
            if user_key:
                # 1) exact path
                if os.path.exists(user_key):
                    resolved_user_key = user_key
                else:
                    # 2) CWD-relative
                    cwd_candidate = os.path.join(os.getcwd(), user_key)
                    if os.path.exists(cwd_candidate):
                        resolved_user_key = cwd_candidate
                    else:
                        # 3) project-root relative (assume repo root is two levels up from this file)
                        project_root = os.path.abspath(
                            os.path.join(os.path.dirname(__file__), "..", "..")
                        )
                        project_candidate = os.path.join(project_root, user_key)
                        if os.path.exists(project_candidate):
                            resolved_user_key = project_candidate

            if resolved_user_key:
                use_creds_path = resolved_user_key
                logger.info(
                    "Using per-user Google credentials for automation: %s",
                    resolved_user_key,
                )
            else:
                logger.error(
                    f"Google credentials file missing or not set: {creds_path}"
                )
                # If the user has an uploaded key path recorded but the file is missing,
                # give a more actionable error message so they can re-upload.
                if user_key:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            f"A Google key path is configured for your account ('{user_key}') but the file was not found. "
                            "Please re-upload the Google service account JSON on your profile page or contact support."
                        ),
                    )
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"Missing Google service account file. Either set GOOGLE_APPLICATION_CREDENTIALS '{creds_path}' "
                        "or upload a per-user Google service account file in your profile. Automation will not start."
                    ),
                )

        # Quick Celery worker availability check
        try:
            ping = celery_worker.control.ping(timeout=2)
            if not ping:
                logger.error("No Celery workers responded to ping")
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "No Celery workers are available. Ensure worker processes are running and connected to the broker. "
                        "Automation will not start."
                    ),
                )
        except Exception as e:
            logger.error(f"Error pinging Celery workers: {e}")
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Failed to contact Celery workers: {str(e)}. "
                    "Ensure Redis/broker and workers are reachable. Automation will not start."
                ),
            )

    except HTTPException:
        # propagate
        raise
    except Exception as e:
        logger.exception("Unexpected error during pre-start checks")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    # Set up a recurring schedule
    try:
        schedule_automation(current_user.id)
    except Exception as e:
        logger.exception("Failed to schedule automation tasks")
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to schedule automation tasks: {str(e)}. "
                "Check broker connectivity and worker logs."
            ),
        )

    session.commit()
    return {
        "message": "Automation started for all accounts.",
        "user_id": current_user.id,
    }


@router.delete("/delete_all_user_tasks")
async def delete_all_user_tasks(
    session: SessionDep,
    current_user: CurrentUser,
):
    # Delete all tasks for the user
    statement = select(UserTask).where(UserTask.user_id == current_user.id)
    user_tasks = session.exec(statement).all()
    for task in user_tasks:
        session.delete(task)

    session.commit()
    return {"message": "All tasks deleted for the user."}


def schedule_automation(user_id: uuid.UUID | str):
    # Schedule the automation to run 10-15 times per day at random times
    num_runs = random.randint(10, 15)

    # Get the current date
    today = datetime.now().date()

    # Schedule tasks for today
    for _ in range(num_runs):
        # Generate a random time between 00:00 and 23:59
        random_time = timedelta(minutes=random.randint(0, 1439))
        schedule_time = datetime.combine(today, datetime.min.time()) + random_time

        celery_worker.send_task(
            "celery_worker.task.run_user_automation",
            args=[str(user_id)],
            eta=schedule_time,
        )

    # Schedule the next day's automation
    next_day = today + timedelta(days=1)
    next_day_midnight = datetime.combine(next_day, datetime.min.time())
    celery_worker.send_task(
        "celery_worker.task.schedule_next_day",
        args=[str(user_id)],
        eta=next_day_midnight,
    )
