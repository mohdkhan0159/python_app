from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import random

from ..database import get_db
from ..auth import get_current_user
from ..models import Course, Purchase

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ------------------------------
# STEP 1 — Load payment page
# ------------------------------
@router.get("/payment/{course_id}")
async def payment_page(course_id: int, request: Request, db: AsyncSession = Depends(get_db)):

    q = await db.execute(select(Course).where(Course.id == course_id))
    course = q.scalar_one_or_none()

    if not course:
        return templates.TemplateResponse("404.html", {"request": request})

    return templates.TemplateResponse("payment.html", {
        "request": request,
        "course": course
    })


# ------------------------------
# STEP 2 — Process payment
# ------------------------------
@router.post("/payment/{course_id}")
async def process_payment(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Require login ONLY for POST
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    form = await request.form()
    card_number = form.get("card_number")
    cvv = form.get("cvv")

    # Basic fake validation
    if len(card_number) < 12 or len(cvv) < 3:
        return templates.TemplateResponse(
            "payment_failed.html",
            {"request": request, "course_id": course_id}
        )

    # Fake random approval / decline (50% chance)
    approved = random.choice([True, False, True])  # slightly biased to approve

    if not approved:
        return templates.TemplateResponse(
            "payment_failed.html",
            {"request": request, "course_id": course_id}
        )

    # Save purchase
    new_purchase = Purchase(
        user_id=current_user.id,
        course_id=course_id,
        paid=True
    )

    db.add(new_purchase)
    await db.commit()

    return templates.TemplateResponse(
        "payment_success.html",
        {"request": request, "course_id": course_id}
    )
