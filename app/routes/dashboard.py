# app/routes/dashboard.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.templating import Jinja2Templates

from ..database import get_db
from ..models import Purchase, Course
from ..auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(request: Request,
                    db: AsyncSession = Depends(get_db),
                    current_user=Depends(get_current_user)):

    q = await db.execute(
        select(Purchase).where(Purchase.user_id == current_user.id, Purchase.paid == True)
    )
    purchases = q.scalars().all()

    courses = []
    for p in purchases:
        r = await db.execute(select(Course).where(Course.id == p.course_id))
        c = r.scalars().first()
        if c:
            courses.append(c)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "courses": courses
    })
