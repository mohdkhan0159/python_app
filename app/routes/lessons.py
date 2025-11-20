# app/routes/lessons.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.templating import Jinja2Templates

from ..database import get_db
from ..models import Course, Lesson, Purchase
from ..auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# -----------------------------------------------------------
# PAGE 1: Lessons list for a course
# -----------------------------------------------------------
@router.get("/lessons/{course_id}", response_class=HTMLResponse)
async def lessons_page(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    # Check purchase
    q = await db.execute(select(Purchase).where(
        Purchase.course_id == course_id,
        Purchase.user_id == current_user.id,
        Purchase.paid == True
    ))
    purchase = q.scalar_one_or_none()

    if not purchase:
        return RedirectResponse(f"/payment/{course_id}", status_code=303)

    # Load course
    qc = await db.execute(select(Course).where(Course.id == course_id))
    course = qc.scalar_one_or_none()

    # Load lessons
    ql = await db.execute(select(Lesson).where(Lesson.course_id == course_id))
    lessons = ql.scalars().all()

    return templates.TemplateResponse("lessons.html", {
        "request": request,
        "course": course,
        "lessons": lessons
    })


# -----------------------------------------------------------
# PAGE 2: View a single lesson + video
# -----------------------------------------------------------
@router.get("/lesson/{lesson_id}", response_class=HTMLResponse)
async def lesson_view(
    lesson_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    # Get lesson
    ql = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = ql.scalar_one_or_none()

    if not lesson:
        raise HTTPException(404, "Lesson not found")

    # Check purchase for this lesson’s course
    qp = await db.execute(select(Purchase).where(
        Purchase.course_id == lesson.course_id,
        Purchase.user_id == current_user.id,
        Purchase.paid == True
    ))
    purchase = qp.scalar_one_or_none()

    if not purchase:
        return RedirectResponse(f"/payment/{lesson.course_id}", status_code=303)

    # Load course
    qc = await db.execute(select(Course).where(Course.id == lesson.course_id))
    course = qc.scalar_one_or_none()

    # Convert YouTube URL → embed ID
    video_id = None
    if lesson.video_url:
        import re
        match = re.search(r"v=([^&]+)", lesson.video_url)
        video_id = match.group(1) if match else lesson.video_url

    return templates.TemplateResponse("lesson_view.html", {
        "request": request,
        "lesson": lesson,
        "course": course,
        "video_id": video_id
    })
