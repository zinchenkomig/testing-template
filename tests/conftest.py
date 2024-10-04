import pytest
import os

from httpx import AsyncClient
from sqlalchemy_utils import drop_database, database_exists, create_database

from src import dependencies
import src.db_models as db
from sqlalchemy import create_engine, update

from main import app
from utils.db_connection import get_connection_string
from utils.db_connection_sync import get_sync_connection_string
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import sqlalchemy as sql


# Is required for anyio to work properly
# https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on
@pytest.fixture(scope='class')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope='class')
async def async_client():
    db_address = 'localhost'
    db_user = os.getenv('TEST_DB_USER', 'testuser')
    db_password = os.getenv('TEST_DB_PASSWORD', '123')
    db_name = os.getenv('TEST_DB_NAME', 'test')
    async_engine = create_async_engine(get_connection_string(db_address, db_user, db_password, db_name))
    AsyncMainSession = async_sessionmaker(async_engine)

    async def _get_async_session():
        async_session = AsyncMainSession()
        try:
            yield async_session
        finally:
            await async_session.close()

    app.dependency_overrides[dependencies.get_async_session] = _get_async_session
    client = await AsyncClient(app=app, base_url='http://testenv').__aenter__()
    try:
        yield client
    finally:
        await client.__aexit__()


@pytest.fixture(scope='class')
async def async_session():
    db_address = 'localhost'
    db_user = os.getenv('TEST_DB_USER', 'testuser')
    db_password = os.getenv('TEST_DB_PASSWORD', '123')
    db_name = os.getenv('TEST_DB_NAME', 'test')
    async_engine = create_async_engine(get_connection_string(db_address, db_user, db_password, db_name))
    AsyncMainSession = async_sessionmaker(async_engine)
    session = AsyncMainSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope='class')
async def user_access(async_client, async_session):
    test_password = 'test_password'
    test_email = 'testemail@email.com'
    await async_client.post('/auth/register', json={'password': test_password,
                                                    'email': test_email,
                                                    'first_name': 'John',
                                                    })

    user_query = await async_session.execute(sql.select(db.User).filter_by(email=test_email).limit(1))
    user = user_query.scalars().one_or_none()
    assert user is not None

    verify_response = await async_client.post('/auth/verify', json={'user_guid': str(user.guid)})
    assert verify_response.status_code == 200

    login_response = await async_client.post('/auth/login/email',
                                             data={'username': test_email, 'password': test_password})
    access = login_response.json()
    return {'Authorization': 'Bearer ' + access['access_token']}


@pytest.fixture(scope='class')
async def superuser_access(async_client, async_session):
    test_password = 'test_password'
    test_email = 'superuser@email.com'
    await async_client.post('/auth/register', json={
        'password': test_password,
        'email': test_email,
        'first_name': 'John',
    })
    user_query = await async_session.execute(sql.select(db.User).filter_by(email=test_email).limit(1))
    user = user_query.scalars().one_or_none()
    assert user is not None

    verify_response = await async_client.post('/auth/verify', json={'user_guid': str(user.guid)})
    assert verify_response.status_code == 200

    login_response = await async_client.post('/auth/login/email', data={'username': test_email,
                                                                        'password': test_password})
    assert login_response.status_code == 200

    await async_session.execute(update(db.User).where(db.User.email == test_email).values(roles=['admin']))
    await async_session.commit()
    access = login_response.json()
    return {'Authorization': 'Bearer ' + access['access_token']}


@pytest.fixture(scope='class')
def mocked_connection() -> str:
    db_address = 'localhost'
    db_user = os.getenv('TEST_DB_USER', 'testuser')
    db_password = os.getenv('TEST_DB_PASSWORD', '123')
    db_name = os.getenv('TEST_DB_NAME', 'test')
    db_connection_string = get_sync_connection_string(db_address, db_user, db_password, db_name)
    return db_connection_string


@pytest.fixture(autouse=True, scope='class')
def clear_db_before_usage(mocked_connection):
    db_connection_string = mocked_connection
    if database_exists(db_connection_string):
        drop_database(db_connection_string)
    create_database(db_connection_string)
    test_engine = create_engine(db_connection_string)
    db.Base.metadata.create_all(test_engine)
