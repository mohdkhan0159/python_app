from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..auth import get_password_hash, login_user

router = APIRouter(prefix="/users", tags=["users"])


# -------------------------
# REGISTER PAGE (GET)
# -------------------------
@router.get("/register")
async def register_page(request: Request):
    """Serve the registration form"""
    return request.app.state.templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


# -------------------------
# REGISTER (POST)
# -------------------------
@router.post("/register")
async def register_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle registration form submission"""
    
    # Get form data
    form = await request.form()
    first_name = form.get("first_name")
    last_name = form.get("last_name")
    email = form.get("email")
    password = form.get("password")
    confirm_password = form.get("confirm_password")
    
    # Validation
    if not email or not password or not first_name or not last_name:
        return request.app.state.templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "All fields are required"}
        )
    
    if password != confirm_password:
        return request.app.state.templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Passwords do not match"}
        )
    
    if len(password) < 6:
        return request.app.state.templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Password must be at least 6 characters"}
        )
    
    # Check if user exists
    q = await db.execute(select(User).where(User.email == email))
    existing = q.scalar_one_or_none()

    if existing:
        return request.app.state.templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered"}
        )

    # Create new user
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=get_password_hash(password)
    )

    db.add(user)
    await db.commit()

    # Redirect to login with success message
    return RedirectResponse("/login?registered=true", status_code=303)


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
# PROFILE EDIT (GET)
# -------------------------
@router.get("/profile/edit")
async def profile_edit_page(request: Request):
    """Serve the profile edit form"""
    from ..auth import get_current_user
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse("/login?next=/profile/edit", status_code=303)
    
    return request.app.state.templates.TemplateResponse(
        "profile_edit.html",
        {"request": request, "user": user}
    )


# -------------------------
# PROFILE EDIT (POST)
# -------------------------
@router.post("/profile/edit")
async def profile_edit_submit(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle profile edit form submission"""
    from ..auth import get_current_user
    from ..models import User
    
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/profile/edit", status_code=303)
    
    # Get form data
    form = await request.form()
    first_name = form.get("first_name")
    last_name = form.get("last_name")
    
    # Validation
    if not first_name or not last_name:
        return request.app.state.templates.TemplateResponse(
            "profile_edit.html",
            {"request": request, "user": user, "error": "First and last name are required"}
        )
    
    # Update user in database
    result = await db.execute(select(User).where(User.id == user.id))
    db_user = result.scalar_one_or_none()
    
    if db_user:
        db_user.first_name = first_name
        db_user.last_name = last_name
        await db.commit()
    
    # Redirect to dashboard with success
    return RedirectResponse("/dashboard", status_code=303)


# -------------------------
# LOGOUT
# -------------------------
@router.get("/logout")
async def logout_route(request: Request):
    """Logout user by clearing session"""
    from ..auth import logout_user
    return await logout_user(request)
