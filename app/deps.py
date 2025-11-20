# app/deps.py
# -------------------------------------------------------
# This file is intentionally minimal now.
# JWT has been removed; session-based auth handles login.
# -------------------------------------------------------

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db

# If you want shared dependencies later (pagination, caching, etc.),
# you can add them here.

async def get_db_session(db: AsyncSession = Depends(get_db)):
    return db
