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
from .models import Course, Lesson

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
app.include_router(ui.router)  # UI routes first (HTML pages)
app.include_router(courses.router)  # API routes second
app.include_router(payments.router)
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
            # Build thumbnail URLs based on environment
            if settings.ENV == "production" and settings.AZURE_STORAGE_ACCOUNT_NAME:
                # Production: Use Azure Blob Storage URLs
                storage_account = settings.AZURE_STORAGE_ACCOUNT_NAME
                container = settings.AZURE_STORAGE_CONTAINER or "uploads"
                base_url = f"https://{storage_account}.blob.core.windows.net/{container}"
                
                sample_courses = [
                    Course(title="Python for Beginners", description="Learn Python from scratch with hands-on examples.", thumbnail_path=f"{base_url}/python.png"),
                    Course(title="Advanced Python", description="Master advanced Python techniques and best practices.", thumbnail_path=f"{base_url}/advanced_python.png"),
                    Course(title="FastAPI Bootcamp", description="Build modern APIs with FastAPI framework.", thumbnail_path=f"{base_url}/fastapi.png"),
                    Course(title="Docker & Kubernetes", description="Container orchestration and deployment.", thumbnail_path=f"{base_url}/docker_kubernetes.png"),
                    Course(title="React for Beginners", description="Build interactive UIs with React.", thumbnail_path=f"{base_url}/react.png"),
                    Course(title="Node.js Backend Development", description="Server-side JavaScript with Node.js.", thumbnail_path=f"{base_url}/nodejs.png"),
                    Course(title="Azure Cloud Fundamentals", description="Cloud computing with Microsoft Azure.", thumbnail_path=f"{base_url}/azure.png"),
                    Course(title="SQL Database Design", description="Design and optimize relational databases.", thumbnail_path=f"{base_url}/sql.png"),
                    Course(title="DevOps with CI/CD", description="Automate deployment pipelines.", thumbnail_path=f"{base_url}/devops.png"),
                    Course(title="Machine Learning with Python", description="Introduction to ML and AI.", thumbnail_path=f"{base_url}/ml.png"),
                ]
            else:
                # Local: Use relative paths
                sample_courses = [
                    Course(title="Python for Beginners", description="Learn Python from scratch with hands-on examples.", thumbnail_path="/uploads/python.png"),
                    Course(title="Advanced Python", description="Master advanced Python techniques and best practices.", thumbnail_path="/uploads/advanced_python.png"),
                    Course(title="FastAPI Bootcamp", description="Build modern APIs with FastAPI framework.", thumbnail_path="/uploads/fastapi.png"),
                    Course(title="Docker & Kubernetes", description="Container orchestration and deployment.", thumbnail_path="/uploads/docker_kubernetes.png"),
                    Course(title="React for Beginners", description="Build interactive UIs with React.", thumbnail_path="/uploads/react.png"),
                    Course(title="Node.js Backend Development", description="Server-side JavaScript with Node.js.", thumbnail_path="/uploads/nodejs.png"),
                    Course(title="Azure Cloud Fundamentals", description="Cloud computing with Microsoft Azure.", thumbnail_path="/uploads/azure.png"),
                    Course(title="SQL Database Design", description="Design and optimize relational databases.", thumbnail_path="/uploads/sql.png"),
                    Course(title="DevOps with CI/CD", description="Automate deployment pipelines.", thumbnail_path="/uploads/devops.png"),
                    Course(title="Machine Learning with Python", description="Introduction to ML and AI.", thumbnail_path="/uploads/ml.png"),
                ]
            
            session.add_all(sample_courses)
            await session.commit()

        # Add lessons to courses if they don't have any
    async with AsyncSessionLocal() as session:
        from app.models import Lesson
        
        # Lesson data matching seed_lessons_pod.py
        COURSE_LESSONS = {
            "Python for Beginners": [
                ("Introduction to Python", "_uQrJ0TkZlc"),
                ("Variables and Data Types", "vKqVnr0BE48"),
                ("Control Flow", "6iF8Xb7Z3wQ")
            ],
            "Advanced Python": [
                ("Decorators", "FsAPt_9Bf3U"),
                ("Generators", "bD05uGo_sVI"),
                ("Context Managers", "eba-1PHD8ng")
            ],
            "FastAPI Bootcamp": [
                ("FastAPI Setup", "tLKKmouU5m4"),
                ("Path Parameters", "7t2alSnE2SY"),
                ("Query Parameters", "0sOvCWFmrtA")
            ],
            "Docker & Kubernetes": [
                ("Docker Basics", "3c-iBn73dDE"),
                ("Docker Compose", "HG68Ymazo18"),
                ("Kubernetes Intro", "d6WC5n9G_sM")
            ],
            "React for Beginners": [
                ("React Hello World", "SqcY0GlETk4"),
                ("Components", "Y2hgEGPzT2c"),
                ("State Management", "4ORZ1Gmja5I")
            ],
            "Node.js Backend Development": [
                ("Node.js Intro", "Oe421EPjeBE"),
                ("Modules", "xHLd36QoS4k"),
                ("Express Framework", "L72fhGm1tfE")
            ],
            "Azure Cloud Fundamentals": [
                ("Azure Overview", "NKEFWyqJ5dy"),
                ("Virtual Machines", "zL74eg5s2X4"),
                ("App Services", "1Xj5J5s0s4w")
            ],
            "SQL Database Design": [
                ("SQL Basics", "HXV3zeQKqGY"),
                ("Normalization", "UrYXuJlpqbI"),
                ("Joins", "9yeOJ0ZHU60")
            ],
            "DevOps with CI/CD": [
                ("DevOps Intro", "9pZ2xmsSDdo"),
                ("Jenkins Setup", "FX322RVNGj4"),
                ("GitHub Actions", "R8_veQiYBjI")
            ],
            "Machine Learning with Python": [
                ("ML Intro", "7eh4d6sabA0"),
                ("Linear Regression", "E5RjzSK0fvY"),
                ("Classification", "zM4VZR0px8E")
            ]
        }
        
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        
        total_added = 0
        for course in courses:
            # Check if lessons already exist
            result = await session.execute(select(Lesson).where(Lesson.course_id == course.id))
            existing_lessons = result.scalars().all()
            
            if not existing_lessons and course.title in COURSE_LESSONS:
                lessons_data = COURSE_LESSONS[course.title]
                for title, video_id in lessons_data:
                    lesson = Lesson(
                        course_id=course.id,
                        title=title,
                        content=f"This is the lesson content for {title}.",
                        video_url=video_id
                    )
                    session.add(lesson)
                    total_added += 1
        
        if total_added > 0:
            await session.commit()
            # print(f"✅ Added {total_added} lessons to courses")
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
