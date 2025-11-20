from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..auth import get_password_hash, login_user

router = APIRouter(prefix="/users", tags=["users"])


# -------------------------
# REGISTER
# -------------------------
@router.post("/register")
async def register_user(email: str, password: str, db: AsyncSession = Depends(get_db)):

    q = await db.execute(select(User).where(User.email == email))
    existing = q.scalar_one_or_none()

    if existing:
        return {"error": "Email already exists"}

    user = User(
    email=email,
    hashed_password=get_password_hash(password)
   )


    db.add(user)
    await db.commit()

    return {"message": "User registered successfully"}


# -------------------------
# LOGIN (HTML FORM)
# -------------------------
@router.post("/login")
async def login_user_route(request: Request, db: AsyncSession = Depends(get_db)):

    form = await request.form()
    email = form.get("username")      # from login.html
    password = form.get("password")

    return await login_user(request, email, password, db)


# -------------------------
# LOGOUT
# -------------------------
@router.get("/logout")
async def logout_route(request: Request):
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("session_token")
    return response
