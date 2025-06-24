import os
import json
import base64
import io
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.storage.blob import BlobServiceClient
import fitz  # PyMuPDF
from PIL import Image
import hashlib
import shutil

# --- Configuration ---
load_dotenv()

# Azure AI Document Intelligence
doc_intel_endpoint = os.getenv("AZURE_DOC_INTEL_ENDPOINT")
doc_intel_key = os.getenv("AZURE_DOC_INTEL_KEY")

# Azure Blob Storage
blob_connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
blob_container_name = "handbook-images"  # Container to store extracted images

# Azure OpenAI
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
openai_embedding_model = "text-embedding-3-large"
openai_vision_model = "gpt-4o"

# Source Document
pdf_path = "./clinical_skills_handbook.pdf"
output_filename = "processed_handbook.jsonl"

# Processing configuration
MAX_PAGES_PER_CHUNK = 20  # Process 20 pages at a time for Document Intelligence
MAX_EMBEDDING_LENGTH = 8000  # Maximum characters for embedding
VISUAL_DPI = 150  # DPI for rendering tables and diagrams

# --- Helper Functions ---
def get_file_hash(content):
    """Generate a hash for file content to create unique filenames."""
    return hashlib.md5(content).hexdigest()[:12]

def save_and_upload_image(image_content, image_name, blob_service_client):
    """Save image locally and upload to blob storage."""
    # Create temp images directory if it doesn't exist
    os.makedirs("./temp_images", exist_ok=True)
    
    local_path = f"./temp_images/{image_name}"
    
    # Save locally
    if isinstance(image_content, bytes):
        with open(local_path, "wb") as f:
            f.write(image_content)
    else:
        # If it's a PIL Image
        image_content.save(local_path)
    
    # Upload to blob
    blob_client = blob_service_client.get_blob_client(
        container=blob_container_name,
        blob=image_name
    )
    
    # Check if blob already exists to avoid re-uploading
    if blob_client.exists():
        print(f"  - Blob '{image_name}' already exists. Skipping upload.")
        return blob_client.url

    with open(local_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    
    return blob_client.url

def extract_images_from_page(page, page_num, blob_service_client):
    """Extract all images from a PDF page using PyMuPDF."""
    images_info = []
    image_list = page.get_images(full=True)
    
    for img_index, img in enumerate(image_list):
        try:
            # Get image data
            xref = img[0]
            pix = fitz.Pixmap(page.parent, xref)
            
            # Convert to RGB if necessary
            if pix.n - pix.alpha > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            
            # Get image bytes
            img_data = pix.tobytes("png")
            
            # Create unique filename
            img_hash = get_file_hash(img_data)
            img_name = f"page_{page_num}_img_{img_index}_{img_hash}.png"
            
            # Upload to blob storage
            img_url = save_and_upload_image(img_data, img_name, blob_service_client)
            
            # Get image position on page
            img_rect = page.get_image_bbox(img)
            
            images_info.append({
                "id": f"page_{page_num}_img_{img_hash}",
                "url": img_url,
                "page": page_num,
                "type": "extracted_image",
                "rect": {
                    "x0": img_rect.x0,
                    "y0": img_rect.y0,
                    "x1": img_rect.x1,
                    "y1": img_rect.y1
                }
            })
            
            print(f"  - Extracted image {img_index + 1} from page {page_num}")
            
        except Exception as e:
            print(f"  ! Error extracting image {img_index} from page {page_num}: {e}")
    
    return images_info

def render_table_as_image(pdf_doc, page_num, bbox, table_index, blob_service_client):
    """Render a table region as an image using its bounding box."""
    try:
        page = pdf_doc[page_num - 1]  # PyMuPDF uses 0-based indexing
        
        # Create a rectangle from the bounding box
        page_rect = page.rect
        x0 = bbox[0] * page_rect.width
        y0 = bbox[1] * page_rect.height
        x1 = bbox[2] * page_rect.width
        y1 = bbox[3] * page_rect.height
        
        padding = 10
        clip_rect = fitz.Rect(x0 - padding, y0 - padding, x1 + padding, y1 + padding).intersect(page_rect)
        
        # Render the table region as an image
        mat = fitz.Matrix(VISUAL_DPI/72.0, VISUAL_DPI/72.0)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect)
        
        img_data = pix.tobytes("png")
        img_hash = get_file_hash(img_data)
        img_name = f"page_{page_num}_table_{table_index}_{img_hash}.png"
        
        img_url = save_and_upload_image(img_data, img_name, blob_service_client)
        
        print(f"  - Rendered table {table_index} from page {page_num}")
        return img_url, img_name
        
    except Exception as e:
        print(f"  ! Error rendering table {table_index} on page {page_num}: {e}")
        return None, None

def get_image_verbalization(image_url_or_path):
    """Uses GPT-4o to create a detailed text description of an image."""
    print(f"  - Verbalizing visual content...")
    
    try:
        with open(image_url_or_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = openai_client.chat.completions.create(
            model=openai_vision_model,
            messages=[
                { "role": "user", "content": [
                    { "type": "text", "text": "Describe this medical diagram, flowchart, or table in detail. Explain its purpose, key components, and the information it conveys. Be comprehensive, as this description will be used for semantic search." },
                    { "type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"} }
                ]}
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ! Error verbalizing image: {e}")
        return "Medical visual content"

def create_text_embedding(text):
    """Generates a vector embedding for a text chunk."""
    if len(text) > MAX_EMBEDDING_LENGTH:
        text = text[:MAX_EMBEDDING_LENGTH]
    
    try:
        response = openai_client.embeddings.create(
            input=text, 
            model=openai_embedding_model,
            dimensions=1536  # Specify 1536 dimensions to match the index schema
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  ! Error creating embedding: {e}")
        return [0.0] * 1536  # Return 1536 zeros on error to match schema

def process_pdf_visual_content(pdf_path, blob_service_client, processed_ids, output_file):
    """Extract all images and visual content from PDF using PyMuPDF."""
    print("\nExtracting visual content from PDF...")
    
    pdf_doc = fitz.open(pdf_path)
    new_items_processed = 0
    
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        actual_page_num = page_num + 1
        
        images = extract_images_from_page(page, actual_page_num, blob_service_client)
        
        for visual in images:
            if visual['id'] in processed_ids:
                print(f"  - Skipping already processed visual: {visual['id']}")
                continue

            try:
                local_path = f"./temp_images/{os.path.basename(visual['url'].split('?')[0])}"
                image_summary = get_image_verbalization(local_path)
                
                chunk_data = {
                    "id": visual['id'],
                    "content": f"Visual content on page {visual['page']}",
                    "source_page": visual['page'],
                    "content_type": "image",
                    "image_reference": visual['url'],
                    "image_summary": image_summary,
                    "content_vector": create_text_embedding(f"Image on page {visual['page']}: {image_summary}"),
                    "image_summary_vector": create_text_embedding(image_summary)
                }

                with open(output_file, "a") as f:
                    f.write(json.dumps(chunk_data) + "\n")
                
                processed_ids.add(visual['id'])
                new_items_processed += 1
                
            except Exception as e:
                print(f"  ! Error processing visual: {e}")
    
    pdf_doc.close()
    print(f"\nFinished visual content extraction. Processed {new_items_processed} new visuals.")

def process_chunk_with_doc_intel(chunk_path, doc_intel_client, blob_service_client, pdf_doc, processed_ids, output_file, page_offset=0):
    """Process a PDF chunk with Document Intelligence to find tables and layout."""
    print(f"\nAnalyzing document structure with Document Intelligence for pages {page_offset + 1}...")
    
    new_items_processed = 0
    
    try:
        with open(chunk_path, "rb") as f:
            poller = doc_intel_client.begin_analyze_document("prebuilt-layout", analyze_request=f, content_type="application/pdf")
        
        result: AnalyzeResult = poller.result()
        
        # Process tables
        if hasattr(result, 'tables') and result.tables:
            for i, table in enumerate(result.tables):
                try:
                    actual_page = table.bounding_regions[0].page_number + page_offset
                    table_id = f"page_{actual_page}_table_{i}"

                    if table_id in processed_ids:
                        print(f"  - Skipping already processed table: {table_id}")
                        continue

                    # The BoundingRegion object now has a 'polygon' attribute instead of 'bounding_box'.
                    # We can construct the bounding box from the polygon's vertices.
                    polygon = table.bounding_regions[0].polygon
                    
                    # The polygon is a sequence of x, y coordinates for each vertex.
                    # We can calculate the bounding box from the min/max of these coordinates.
                    min_x = min(polygon[i] for i in range(0, len(polygon), 2))
                    max_x = max(polygon[i] for i in range(0, len(polygon), 2))
                    min_y = min(polygon[i] for i in range(1, len(polygon), 2))
                    max_y = max(polygon[i] for i in range(1, len(polygon), 2))
                    bbox = [min_x, min_y, max_x, max_y]
                    
                    table_img_url, img_name = render_table_as_image(pdf_doc, actual_page, bbox, i, blob_service_client)
                    
                    if table_img_url:
                        local_path = f"./temp_images/{img_name}"
                        image_summary = get_image_verbalization(local_path)
                    else:
                        # Fallback to text if image rendering fails
                        print(f"  ! Image rendering failed for table {i} on page {actual_page}. Falling back to text.")
                        image_summary = "Table content: "
                        if hasattr(table, 'cells'):
                            for cell in table.cells:
                                if hasattr(cell, 'content'):
                                    image_summary += cell.content + " | "
                        # No image reference if rendering failed
                        table_img_url = None

                    chunk_data = {
                        "id": table_id,
                        "content": f"Table on page {actual_page}", "source_page": actual_page, "content_type": "table",
                        "image_reference": table_img_url, "image_summary": image_summary,
                        "content_vector": create_text_embedding(f"Table on page {actual_page}: {image_summary}"),
                        "image_summary_vector": create_text_embedding(image_summary)
                    }

                    with open(output_file, "a") as f:
                        f.write(json.dumps(chunk_data) + "\n")
                    
                    processed_ids.add(table_id)
                    new_items_processed += 1
                
                except Exception as e:
                    print(f"  ! Error processing table {i}: {e}")
        
        # Process paragraphs
        if hasattr(result, 'paragraphs') and result.paragraphs:
            for i, para in enumerate(result.paragraphs):
                try:
                    if para.content and len(para.content.strip()) > 10:
                        actual_page = para.bounding_regions[0].page_number + page_offset
                        # Create a deterministic ID using a hash of the content
                        content_hash = hashlib.md5(para.content.encode('utf-8')).hexdigest()[:12]
                        para_id = f"page_{actual_page}_para_{i}_{content_hash}"

                        if para_id in processed_ids:
                            continue

                        chunk_data = {
                            "id": para_id, "content": para.content, "source_page": actual_page, "content_type": "text",
                            "image_reference": None, "image_summary": None,
                            "content_vector": create_text_embedding(para.content), "image_summary_vector": None
                        }

                        with open(output_file, "a") as f:
                            f.write(json.dumps(chunk_data) + "\n")
                        
                        processed_ids.add(para_id)
                        new_items_processed += 1
                except Exception as e:
                    print(f"  ! Error processing paragraph: {e}")
    except Exception as e:
        print(f"  ! Error in Document Intelligence processing: {e}")
    
    print(f"Finished structure analysis. Processed {new_items_processed} new items.")

def split_pdf_for_doc_intel(pdf_doc, temp_dir, pages_per_chunk=MAX_PAGES_PER_CHUNK):
    total_pages = len(pdf_doc)
    chunks = []
    
    for start_page in range(0, total_pages, pages_per_chunk):
        end_page = min(start_page + pages_per_chunk, total_pages)
        
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(pdf_doc, from_page=start_page, to_page=end_page-1)
        
        chunk_path = os.path.join(temp_dir, f"chunk_{start_page + 1}-{end_page}.pdf")
        chunk_doc.save(chunk_path)
        
        chunks.append({'path': chunk_path, 'start_page': start_page + 1})
        chunk_doc.close()
    
    return chunks

# --- Main Ingestion Logic ---
def main():
    print("="*60 + "\nCLINICAL HANDBOOK INGESTION - MULTIMODAL PROCESSING\n" + "="*60)
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}"); return
    
    # Load already processed IDs
    processed_ids = set()
    if os.path.exists(output_filename):
        print(f"Resuming from existing output file: {output_filename}")
        with open(output_filename, "r") as f:
            for line in f:
                try: processed_ids.add(json.loads(line)['id'])
                except: continue
        print(f"Loaded {len(processed_ids)} already processed items.")

    # Initialize clients
    print("\nInitializing Azure clients...")
    doc_intel_client = DocumentIntelligenceClient(endpoint=doc_intel_endpoint, credential=AzureKeyCredential(doc_intel_key))
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    
    try:
        blob_service_client.create_container(blob_container_name)
        print(f"Created container: {blob_container_name}")
    except Exception as e:
        if "ContainerAlreadyExists" in str(e): print(f"Container {blob_container_name} already exists")
        else: print(f"Error creating container: {e}")
    
    # Process visual content
    process_pdf_visual_content(pdf_path, blob_service_client, processed_ids, output_filename)
    
    # Process text and tables
    print("\n" + "-"*60 + "\nProcessing document structure and tables...\n" + "-"*60)
    
    temp_chunk_dir = "./temp_pdf_chunks"
    os.makedirs(temp_chunk_dir, exist_ok=True)
    
    pdf_doc = fitz.open(pdf_path)
    chunks = split_pdf_for_doc_intel(pdf_doc, temp_chunk_dir)
    
    for chunk in chunks:
        page_offset = chunk['start_page'] - 1
        process_chunk_with_doc_intel(chunk['path'], doc_intel_client, blob_service_client, pdf_doc, processed_ids, output_filename, page_offset)
    
    pdf_doc.close()
    
    # Clean up
    print("\nCleaning up temporary files...")
    shutil.rmtree("./temp_images", ignore_errors=True)
    shutil.rmtree(temp_chunk_dir, ignore_errors=True)
    
    print("\n" + "="*60)
    print("INGESTION COMPLETE!")
    print(f"Total items in {output_filename}: {len(processed_ids)}")
    print("="*60)

if __name__ == "__main__":
    main() 