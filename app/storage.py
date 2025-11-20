from azure.storage.blob import BlobServiceClient
from app.settings import settings
import uuid
import os

def get_blob_client():
    if not settings.AZURE_STORAGE_ACCOUNT_NAME:
        raise RuntimeError("Azure Storage not configured")

    connection_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={settings.AZURE_STORAGE_ACCOUNT_NAME};"
        f"AccountKey={settings.AZURE_STORAGE_ACCOUNT_KEY};"
        f"EndpointSuffix=core.windows.net"
    )

    service_client = BlobServiceClient.from_connection_string(connection_str)
    container_client = service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
    return container_client


async def upload_file_to_blob(file, folder="uploads"):
    """
    Uploads a file to blob storage and returns its public URL.
    """
    container = get_blob_client()

    ext = file.filename.split(".")[-1]
    blob_name = f"{folder}/{uuid.uuid4()}.{ext}"

    blob_client = container.get_blob_client(blob_name)

    # Read file content
    content = await file.read()

    # Upload
    blob_client.upload_blob(content, overwrite=True)

    # Return public URL
    if settings.AZURE_STORAGE_CDN_URL:
        return f"{settings.AZURE_STORAGE_CDN_URL}/{blob_name}"
    else:
        return (
            f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
            f"{settings.AZURE_STORAGE_CONTAINER}/{blob_name}"
        )


# import os
# from azure.storage.blob import BlobServiceClient
# from .config import settings

# def get_blob_service():
#     conn = settings.AZURE_STORAGE_CONNECTION_STRING
#     if not conn:
#         return None
#     return BlobServiceClient.from_connection_string(conn)

# def upload_blob(file_path: str, blob_name: str):
#     client = get_blob_service()
#     if not client:
#         dest = os.path.join('app', 'static', 'thumbnails', blob_name)
#         os.makedirs(os.path.dirname(dest), exist_ok=True)
#         with open(file_path, 'rb') as src, open(dest, 'wb') as dst:
#             dst.write(src.read())
#         return f'/static/thumbnails/{blob_name}'
#     container = client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
#     try:
#         container.create_container()
#     except Exception:
#         pass
#     blob_client = container.get_blob_client(blob_name)
#     with open(file_path, 'rb') as data:
#         blob_client.upload_blob(data, overwrite=True)
#     return blob_client.url
