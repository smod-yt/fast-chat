from sqlalchemy import func, select

from src.app.db import AsyncSessionLocal
from src.app.models import User
from src.app.models.chat_model import (
    SAVED_MESSAGES_TITLE,
    SYSTEM_NOTIFICATIONS_TITLE,
    Chat,
    ChatParticipant,
)
from src.app.schemas.chat_schema import ChatResponse, PaginatedChatsResponse
from tests.utils import auth_header, validate_response


def private_chats(data: PaginatedChatsResponse) -> list[ChatResponse]:
    return [chat for chat in data.items if chat.type == "private"]


def system_chats(data: PaginatedChatsResponse) -> list[ChatResponse]:
    return [chat for chat in data.items if chat.type == "system"]


async def create_private_chat(client, actor, other_user_id):
    return await client.post(
        "/chats",
        json={"user_ids": [actor.user.id, other_user_id], "type": "private"},
        headers=auth_header(actor.access_token),
    )


async def test_create_private_chat_success(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()

    response = await create_private_chat(client, user, other.user.id)
    assert response.status_code == 201

    chat = validate_response(response, ChatResponse)
    assert chat.type == "private"
    assert chat.owner_id == user.user.id
    assert chat.is_blocked is False
    assert chat.writable is True
    assert chat.title is None
    assert {player.user_id for player in chat.participants} == {
        user.user.id,
        other.user.id,
    }


async def test_create_duplicate_chat_fails(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()

    assert (await create_private_chat(client, user, other.user.id)).status_code == 201

    response = await create_private_chat(client, user, other.user.id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_cannot_create_system_chat(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()

    response = await client.post(
        "/chats",
        json={"user_ids": [user.user.id, other.user.id], "type": "system"},
        headers=auth_header(user.access_token),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_create_chat_without_self_fails(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()

    response = await client.post(
        "/chats",
        json={"user_ids": [other.user.id, 999999], "type": "private"},
        headers=auth_header(user.access_token),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


async def test_create_chat_with_missing_user_fails(client, user_factory):
    user, _ = await user_factory()

    response = await client.post(
        "/chats",
        json={"user_ids": [user.user.id, 999999], "type": "private"},
        headers=auth_header(user.access_token),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


async def test_create_chat_with_duplicate_user_ids_fails(client, user_factory):
    user, _ = await user_factory()

    response = await client.post(
        "/chats",
        json={"user_ids": [user.user.id, user.user.id], "type": "private"},
        headers=auth_header(user.access_token),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


async def test_get_own_chats(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()
    await create_private_chat(client, user, other.user.id)

    response = await client.get("/chats", headers=auth_header(user.access_token))
    assert response.status_code == 200

    data = validate_response(response, PaginatedChatsResponse)
    assert data.total == 3
    assert len(private_chats(data)) == 1
    assert len(system_chats(data)) == 2


async def test_system_chats_created_on_register(client, user_factory):
    user, _ = await user_factory()

    response = await client.get("/chats", headers=auth_header(user.access_token))
    data = validate_response(response, PaginatedChatsResponse)

    chats = system_chats(data)
    assert len(chats) == 2
    assert {chat.title for chat in chats} == {
        SAVED_MESSAGES_TITLE,
        SYSTEM_NOTIFICATIONS_TITLE,
    }
    for chat in chats:
        assert chat.writable is False
        assert chat.owner_id == user.user.id
        assert [p.user_id for p in chat.participants] == [user.user.id]


async def test_user_cannot_get_other_chats(client, user_factory):
    owner, _ = await user_factory()
    other, _ = await user_factory()

    response = await client.get(
        f"/chats/{owner.user.id}", headers=auth_header(other.access_token)
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_moderator_can_get_other_chats(client, user_factory, moderator_factory):
    owner, _ = await user_factory()
    moderator, _ = await moderator_factory()

    response = await client.get(
        f"/chats/{owner.user.id}", headers=auth_header(moderator.access_token)
    )
    assert response.status_code == 200
    data = validate_response(response, PaginatedChatsResponse)
    assert data.total == 2


async def test_user_can_get_own_chats_by_user_id(client, user_factory):
    user, _ = await user_factory()

    response = await client.get(
        f"/chats/{user.user.id}", headers=auth_header(user.access_token)
    )
    assert response.status_code == 200
    assert validate_response(response, PaginatedChatsResponse).total == 2


async def test_owner_can_update_chat(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()
    created = await create_private_chat(client, user, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.patch(
        f"/chats/{chat.uuid}",
        json={"is_blocked": True},
        headers=auth_header(user.access_token),
    )
    assert response.status_code == 200
    updated = validate_response(response, ChatResponse)
    assert updated.is_blocked is True


async def test_user_cannot_update_other_chat(client, user_factory):
    owner, _ = await user_factory()
    other, _ = await user_factory()
    created = await create_private_chat(client, owner, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.patch(
        f"/chats/{chat.uuid}",
        json={"is_blocked": True},
        headers=auth_header(other.access_token),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_moderator_can_update_other_chat(
    client, user_factory, moderator_factory
):
    owner, _ = await user_factory()
    other, _ = await user_factory()
    moderator, _ = await moderator_factory()
    created = await create_private_chat(client, owner, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.patch(
        f"/chats/{chat.uuid}",
        json={"is_blocked": True},
        headers=auth_header(moderator.access_token),
    )
    assert response.status_code == 200
    assert validate_response(response, ChatResponse).is_blocked is True


async def test_owner_can_delete_chat(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()
    created = await create_private_chat(client, user, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.delete(
        f"/chats/{chat.uuid}", headers=auth_header(user.access_token)
    )
    assert response.status_code == 204

    listed = await client.get("/chats", headers=auth_header(user.access_token))
    data = validate_response(listed, PaginatedChatsResponse)
    assert chat.uuid not in {item.uuid for item in data.items}

    async with AsyncSessionLocal() as session:
        participants = (
            await session.execute(
                select(func.count(ChatParticipant.user_id)).where(
                    ChatParticipant.chat_uuid == chat.uuid
                )
            )
        ).scalar_one()
    assert participants == 0


async def test_user_cannot_delete_other_chat(client, user_factory):
    owner, _ = await user_factory()
    other, _ = await user_factory()
    created = await create_private_chat(client, owner, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.delete(
        f"/chats/{chat.uuid}", headers=auth_header(other.access_token)
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_moderator_cannot_delete_other_chat(
    client, user_factory, moderator_factory
):
    owner, _ = await user_factory()
    other, _ = await user_factory()
    moderator, _ = await moderator_factory()
    created = await create_private_chat(client, owner, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.delete(
        f"/chats/{chat.uuid}", headers=auth_header(moderator.access_token)
    )
    assert response.status_code == 403


async def test_admin_can_delete_other_chat(client, user_factory, admin_factory):
    owner, _ = await user_factory()
    other, _ = await user_factory()
    admin, _ = await admin_factory()
    created = await create_private_chat(client, owner, other.user.id)
    chat = validate_response(created, ChatResponse)

    response = await client.delete(
        f"/chats/{chat.uuid}", headers=auth_header(admin.access_token)
    )
    assert response.status_code == 204


async def test_system_chat_cannot_be_modified_or_deleted(client, user_factory):
    user, _ = await user_factory()

    listed = await client.get("/chats", headers=auth_header(user.access_token))
    data = validate_response(listed, PaginatedChatsResponse)
    chat = system_chats(data)[0]

    patch_response = await client.patch(
        f"/chats/{chat.uuid}",
        json={"is_blocked": True},
        headers=auth_header(user.access_token),
    )
    assert patch_response.status_code == 403

    delete_response = await client.delete(
        f"/chats/{chat.uuid}", headers=auth_header(user.access_token)
    )
    assert delete_response.status_code == 403


async def test_admin_cannot_delete_system_chat(client, admin_factory):
    admin, _ = await admin_factory()

    listed = await client.get("/chats", headers=auth_header(admin.access_token))
    data = validate_response(listed, PaginatedChatsResponse)
    chat = system_chats(data)[0]

    response = await client.delete(
        f"/chats/{chat.uuid}", headers=auth_header(admin.access_token)
    )
    assert response.status_code == 403


async def test_chats_require_auth(client):
    chat_uuid = "00000000-0000-0000-0000-000000000000"

    assert (await client.get("/chats")).status_code == 401
    assert (await client.get("/chats/1")).status_code == 401
    assert (await client.post("/chats", json={})).status_code == 401
    assert (
        await client.patch(f"/chats/{chat_uuid}", json={"is_blocked": True})
    ).status_code == 401
    assert (await client.delete(f"/chats/{chat_uuid}")).status_code == 401


async def test_deleting_user_sets_chat_owner_null(client, user_factory):
    user, _ = await user_factory()
    other, _ = await user_factory()
    created = await create_private_chat(client, user, other.user.id)
    chat = validate_response(created, ChatResponse)

    async with AsyncSessionLocal() as session:
        db_user = await session.get(User, user.user.id)
        await session.delete(db_user)
        await session.commit()

    async with AsyncSessionLocal() as session:
        db_chat = await session.get(Chat, chat.uuid)
        assert db_chat.owner_id is None
        participants = (
            await session.execute(
                select(ChatParticipant.user_id).where(
                    ChatParticipant.chat_uuid == chat.uuid
                )
            )
        ).scalars().all()
    assert list(participants) == [other.user.id]
