import hashlib
import hmac
from copy import copy
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Annotated
from typing import Union

from fastapi import APIRouter, Response, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext

from conf import settings
from conf.secrets import PASSWORD_ENCODING_SECRET
from conf.secrets import tg_secret_token
from src.db_models import User
from src.dependencies import AsyncSessionDep, EmailSenderDep
from src.json_schemes import UserCreate, UserRead, UserGUID, Token
from src.repo import user as user_repo
from src.roles import Role
from .email_template import registration_template
from ..auth import get_user_from_refresh_token

auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_jwt_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, PASSWORD_ENCODING_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_data_string(data: dict):
    sorted_data = sorted(data.items(), key=lambda x: x[0])
    sorted_data_str = '\n'.join([f'{key}={val}' for key, val in sorted_data])
    return sorted_data_str


def is_tg_hash_valid(data: dict, tg_bot_token: str):
    d = copy(data)
    data_hash = d.pop('hash')
    data_str = get_data_string(d)
    secret_hashed = hashlib.sha256(tg_bot_token.encode())
    one = hmac.new(key=secret_hashed.digest(), msg=data_str.encode(), digestmod='sha256')
    return hmac.compare_digest(one.hexdigest(), data_hash)


async def authenticate_user(async_session, email: str, password: str) -> Union[User, bool]:
    user = await user_repo.get_user(async_session, email=email)
    if user is None:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def get_jwt_tokens(user: User, response: Response) -> Token:
    refresh_token = create_jwt_token(data={
        "sub": str(user.guid)},
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    response.set_cookie(key='login_token', value=refresh_token,
                        samesite=settings.SAME_SITE,
                        secure=settings.IS_SECURE_COOKIE,
                        httponly=True,
                        )
    access_token = create_jwt_token(data={
        "sub": str(user.guid),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "roles": user.roles,
        "photo_url": user.photo_url,
    }, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    return Token(access_token=access_token, token_type="Bearer")


@auth_router.post("/login/email", response_model=Token)
async def login_with_email(response: Response,
                           async_session: AsyncSessionDep,
                           form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = await authenticate_user(async_session, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must first verify user email to login"
        )
    return get_jwt_tokens(user, response)


@auth_router.post("/access_token", response_model=Token)
async def get_access_token(response: Response, user: Annotated[User, Depends(get_user_from_refresh_token)]) -> Token:
    return get_jwt_tokens(user, response)


@auth_router.post("/login/tg", response_model=Token)
async def auth_tg(response: Response, async_session: AsyncSessionDep, request: Dict[Any, Any]):
    if not is_tg_hash_valid(request, tg_secret_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed tg token verification",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = request.get('username')
    if request.get('id') is not None:
        tg_id = str(request.get('id'))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='telegram id not specified')
    photo_url = request.get('photo_url')
    first_name = request.get('first_name')
    last_name = request.get('last_name')
    user = await user_repo.get_user(async_session, tg_id=tg_id)
    if user is None:
        user = User(first_name=first_name,
                    last_name=last_name,
                    email=None,
                    password=None,
                    tg_id=tg_id,
                    tg_username=username,
                    is_active=True,
                    photo_url=photo_url,
                    roles=[Role.Reader.value],
                    is_verified=True
                    )
        user = await user_repo.new_user(async_session, user)
        await async_session.commit()
        await async_session.refresh(user)
    return get_jwt_tokens(user, response)


@auth_router.post('/logout')
async def logout(response: Response):
    """
    Removes JWT token from http_only cookie
    :param response:
    :return:
    """
    response.set_cookie('login_token', value='', httponly=True,
                        samesite=settings.SAME_SITE, secure=settings.IS_SECURE_COOKIE)


@auth_router.post('/register')
async def register(user_create: UserCreate, response: Response,
                   async_session: AsyncSessionDep, sender: EmailSenderDep):
    """
    Registers a user
    :param sender:
    :param response:
    :param user_create:
    :param async_session:
    :return:
    """
    if await user_repo.check_is_user_exists(async_session, user_create):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    hashed_pass = get_password_hash(user_create.password)
    user = User(email=user_create.email,
                first_name=user_create.first_name,
                password=hashed_pass,
                is_verified=False,
                is_active=True,
                roles=[Role.Reader.value])
    await user_repo.new_user(async_session, user)
    await async_session.commit()
    await async_session.refresh(user)
    response.status_code = status.HTTP_201_CREATED
    verification_link = f'{settings.FRONTEND_URL}/verify/{user.guid}'
    message = registration_template.replace('{{verification_link}}', verification_link)
    sender.send_with_retries(to=user_create.email,
                             subject="Account Created",
                             message_text=message)


@auth_router.post('/verify')
async def verify_user(async_session: AsyncSessionDep, user: UserGUID):
    await user_repo.verify_user(async_session, user.user_guid)
    await async_session.commit()


@auth_router.get('/check/email')
async def check_username(email: str, async_session: AsyncSessionDep):
    user = await user_repo.get_user(async_session, email=email)
    return user is not None
