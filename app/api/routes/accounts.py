import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.account_model import (
    Account,
    AccountCreate,
    AccountPublic,
    AccountsPublic,
    AccountUpdate,
)
from app.models.user_model import Message
from automation.enums.platform import Platform

router = APIRouter()


@router.get("/platforms")
def get_platforms() -> Any:
    """
    Get available platform choices.
    """
    platforms = [
        {"value": platform.name.lower(), "label": platform.name.title()}
        for platform in Platform
    ]
    return {"platforms": platforms}


@router.get("/", response_model=AccountsPublic)
def read_accounts(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve accounts.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Account)
        count = session.exec(count_statement).one()
        statement = select(Account).offset(skip).limit(limit)
        accounts = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Account)
            .where(Account.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Account)
            .where(Account.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        accounts = session.exec(statement).all()

    return AccountsPublic(data=accounts, count=count)


@router.get("/{id}", response_model=AccountPublic)
def read_account(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get account by ID.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not current_user.is_superuser and (account.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return account


@router.post("/", response_model=AccountPublic)
def create_account(
    *, session: SessionDep, current_user: CurrentUser, account_in: AccountCreate
) -> Any:
    """
    Create new account.
    """
    account = Account.model_validate(account_in, update={"owner_id": current_user.id})
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.put("/{id}", response_model=AccountPublic)
def update_account(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    account_in: AccountUpdate,
) -> Any:
    """
    Update an account.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not current_user.is_superuser and (account.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = account_in.model_dump(exclude_unset=True)
    account.sqlmodel_update(update_dict)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{id}")
def delete_account(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an account.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not current_user.is_superuser and (account.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(account)
    session.commit()
    return Message(message="Account deleted successfully")
