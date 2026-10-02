import pytest
from httpx import AsyncClient

from src.app.schemas.auth_schema import AuthResponse
from tests.utils import validate_response


async def test_register_success(client: AsyncClient, user_factory):
    await user_factory()


async def test_register_duplicate_user_conflict(client: AsyncClient, user_factory):
    user_data, response = await user_factory(user_name="conflict_user")
    conflict_response = await client.post(
        "/auth/register",
        json={
            "name": user_data.user.name,
            "user_name": user_data.user.user_name,
            "password": "somepassword",
        },
    )

    assert conflict_response.status_code == 409


async def test_register_duplicate_admin_conflict(client: AsyncClient, user_factory):
    payload = {
        "name": "Admin",
        "user_name": "admin",
        "password": "somepassword",
    }

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        ({}),
        ({"user_name": "validname", "password": "pass123"}),
        ({"name": "Test", "password": "pass123"}),
        ({"name": "Test", "user_name": "validname"}),
        ({"name": "", "user_name": "validname", "password": "pass123"}),
        ({"name": "a" * 33, "user_name": "validname", "password": "pass123"}),
        ({"name": "Test", "user_name": "ab", "password": "pass123"}),
        ({"name": "Test", "user_name": "a" * 17, "password": "pass123"}),
        ({"name": "Test", "user_name": "Invalid_Caps", "password": "pass123"}),
        ({"name": "Test", "user_name": "user@name!", "password": "pass123"}),
        ({"name": "Test", "user_name": "юзернейм", "password": "pass123"}),
        ({"name": "Test", "user_name": "validname", "password": "a" * 61}),
    ],
)
async def test_register_invalid_payload(client: AsyncClient, payload: dict):
    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        ({}),
        ({"password": "pass123"}),
        ({"user_name": "validname"}),
        ({"user_name": "ab", "password": "pass123"}),
        ({"user_name": "a" * 17, "password": "pass123"}),
        ({"user_name": "Invalid_Caps", "password": "pass123"}),
        ({"user_name": "validname", "password": "a" * 61}),
    ],
)
async def test_login_invalid_payload(client: AsyncClient, payload: dict):
    response = await client.post("/auth/login", json=payload)

    assert response.status_code == 422


async def test_login_success(client: AsyncClient, user_factory):
    user_pass = "somepass"
    user_data, response = await user_factory(password=user_pass)

    login_response = await client.post(
        "/auth/login",
        json={
            "name": user_data.user.name,
            "user_name": user_data.user.user_name,
            "password": user_pass,
        },
    )

    assert login_response.status_code == 200
    validate_response(login_response, AuthResponse)

    register_refresh_token = response.cookies.get("refresh_token")
    login_refresh_token = login_response.cookies.get("refresh_token")

    login_access_token = login_response.json()["access_token"]

    assert login_refresh_token != register_refresh_token
    assert login_refresh_token != None
    assert login_access_token != None


async def test_login_invalid_user_name(client: AsyncClient, user_factory):
    user_data, response = await user_factory(password="correct_password")

    login_response = await client.post(
        "/auth/login",
        json={
            "user_name": user_data.user.user_name,
            "password": "wrong_password",
        },
    )
    assert login_response.status_code == 401


async def test_login_invalid_password(client: AsyncClient, user_factory):
    user_pass = "correct_password"
    user_data, response = await user_factory(user_name="user_name", password=user_pass)

    login_response = await client.post(
        "/auth/login",
        json={
            "user_name": "non_exists_user",
            "password": user_pass,
        },
    )
    assert login_response.status_code == 401
