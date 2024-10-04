import datetime
from typing import Optional

from pydantic import BaseModel
import uuid


class BaseORM(BaseModel):

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    first_name: str
    email: str
    password: str


class UserGUID(BaseModel):
    user_guid: uuid.UUID


class UserRead(BaseORM):
    guid: uuid.UUID
    email: Optional[str]
    roles: list[str]
    photo_url: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_verified: bool


class SuperuserUserUpdate(BaseModel):
    roles: list[str]


class UserUpdate(BaseModel):
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class Email(BaseModel):
    email: str


class RecoverPassword(BaseModel):
    new_password: str
    token: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class GetUsersRequest(BaseModel):
    search: Optional[str]


class Tweet(BaseORM):
    guid: uuid.UUID
    message: str
    created_by: UserRead
    created_at: datetime.datetime


class CreateTweet(BaseModel):
    message: str
