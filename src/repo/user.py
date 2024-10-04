from typing import List
from typing import Optional

import fastapi
from fastapi import HTTPException
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

import src.db_models as models
from src.utils import make_search_query


async def get_user(async_session: AsyncSession, tg_id=None, user_guid=None, email=None) -> Optional[
    models.User]:
    if tg_id is None and user_guid is None and email is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="no identity specified")

    if tg_id is not None:
        query = select(models.User).filter_by(tg_id=tg_id).limit(1)
    if user_guid is not None:
        query = select(models.User).filter_by(guid=user_guid).limit(1)
    if email is not None:
        query = select(models.User).filter_by(email=email).limit(1)

    user_query_exec = await async_session.execute(query)
    user = user_query_exec.scalars().one_or_none()
    return user


async def check_is_user_exists(async_session, user_create):
    user_query_exec = await async_session.execute(select(models.User)
                                                  .filter((models.User.email == user_create.email)).limit(1))
    user = user_query_exec.scalars().first()
    return user is not None


async def new_user(async_session, user):
    async_session.add(user)
    return user


async def verify_user(async_session, user_guid):
    user_query_exec = await async_session.execute(select(models.User).filter_by(guid=user_guid).limit(1))
    user = user_query_exec.scalars().one_or_none()
    if user is None:
        raise HTTPException(status_code=404)
    user.is_verified = True


async def get_users(async_session: AsyncSession, search: Optional[str], page: int, limit: int) -> List[models.User]:
    query = select(models.User).order_by(models.User.created_at.desc())
    if search is not None and search != '':
        query = query.filter(
            func.to_tsvector(func.coalesce(models.User.first_name, '') + ' '
                             + func.coalesce(models.User.last_name, '') + ' '
                             + func.coalesce(models.User.email, '')
                             )
            .op('@@')(
                func.to_tsquery(make_search_query(search)))
        )
    if page is not None and limit is not None:
        query = query.limit(limit).offset((page - 1) * limit)
    users_resp = await async_session.execute(query)
    users = list(users_resp.scalars().all())
    return users


async def delete_user(async_session: AsyncSession, delete_user_id: str):
    await async_session.execute(delete(models.User).where(models.User.guid == delete_user_id))


async def update_user(async_session: AsyncSession, update_user_id: str, new_user_params):
    await async_session.execute(update(models.User).where(models.User.guid == update_user_id)
                                .values(**new_user_params.dict()))


async def set_user_recovery_token(async_session: AsyncSession, email: str):
    await async_session.execute()
