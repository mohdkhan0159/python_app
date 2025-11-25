import asyncio
from app.database import AsyncSessionLocal
from app.models import Course, Lesson
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        print("\n--- COURSES ---")
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        for c in courses:
            print(f"C:{c.id}|{c.title}|{c.thumbnail_path}")
        
        print("\n--- LESSONS ---")
        result = await session.execute(select(Lesson))
        lessons = result.scalars().all()
        print(f"Found {len(lessons)} lessons.")
        for l in lessons:
            print(f"L:{l.id}|{l.title}|{l.video_url}")

if __name__ == "__main__":
    asyncio.run(main())
