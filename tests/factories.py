import pytest_asyncio
from faker import Faker
from httpx import AsyncClient

faker = Faker()


@pytest_asyncio.fixture
async def user_factory(client: AsyncClient):
    async def factory(
        name: str | None = None,
        user_name: str | None = None,
        password: str | None = "password",
        expected_status_code: int | None = 201,
    ) -> dict:
        name = name or faker.name()
        user_name = user_name or faker.user_name()

        response = await client.post(
            "/api/v1/auth/register",
            json={"name": name, "user_name": user_name, "password": password},
        )
        content = response.json()

        assert response.status_code == expected_status_code

        return {**content, "refresh_token": response.cookies.get("refresh_token")}

    return factory
