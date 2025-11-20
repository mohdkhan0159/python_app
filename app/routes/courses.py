# app/routes/courses.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from azure.storage.blob.aio import BlobClient
from ..database import get_db
from ..crud import list_courses, get_course
from ..schemas import CourseOut, CourseBase
from ..models import Course
from app.settings import settings

import uuid

router = APIRouter(prefix='/courses', tags=['courses'])


@router.get('/', response_model=list[CourseOut])
async def all_courses(db: AsyncSession = Depends(get_db)):
    return await list_courses(db)


@router.post('/', response_model=CourseOut)
async def create_course(course: CourseBase, db: AsyncSession = Depends(get_db)):
    new = Course(**course.dict())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new


@router.post('/{course_id}/thumbnail')
async def upload_thumbnail(
    course_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):

    # 1. Make sure course exists
    crs = await get_course(db, course_id)
    if not crs:
        raise HTTPException(404, 'Course not found')

    # 2. Create blob name
    extension = file.filename.split(".")[-1]
    blob_name = f"course_{course_id}_{uuid.uuid4().hex}.{extension}"

    # 3. Create Blob Client
    blob_client = BlobClient.from_connection_string(
        conn_str=settings.AZURE_STORAGE_CONNECTION_STRING,
        container_name=settings.AZURE_BLOB_CONTAINER,
        blob_name=blob_name
    )

    # 4. Read bytes & upload
    data = await file.read()
    await blob_client.upload_blob(data, overwrite=True)

    # 5. Construct URL
    blob_url = blob_client.url

    # 6. Save URL in DB
    crs.thumbnail_path = blob_url
    await db.commit()
    await db.refresh(crs)

    return {"thumbnail_url": blob_url}
