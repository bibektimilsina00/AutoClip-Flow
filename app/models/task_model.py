import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.account_model import Account
    from models.user_model import User


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class UserTaskBase(SQLModel):
    title: str | None = None
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress: Optional[int] = Field(default=0)
    # Celery task id (the broker-assigned id for the background job). This is
    # distinct from the DB primary key `id` and is optional.
    task_id: Optional[str] = Field(default=None, index=True)
    scheduled_time: Optional[datetime] = Field(default=None)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    account_id: Optional[uuid.UUID] = Field(foreign_key="account.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Properties to receive via API when creating a new task
class UserTaskCreate(UserTaskBase):
    pass


# Properties to receive via API on update, all fields are optional
class UserTaskUpdate(SQLModel):
    status: TaskStatus | None = None
    progress: int | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Properties to return via API
class UserTaskPublic(UserTaskBase):
    id: uuid.UUID
    user_id: uuid.UUID


# Database model for storing tasks, with relationship to User model
class UserTask(UserTaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user: Optional["User"] = Relationship(back_populates="tasks")
    account: Optional["Account"] = Relationship(back_populates="tasks")
