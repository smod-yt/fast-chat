import asyncio
import bcrypt

async def hash_password(password: str) -> str:
    salt = await asyncio.to_thread(bcrypt.gensalt)
    hashed_password = await asyncio.to_thread(
        bcrypt.hashpw,
        password.encode("utf-8"),
        salt
    )

    return hashed_password.decode("utf-8")

async def check_password(password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(
        bcrypt.checkpw,
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )