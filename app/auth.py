# app/auth.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from .models import User
from .database import AsyncSessionLocal, get_db
import uuid
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# Password utilities
# -----------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -----------------------------
# Authenticate user (DB)
# -----------------------------
async def authenticate_user(email: str, password: str, db: AsyncSession):
    q = await db.execute(select(User).where(User.email == email))
    user = q.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# -----------------------------
# Login (writes user_id to server-side session)
# This function signature is used by routes/users.py:
#    return await login_user(request, email, password, db)
# -----------------------------
async def login_user(request: Request, email: str, password: str, db: AsyncSession):
    user = await authenticate_user(email, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Save user id into session (starlette session)
    request.session["user_id"] = user.id

    # optional: create additional session cookie/token if you want
    return RedirectResponse("/dashboard", status_code=303)
# async def login_user(request: Request, email: str, password: str, db: AsyncSession):

#     print("LOGIN USER START")

#     user = await authenticate_user(email, password, db)
#     if not user:
#         print("AUTH FAILED")
#         raise HTTPException(status_code=401, detail="Invalid email or password")

#     print("AUTH SUCCESS — user id:", user.id)

#     # save user ID in session
#     request.session["user_id"] = user.id

#     print("SESSION AFTER LOGIN:", dict(request.session))

#     return RedirectResponse("/dashboard", status_code=303)


# -----------------------------
# Logout
# -----------------------------
async def logout_user(request: Request):
    # clears entire session for this client
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# -----------------------------
# Get current user from session
# -----------------------------
async def get_current_user_from_session(request: Request) -> Optional[User]:
    # DO NOT CHECK "session" IN request.scope (FastAPI never puts it there)

    user_id = request.session.get("user_id")
    if not user_id:
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    return user



# -----------------------------
# Backwards-compatible helper
# -----------------------------
# Use this in middleware and routes: it delegates to the session helper above.
async def get_current_user(request: Request) -> Optional[User]:
    """
    Public helper that returns the logged-in user (or None).
    Kept separate so callers import `get_current_user` from here.
    """
    return await get_current_user_from_session(request)
