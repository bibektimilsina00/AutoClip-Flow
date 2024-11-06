import random
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models.account_model import Account
from app.models.task_model import TaskStatus, UserTask, UserTaskCreate, UserTaskUpdate
from automation.utils.logging_utils import fast_api_logger as logger
from celery_worker.celery_worker import celery_worker
from celery_worker.task import run_user_automation

# Create a router for automation
router = APIRouter()


class AutomationStatus(BaseModel):
    account_id: str
    task_id: str
    status: str
    result: dict = None


@router.get("/automation_status/", response_model=List[AutomationStatus])
async def get_automation_status(current_user: CurrentUser, session: SessionDep):

    # Query tasks from the database for the current user
    statement = select(UserTask).where(UserTask.user_id == current_user.id)
    user_tasks = session.exec(statement).all()

    automation_statuses = []
    for task in user_tasks:
        result = celery_worker.AsyncResult(str(task.id))
        automation_statuses.append(
            AutomationStatus(
                account_id=task.account_id,
                task_id=task.id,
                status=result.status,
                result=result.result if result.successful() else None,
            )
        )

    return automation_statuses


@router.post("/stop_automation")
async def stop_automation(
    session: SessionDep,
    current_user: CurrentUser,
):
    # Cancel all scheduled tasks for the user
    celery_worker.control.revoke(current_user.id, terminate=True)

    # Update all processing tasks to stopped
    statement = (
        select(UserTask)
        .where(UserTask.status == TaskStatus.PROCESSING)
        .where(UserTask.user_id == current_user.id)
    )
    processing_tasks = session.exec(statement).all()
    for task in processing_tasks:
        task.status = TaskStatus.STOPPED
        session.add(task)

    session.commit()
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

    # Set up a recurring schedule
    schedule_automation(current_user.id)

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


def schedule_automation(user_id: int):
    run_user_automation.delay(user_id)
