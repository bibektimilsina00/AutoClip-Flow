import uuid
from typing import TYPE_CHECKING, List, Optional

from pydantic import EmailStr

from app.models.user_model import Field, Relationship, SQLModel

# single-enum Platform removed; we store multiple platforms as CSV in `platforms`

if TYPE_CHECKING:
    from models.task_model import UserTask
    from models.user_model import User


# Base properties shared across models
class AccountBase(SQLModel):
    category: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(index=True, unique=True, max_length=255)
    google_drive_folder_id: str = Field(max_length=255)
    # Store multiple selected platforms as CSV (e.g. "tiktok,instagram,facebook")
    platforms: Optional[str] = Field(default=None, max_length=255)
    # Facebook-specific optional settings
    facebook_page_id: Optional[str] = Field(default=None, max_length=255)
    facebook_group_id: Optional[str] = Field(default=None, max_length=255)
    facebook_post_to_page: Optional[bool] = Field(default=False)
    facebook_post_to_group: Optional[bool] = Field(default=False)


# Properties to receive on account creation
class AccountCreate(AccountBase):
    password: str = Field(min_length=8, max_length=40)


# Properties to receive on account update (all fields optional)
class AccountUpdate(SQLModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=255)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    google_drive_folder_id: Optional[str] = Field(default=None, max_length=255)
    platforms: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=8, max_length=40)


# Database model, table inferred from class name
class Account(AccountBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password: str = Field(max_length=40)  # Stored securely (hashed ideally)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: Optional["User"] = Relationship(back_populates="accounts")
    tasks: List["UserTask"] = Relationship(back_populates="account")


# Properties to return via API
class AccountPublic(AccountBase):
    id: uuid.UUID
    owner_id: uuid.UUID


# For list responses
class AccountsPublic(SQLModel):
    data: List[AccountPublic]
    count: int
