import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models.user_model import User, UserCreate, UserUpdate
from app.models.account_model import Account, AccountCreate
from app.models.task_model import UserTask, UserTaskCreate, UserTaskUpdate, TaskStatus


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_account(
    *, session: Session, account_in: AccountCreate, owner_id: uuid.UUID
) -> Account:
    db_account = Account.model_validate(account_in, update={"owner_id": owner_id})
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    return db_account


def get_task_by_id(*, session: Session, task_id: uuid.UUID) -> UserTask | None:
    statement = select(UserTask).where(UserTask.id == task_id)
    session_task = session.exec(statement).first()
    return session_task


def create_task(
    *,
    session: Session,
    task_in: UserTaskCreate,
) -> UserTask:
    db_task = UserTask.model_validate(task_in)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


def update_task(
    *,
    session: Session,
    db_task: UserTask,
    task_in: UserTaskUpdate,
):
    task_data = task_in.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(task_data)
    session.add(db_task)
    session.commit()
