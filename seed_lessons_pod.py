import asyncio
from app.database import AsyncSessionLocal
from app.models import Course, Lesson
from sqlalchemy import select

# Map Course Title -> List of (Lesson Title, YouTube Video ID)
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

async def seed_lessons():
    async with AsyncSessionLocal() as session:
        print("Fetching courses...")
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        
        total_added = 0
        
        for course in courses:
            print(f"Processing '{course.title}'...")
            
            # Check if lessons already exist
            result = await session.execute(select(Lesson).where(Lesson.course_id == course.id))
            existing_lessons = result.scalars().all()
            
            if existing_lessons:
                print(f"  - Skipped (Already has {len(existing_lessons)} lessons)")
                continue
                
            # Add lessons
            if course.title in COURSE_LESSONS:
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
                print(f"  + Added {len(lessons_data)} lessons")
            else:
                print("  - No lesson data found for this course")
        
        if total_added > 0:
            await session.commit()
            print(f"\nSuccessfully added {total_added} lessons.")
        else:
            print("\nNo new lessons added.")

if __name__ == "__main__":
    asyncio.run(seed_lessons())
