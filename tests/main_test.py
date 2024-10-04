import pytest
import sqlalchemy as sql
from fastapi import status

import src.db_models as db


class TestRegisterAuthFlow:
    @pytest.mark.anyio
    async def test_auth(self, async_client, async_session):
        test_password = 'test_password'
        test_email = 'testemail@email.com'
        register_response = await async_client.post('/auth/register', json={'password': test_password,
                                                                            'email': test_email,
                                                                            'first_name': 'John',
                                                                            })
        assert register_response.status_code == 201

        user_query = await async_session.execute(sql.select(db.User).filter_by(email=test_email).limit(1))
        user = user_query.scalars().one_or_none()
        assert user is not None

        verify_response = await async_client.post('/auth/verify', json={'user_guid': str(user.guid)})
        assert verify_response.status_code == 200

        login_response = await async_client.post('/auth/login/email', data={'username': test_email,
                                                                            'password': test_password})
        assert login_response.status_code == 200


class TestSuperuserRights:
    @pytest.mark.anyio
    async def test_superuser_not_allowed(self, async_client, user_access):
        users_resp = await async_client.get('/superuser/users', headers=user_access)
        assert users_resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.anyio
    async def test_superuser_good(self, async_client, superuser_access):
        users_resp = await async_client.get('/superuser/users', headers=superuser_access)
        assert users_resp.status_code == status.HTTP_200_OK
        assert len(users_resp.json()) > 0
