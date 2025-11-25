import os
from azure.storage.blob import BlobServiceClient

# Try to get connection string from env or file
CONN_STR = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
if not CONN_STR:
    try:
        with open("/mnt/secrets/AZURE_STORAGE_CONNECTION_STRING", "r") as f:
            CONN_STR = f.read().strip()
    except Exception as e:
        print(f"Error reading secret: {e}")

if not CONN_STR:
    print("Could not find connection string")
    exit(1)

try:
    blob_service_client = BlobServiceClient.from_connection_string(CONN_STR)
    container_client = blob_service_client.get_container_client("azurecloud")
    
    print("Blobs in 'azurecloud' container:")
    blobs = container_client.list_blobs()
    for blob in blobs:
        print(blob.name)
        
except Exception as e:
    print(f"Error listing blobs: {e}")
