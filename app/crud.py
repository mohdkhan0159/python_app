from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models
from .auth import get_password_hash, verify_password

async def get_user_by_email(db: AsyncSession, email: str):
    q = await db.execute(select(models.User).where(models.User.email == email))
    return q.scalars().first()

async def create_user(db: AsyncSession, email: str, password: str):
    hashed = get_password_hash(password)
    user = models.User(email=email, hashed_password=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def list_courses(db: AsyncSession):
    q = await db.execute(select(models.Course).where(models.Course.is_published==True))
    return q.scalars().all()

async def get_course(db: AsyncSession, course_id: int):
    q = await db.execute(select(models.Course).where(models.Course.id==course_id))
    return q.scalars().first()
