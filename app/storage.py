# app/storage.py
"""
File storage module that supports both local filesystem and Azure Blob Storage.

Environment Detection:
- Local (ENV=local): Saves files to ./uploads directory
- Azure (ENV=production): Uploads to Azure Blob Storage

The module automatically switches based on AZURE_STORAGE_CONNECTION_STRING availability.
"""

from azure.storage.blob import BlobServiceClient
from app.settings import settings
import uuid
import os
import aiofiles
from pathlib import Path


def is_azure_storage_configured() -> bool:
    """
    Check if Azure Storage is properly configured.
    
    Returns:
        bool: True if Azure Storage connection string is available
    """
    return bool(settings.AZURE_STORAGE_CONNECTION_STRING)


async def save_file_local(file, folder: str = "uploads") -> str:
    """
    Save file to local filesystem.
    
    Args:
        file: FastAPI UploadFile object
        folder: Subdirectory to save file in
        
    Returns:
        str: Relative URL path to the saved file
    """
    # Create uploads directory if it doesn't exist
    upload_dir = Path(folder)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / filename
    
    # Save file
    content = await file.read()
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Return relative URL path
    return f"/{folder}/{filename}"


async def upload_file_to_blob(file, folder: str = "uploads") -> str:
    """
    Upload file to Azure Blob Storage.
    
    Args:
        file: FastAPI UploadFile object
        folder: Blob prefix/folder name
        
    Returns:
        str: Public URL to the uploaded blob
    """
    if not settings.AZURE_STORAGE_CONNECTION_STRING:
        raise RuntimeError("Azure Storage connection string not configured")
    
    # Create blob service client
    service_client = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    )
    
    # Get container client
    container_name = settings.AZURE_STORAGE_CONTAINER or "uploads"
    container_client = service_client.get_container_client(container_name)
    
    # Ensure container exists
    try:
        container_client.create_container()
    except Exception:
        # Container already exists
        pass
    
    # Generate unique blob name
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    blob_name = f"{folder}/{uuid.uuid4()}.{ext}"
    
    # Get blob client
    blob_client = container_client.get_blob_client(blob_name)
    
    # Read and upload file content
    content = await file.read()
    blob_client.upload_blob(content, overwrite=True)
    
    # Return public URL
    return blob_client.url


async def upload_file(file, folder: str = "uploads") -> str:
    """
    Upload file to appropriate storage based on environment configuration.
    
    Automatically detects whether to use local filesystem or Azure Blob Storage
    based on the presence of AZURE_STORAGE_CONNECTION_STRING.
    
    Args:
        file: FastAPI UploadFile object
        folder: Directory/folder name for organizing files
        
    Returns:
        str: URL or path to the uploaded file
    """
    if is_azure_storage_configured():
        print(f"Uploading to Azure Blob Storage: {folder}/{file.filename}")
        return await upload_file_to_blob(file, folder)
    else:
        print(f"Saving to local filesystem: {folder}/{file.filename}")
        return await save_file_local(file, folder)
