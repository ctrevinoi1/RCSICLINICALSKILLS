import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

"""Sync all blobs from the handbook-images container to ./static/images.
Run this once (or periodically) before starting the FastAPI app so that
images can be served locally via /images/<filename>.

Usage:
    python sync_images.py

Environment variables required (loaded from .env):
    AZURE_BLOB_CONNECTION_STRING
    (or set the standard Azure Storage connection string in your shell)
"""

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING")

if not CONNECTION_STRING:
    raise RuntimeError("AZURE_BLOB_CONNECTION_STRING is not set in the environment.")

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

# Containers to sync → local sub-dirs mapping
CONTAINERS = {
    "handbook-images": os.path.join("static", "images"),
    "handbook-pages": os.path.join("static", "pages"),
}

for container, local_dir in CONTAINERS.items():
    os.makedirs(local_dir, exist_ok=True)
    print(f"\nSyncing blobs from container '{container}' to '{local_dir}'…")

    try:
        container_client = blob_service_client.get_container_client(container)
        blobs = list(container_client.list_blobs())
    except Exception as e:
        print(f"  ! Could not list blobs: {e}")
        continue

    if not blobs:
        print("  No blobs found.")
        continue

    downloaded = 0
    skipped = 0
    for blob in blobs:
        filename = os.path.basename(blob.name)
        local_path = os.path.join(local_dir, filename)

        # Skip existing file
        if os.path.exists(local_path):
            skipped += 1
            continue

        try:
            with open(local_path, "wb") as f:
                f.write(container_client.download_blob(blob).readall())
            downloaded += 1
            if downloaded % 50 == 0:
                print(f"  Downloaded {downloaded} blobs…")
        except Exception as e:
            print(f"  Failed to download {blob.name}: {e}")

    print(f"  Done. Downloaded {downloaded} new files, skipped {skipped} already present.") 