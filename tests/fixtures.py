import pytest_asyncio
from faker import Faker
from httpx import AsyncClient

faker = Faker()


@pytest_asyncio.fixture
async def access_token(client: AsyncClient):
    name = faker.name()
    user_name = faker.user_name()

    response = await client.post(
        "/auth/register",
        json={"name": name, "user_name": user_name, "password": "password"},
    )
    content = response.json()

    assert response.status_code == 201

    return content["access_token"]


@pytest_asyncio.fixture
async def refresh_token(client: AsyncClient):
    name = faker.name()
    user_name = faker.user_name()

    response = await client.post(
        "/auth/register",
        json={"name": name, "user_name": user_name, "password": "password"},
    )
    content = response.json()

    assert response.status_code == 201

    return response.cookies.get("refresh_token")
