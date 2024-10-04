from typing import Annotated

import fastapi
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie, OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError

import src.db_models as db
from conf import settings
from conf.secrets import PASSWORD_ENCODING_SECRET
from .dependencies import AsyncSessionDep
from src.repo import user as user_repo
from src.roles import Role

apikey_cookie_getter = APIKeyCookie(name='login_token', auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login/email', auto_error=False)


async def get_user_from_refresh_token(async_session: AsyncSessionDep, token=Depends(apikey_cookie_getter),
                                      fake_email: Annotated[str | None, fastapi.Header()] = None,
                                      fake_roles: Annotated[str | None, fastapi.Header()] = None
                                      ) -> db.User:
    if not settings.IS_PROD and fake_email is not None and fake_roles is not None:
        user = await user_repo.get_user(async_session, email=fake_email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {fake_email} not found")
        user.roles = fake_roles.split(',')
        return user
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized. Please log in.")
    try:
        payload = jwt.decode(token, PASSWORD_ENCODING_SECRET, algorithms=[settings.ALGORITHM])
        user_guid = payload.get("sub")
        if user_guid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not get user from jwt",
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token signature expired. You need to login again.",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"jwt error: {e}",
        )
    user = await user_repo.get_user(async_session, user_guid=user_guid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not get user from user_repo",
        )
    return user


async def get_current_user(async_session: AsyncSessionDep, token: Annotated[str, Depends(oauth2_scheme)]
                           ) -> db.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, PASSWORD_ENCODING_SECRET, algorithms=[settings.ALGORITHM])
        user_guid: str = payload.get("sub")
        if user_guid is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Token expired",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"jwt error: {e}",
        )
    user = await user_repo.get_user(async_session, user_guid=user_guid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not get user from user_repo",
        )
    return user


CurrentUserDep = Annotated[db.User, Depends(get_current_user)]


async def get_current_superuser(current_user: db.User = Depends(get_current_user)):
    if Role.Admin.value not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    else:
        return current_user
