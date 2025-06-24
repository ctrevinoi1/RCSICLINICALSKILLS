import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import json

# --- Configuration ---
load_dotenv()

# Azure Blob Storage
blob_connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
blob_container_name = "handbook-pages"  # Separate container for full page images

# Source Document
pdf_path = "./clinical_skills_handbook.pdf"

# High quality settings for page rendering
PAGE_DPI = 200  # High DPI for clear, readable pages
IMAGE_FORMAT = "png"  # PNG for quality

def main():
    print("="*60)
    print("GENERATING HIGH-QUALITY PAGE IMAGES")
    print("="*60)
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    # Initialize blob service client
    print("\nInitializing Azure Blob Storage client...")
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    
    # Create container for page images if it doesn't exist
    try:
        blob_service_client.create_container(blob_container_name)
        print(f"Created container: {blob_container_name}")
    except Exception as e:
        if "ContainerAlreadyExists" in str(e):
            print(f"Container {blob_container_name} already exists")
        else:
            print(f"Error creating container: {e}")
            return
    
    # Open the PDF
    print(f"\nOpening PDF: {pdf_path}")
    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    print(f"Total pages: {total_pages}")
    
    # Create temporary directory for page images
    os.makedirs("./temp_pages", exist_ok=True)
    
    # Dictionary to store page URLs
    page_urls = {}
    
    print("\nGenerating page images...")
    print("-" * 40)
    
    # Process each page
    for page_num in range(total_pages):
        actual_page_num = page_num + 1
        
        try:
            # Get the page
            page = pdf_doc[page_num]
            
            # Render page as high-quality image
            mat = fitz.Matrix(PAGE_DPI/72.0, PAGE_DPI/72.0)
            pix = page.get_pixmap(matrix=mat)
            
            # Save locally first
            local_filename = f"page_{actual_page_num:04d}.{IMAGE_FORMAT}"
            local_path = f"./temp_pages/{local_filename}"
            pix.save(local_path)
            
            # Upload to blob storage
            blob_client = blob_service_client.get_blob_client(
                container=blob_container_name,
                blob=local_filename
            )
            
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            # Store the URL
            page_url = blob_client.url
            page_urls[actual_page_num] = page_url
            
            # Progress indicator
            if actual_page_num % 10 == 0:
                print(f"  Processed {actual_page_num}/{total_pages} pages...")
            
            # Clean up local file
            os.remove(local_path)
            
        except Exception as e:
            print(f"  ! Error processing page {actual_page_num}: {e}")
    
    pdf_doc.close()
    
    # Save page URLs mapping
    print(f"\nSaving page URL mappings...")
    with open("page_urls.json", "w") as f:
        json.dump(page_urls, f, indent=2)
    
    # Clean up temp directory
    try:
        os.rmdir("./temp_pages")
    except:
        pass
    
    print("\n" + "="*60)
    print("PAGE IMAGE GENERATION COMPLETE!")
    print(f"Generated {len(page_urls)} page images")
    print(f"Page URLs saved to: page_urls.json")
    print("="*60)

if __name__ == "__main__":
    main() 