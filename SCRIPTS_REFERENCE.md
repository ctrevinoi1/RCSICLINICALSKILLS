# Scripts Reference Guide

## Overview of Scripts

This document provides detailed information about each script in the Clinical Skills AI Assistant project.

---

## Ingestion Pipeline Scripts

### 1. `ingest_document.py`

**Purpose**: Extracts text and images from PDF documents using Azure AI Document Intelligence.

**What it does**:
- Splits large PDFs into manageable chunks (max 64 pages per batch)
- Extracts text content with proper formatting
- Identifies and extracts images, tables, and diagrams
- Generates AI summaries for visual content
- Saves all data in JSONL format

**Usage**:
```bash
python ingest_document.py --file [PDF_FILE]
```

**Options**:
- `--file`: Path to the PDF file (required)
- `--batch_size`: Number of pages per batch (default: 64)
- `--model`: Document Intelligence model to use (default: "prebuilt-layout")

**Output**:
- `processed_handbook.jsonl`: Contains all extracted content
- `static/images/`: Directory with extracted images

**How it works internally**:
1. Reads the PDF file
2. Splits into batches to avoid API limits
3. Sends each batch to Azure Document Intelligence
4. Processes the response to extract:
   - Text paragraphs with page numbers
   - Tables as markdown
   - Images as PNG files
5. Uses GPT-4o to generate descriptions of visual content
6. Saves everything in a structured format

---

### 2. `generate_page_images.py`

**Purpose**: Converts each page of the PDF into an image and uploads to Azure Blob Storage.

**What it does**:
- Converts PDF pages to high-quality PNG images
- Uploads images to Azure Blob Storage
- Creates a mapping file of page numbers to blob URLs

**Usage**:
```bash
python generate_page_images.py [PDF_FILE]
```

**Arguments**:
- `PDF_FILE`: Path to the PDF file (required)

**Output**:
- `page_urls.json`: Maps page numbers to Azure blob URLs
- Images uploaded to `handbook-images` container in Azure

**Requirements**:
- Poppler must be installed (for PDF to image conversion)
- Azure Blob Storage connection string in `.env`

**Process**:
1. Uses Poppler's `pdftoppm` to convert each page to PNG
2. Uploads each image to Azure Blob Storage
3. Saves the blob URLs for later reference

---

### 3. `upload_to_search.py`

**Purpose**: Creates and populates the Azure AI Search index with processed content.

**What it does**:
- Creates search index with proper schema
- Generates embeddings for text and image summaries
- Uploads all content to make it searchable
- Enables semantic search capabilities

**Usage**:
```bash
# Create new index or update existing
python upload_to_search.py

# Force recreate index (deletes existing)
python upload_to_search.py --recreate
```

**Options**:
- `--recreate`: Delete and recreate the index

**Prerequisites**:
- Must run `ingest_document.py` first
- Requires `processed_handbook.jsonl` file

**Index Structure**:
- Text content with embeddings
- Image summaries with embeddings
- Source page references
- Content type classification
- Semantic search configuration

---

### 4. `sync_images.py`

**Purpose**: Downloads images from Azure Blob Storage to local storage.

**What it does**:
- Downloads extracted images from Azure
- Downloads full page images
- Creates local copies for offline access

**Usage**:
```bash
python sync_images.py
```

**No arguments required** - uses configuration from `.env` and existing JSON files

**Downloads to**:
- `static/images/`: Extracted images
- `static/pages/`: Full page images

**Why use this**:
- Faster image serving (no cloud latency)
- Works offline
- Reduces Azure bandwidth costs

---

## Utility Scripts

### 5. `check_index.py`

**Purpose**: Verifies the Azure AI Search index status and configuration.

**What it does**:
- Checks if index exists
- Shows document count
- Displays index schema
- Verifies semantic configuration

**Usage**:
```bash
python check_index.py
```

**Useful for**:
- Troubleshooting search issues
- Verifying index creation
- Checking document count

---

### 6. `check_embeddings.py`

**Purpose**: Ensures all documents have proper embeddings for vector search.

**What it does**:
- Queries the search index
- Identifies documents missing embeddings
- Reports on embedding coverage

**Usage**:
```bash
python check_embeddings.py
```

**What to look for**:
- All documents should have `content_vector`
- Documents with images should have `image_summary_vector`
- No missing embeddings for optimal search

---

## Main Application

### 7. `main.py`

**Purpose**: The FastAPI backend server that powers the web application.

**What it does**:
- Provides REST API for the chat interface
- Performs hybrid search (text + vector)
- Generates AI responses using GPT-4o
- Handles image serving with SAS tokens
- Manages chat history

**Usage**:
```bash
uvicorn main:app --reload
```

**API Endpoints**:
- `POST /api/query`: Main chat endpoint
  - Accepts: `{"query": "user question", "chat_history": []}`
  - Returns: AI response with citations

**Key Features**:
- Semantic search with re-ranking
- Multimodal responses (text + images)
- Secure image access via SAS tokens
- Context-aware responses

**Configuration**:
- Uses all Azure services configured in `.env`
- Serves on port 8000 by default

---

## Script Dependencies

```
ingest_document.py
    ↓
generate_page_images.py (parallel)
    ↓
upload_to_search.py
    ↓
(Optional) sync_images.py
    ↓
main.py (runtime)
```

---

## Common Script Patterns

### Error Handling
All scripts include:
- Try-catch blocks for API calls
- Graceful failure messages
- Logging of errors

### Azure Authentication
All scripts use:
- Environment variables from `.env`
- Azure SDK authentication
- Credential validation

### Progress Tracking
Long-running scripts show:
- Progress bars or counters
- Estimated time remaining
- Success/failure summaries

---

## Troubleshooting Scripts

### Script fails with "Module not found"
```bash
# Activate virtual environment
venv\Scripts\activate
# Reinstall requirements
pip install -r requirements.txt
```

### Script can't find Azure services
- Check `.env` file exists
- Verify all keys are correct
- Ensure no extra spaces in values

### Script runs but produces no output
- Check input files exist
- Verify Azure services are active
- Look for error messages in console

### Memory errors with large PDFs
- Reduce batch size in `ingest_document.py`
- Process PDF in sections
- Ensure adequate system RAM

---

## Performance Tips

1. **Parallel Processing**: 
   - Run `generate_page_images.py` while `ingest_document.py` is still running
   - They work on different aspects of the PDF

2. **Batch Operations**:
   - `upload_to_search.py` uploads in batches of 1000
   - Adjust batch size if experiencing timeouts

3. **Caching**:
   - `sync_images.py` only downloads missing images
   - Embeddings are cached in the search index

4. **Resource Usage**:
   - Monitor Azure usage during ingestion
   - Most operations fit within free tiers

---

## Development Tips

### Testing Individual Components
```bash
# Test document extraction
python ingest_document.py --file test.pdf --batch_size 10

# Test search functionality
python -c "import check_index; check_index.main()"

# Test API without frontend
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'
```

### Debugging
- Add `print()` statements in scripts
- Check Azure Portal for service logs
- Use `--verbose` flags where available
- Review generated JSON files for data issues 