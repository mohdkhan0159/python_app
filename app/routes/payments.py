from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import Course, Purchase
from ..auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# -----------------------------------------------------
# PAYMENT PAGE (requires login)
# -----------------------------------------------------
@router.get("/payment/{course_id}", response_class=HTMLResponse)
async def payment_page(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not current_user:
        return RedirectResponse(f"/login?next=/payment/{course_id}", status_code=303)

    q = await db.execute(select(Course).where(Course.id == course_id))
    course = q.scalar_one_or_none()

    if not course:
        return templates.TemplateResponse("404.html", {"request": request})

    return templates.TemplateResponse(
        "payment.html",
        {"request": request, "course": course, "user": current_user}
    )


# -----------------------------------------------------
# PROCESS PAYMENT (dummy logic)
# -----------------------------------------------------
@router.post("/payment/{course_id}")
async def process_payment(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not current_user:
        return RedirectResponse(f"/login?next=/payment/{course_id}", status_code=303)

    purchase = Purchase(
        user_id=current_user.id,
        course_id=course_id,
        paid=True
    )

    db.add(purchase)
    await db.commit()

    return templates.TemplateResponse(
        "payment_success.html",
        {"request": request, "course_id": course_id}
    )
