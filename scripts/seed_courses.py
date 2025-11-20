import asyncio
from app.database import engine, AsyncSessionLocal
from app import models

COURSES = [{'title': f'Course {i}', 'description': f'Description for course {i}', 'thumbnail_path': f'/static/thumbnails/course_{i}.svg', 'price_cents': 1000*i} for i in range(1,11)]

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        q = await session.execute(select(models.Course))
        existing = q.scalars().all()
        if existing:
            print('Courses exist, skipping')
            return
        for c in COURSES:
            session.add(models.Course(**c))
        await session.commit()
        print('Seeded courses')

if __name__ == '__main__':
    asyncio.run(seed())
