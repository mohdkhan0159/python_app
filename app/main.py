from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.future import select
from .database import engine, Base, AsyncSessionLocal

from .routes import (
    users,
    courses,
    payments,
    course_detail,
    payment,
    dashboard,
    lessons,
    ui
)

from .auth import get_current_user
from .models import Course

# -------------------------------------------------------
#   APP SETUP
# -------------------------------------------------------

app = FastAPI(title="Learning Platform")

# Templates
templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates


# Session Middleware (must be added BEFORE any custom middleware)
from .settings import settings

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    same_site="lax"
)



# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------
#   USER MIDDLEWARE – attaches logged-in user
# -------------------------------------------------------
@app.middleware("http")
async def attach_user(request: Request, call_next):
    try:
        # --- SAFE DEBUG PRINT ---
        session_safe = None
        try:
            session_safe = dict(request.session)
        except Exception:
            session_safe = "UNREADABLE SESSION"

        # print("DEBUG SESSION:", session_safe)
        # -------------------------

        request.state.user = await get_current_user(request)

    except Exception as e:
        print("USER LOAD ERROR:", e)
        request.state.user = None

    return await call_next(request)



# -------------------------------------------------------
#   ROUTERS
# -------------------------------------------------------

app.include_router(users.router)
app.include_router(courses.router)
app.include_router(payments.router)
app.include_router(ui.router)
app.include_router(course_detail.router)
app.include_router(payment.router)
app.include_router(dashboard.router)
app.include_router(lessons.router)


# -------------------------------------------------------
#   STARTUP – DB INIT + SAMPLE DATA
# -------------------------------------------------------
@app.on_event("startup")
async def on_startup():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))

    # Add sample courses if DB empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Course))
        existing = result.scalars().all()

        if not existing:
            sample_courses = [
                Course(title="Python for Beginners", description="Learn Python basics.", thumbnail_path="python.png"),
                Course(title="Advanced Python", description="Master advanced Python techniques.", thumbnail_path="advanced_python.png"),
                Course(title="FastAPI Bootcamp", description="Build APIs with FastAPI.", thumbnail_path="fastapi.png"),
            ]
            session.add_all(sample_courses)
            await session.commit()


# -------------------------------------------------------
#   HOME PAGE
# -------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return app.state.templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)
# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")