# app/routes/course_detail.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import Course, Purchase
from ..auth import get_current_user
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/course/{course_id}")
async def course_detail(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Fetch course
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        return templates.TemplateResponse("404.html", {"request": request})

    # Check user purchase
    has_access = False
    if current_user:
        purchase = await db.execute(
            select(Purchase).where(
                Purchase.user_id == current_user.id,
                Purchase.course_id == course_id,
                Purchase.paid == True
            )
        )
        has_access = purchase.scalar_one_or_none() is not None

    return templates.TemplateResponse(
        "course_detail.html",
        {
            "request": request,
            "course": course,
            "current_user": current_user,
            "has_access": has_access
        }
    )
