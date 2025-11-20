from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import AsyncSessionLocal, get_db
from ..models import Course, Purchase, Lesson
from ..auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# -----------------------------------------------------
# PUBLIC — view courses
# -----------------------------------------------------
@router.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    return templates.TemplateResponse(
        "courses.html",
        {"request": request, "courses": courses}
    )


# -----------------------------------------------------
# LOGIN PAGE
# -----------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/dashboard"):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next}
    )


# -----------------------------------------------------
# DASHBOARD — private
# -----------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login?next=/dashboard", status_code=303)

    result = await db.execute(
        select(Course)
        .join(Purchase)
        .where(Purchase.user_id == current_user.id, Purchase.paid == True)
    )

    courses = result.scalars().all()

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "courses": courses, "user": current_user}
    )

@router.get("/lesson/{lesson_id}", response_class=HTMLResponse)
async def lesson_detail(request: Request, lesson_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return request.app.state.templates.TemplateResponse(
        "lesson_detail.html",
        {"request": request, "lesson": lesson}
    )

@router.get("/")
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.is_published == True))
    courses = result.scalars().all()

    return request.app.state.templates.TemplateResponse(
        "index.html",
        {"request": request, "courses": courses}
    )

@router.get("/course/{course_id}", response_class=HTMLResponse)
async def course_detail(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if user purchased
    has_access = False
    if current_user:
        p = await db.execute(
            select(Purchase).where(
                Purchase.course_id == course_id,
                Purchase.user_id == current_user.id,
                Purchase.paid == True
            )
        )
        has_access = p.scalars().first() is not None

    return templates.TemplateResponse(
        "course_detail.html",
        {"request": request, "course": course, "has_access": has_access}
    )

@router.get("/profile", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login?next=/profile")

    # Get purchased courses
    result = await db.execute(
        select(Course)
        .join(Purchase)
        .where(Purchase.user_id == current_user.id, Purchase.paid == True)
    )
    courses = result.scalars().all()

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "courses": courses
        }
    )
