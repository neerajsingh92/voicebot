from __future__ import annotations

import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

_pool: asyncpg.Pool | None = None


async def connect():
    global _pool
    _pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        min_size=2,
        max_size=10,
    )


async def disconnect():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised — call connect() first")
    return _pool


async def fetch(query: str, *args):
    return await get_pool().fetch(query, *args)


async def fetchrow(query: str, *args):
    return await get_pool().fetchrow(query, *args)


async def fetchval(query: str, *args):
    return await get_pool().fetchval(query, *args)


async def execute(query: str, *args):
    return await get_pool().execute(query, *args)
