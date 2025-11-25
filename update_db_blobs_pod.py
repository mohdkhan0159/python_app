import asyncio
from app.database import AsyncSessionLocal
from app.models import Course
from sqlalchemy import select

# Configuration
STORAGE_ACCOUNT = "azurecloud0159"
CONTAINER = "azurecloud"
BASE_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER}"

# Map course titles to blob names
THUMBNAILS = {
    "Python for Beginners": "python_for_beginner.png",
    "Advanced Python": "advanced_python.png",
    "FastAPI Bootcamp": "fastapi_bootcamp.png",
    "Docker & Kubernetes": "docker_kubernetes.png",
    "React for Beginners": "react_beginners.png",
    "Node.js Backend Development": "nodejs_backend.png",
    "Azure Cloud Fundamentals": "azure_cloud_fundamental.png",
    "SQL Database Design": "sql_database_design.png",
    "DevOps with CI/CD": "devops_with_cicd.png",
    "Machine Learning with Python": "machine_learning_with_python.png"
}

async def update_thumbnails():
    async with AsyncSessionLocal() as session:
        print("Fetching courses...")
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        
        updated_count = 0
        for course in courses:
            if course.title in THUMBNAILS:
                blob_name = THUMBNAILS[course.title]
                new_url = f"{BASE_URL}/{blob_name}"
                
                print(f"Updating '{course.title}'")
                print(f"  Old: {course.thumbnail_path}")
                print(f"  New: {new_url}")
                
                course.thumbnail_path = new_url
                updated_count += 1
            else:
                print(f"Skipping '{course.title}' (No mapping found)")
        
        if updated_count > 0:
            await session.commit()
            print(f"\nSuccessfully updated {updated_count} courses.")
        else:
            print("\nNo courses updated.")

if __name__ == "__main__":
    asyncio.run(update_thumbnails())
