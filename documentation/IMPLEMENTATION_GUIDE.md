# Clinical Skills Handbook AI Assistant - Complete Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Windows Setup](#windows-setup)
4. [Azure Services Setup](#azure-services-setup)
5. [Project Installation](#project-installation)
6. [Configuration](#configuration)
7. [Understanding the System Components](#understanding-the-system-components)
8. [Running the Ingestion Pipeline](#running-the-ingestion-pipeline)
9. [Launching the Web Application](#launching-the-web-application)
10. [Troubleshooting](#troubleshooting)
11. [Architecture Diagram](#architecture-diagram)

---

## Overview

This guide will walk you through setting up a sophisticated AI-powered clinical assistant that can answer questions about medical procedures using both text and images from the RCSI Handbook of Clinical Skills. Think of it as creating your own specialized ChatGPT that only knows about this specific medical handbook.

### What You'll Build
- **A Smart Search System**: That understands medical questions and finds relevant information
- **An AI Assistant**: That provides accurate answers using only the handbook content
- **A Visual Interface**: That shows relevant diagrams and images alongside text answers
- **A Web Application**: That medical professionals can use from any browser

### How It Works (Simple Version)
1. **Preparation Phase**: We process the PDF handbook and extract all text and images
2. **Storage Phase**: We store this information in a cloud-based searchable database
3. **Question Phase**: When someone asks a question, we search for relevant information
4. **Answer Phase**: We use AI to create a clear answer based only on what's in the handbook
5. **Display Phase**: We show the answer along with relevant images and page references

---

## Prerequisites

Before starting, ensure you have:

### Required Accounts
- **Microsoft Azure Account**: For cloud services (you can start with a free trial)
- **Windows 10 or 11**: This guide is specifically for Windows users

### Required Files
- **RCSI Clinical Skills Handbook PDF**: The medical handbook you want to make searchable
- **Project Files**: The code files from this repository

---

## Windows Setup

### Step 1: Install Python (Programming Language)

1. **Download Python**:
   - Go to [python.org](https://www.python.org/downloads/)
   - Download Python 3.11 or newer (click the big yellow button)
   - **IMPORTANT**: During installation, check the box that says "Add Python to PATH"

2. **Verify Installation**:
   - Open Command Prompt (press Windows key, type "cmd", press Enter)
   - Type: `python --version`
   - You should see something like "Python 3.11.x"

### Step 2: Install Node.js (For the Web Interface)

1. **Download Node.js**:
   - Go to [nodejs.org](https://nodejs.org/)
   - Download the LTS version (the one on the left)
   - Run the installer with default settings

2. **Verify Installation**:
   - In Command Prompt, type: `node --version`
   - You should see a version number like "v20.x.x"

### Step 3: Install Poppler (For PDF Processing)

Poppler helps us convert PDF pages to images.

1. **Download Poppler**:
   - Go to: https://github.com/oschwartz10612/poppler-windows/releases/
   - Download the latest release (look for `Release-xx.xx.x-x.zip`)

2. **Extract and Install**:
   - Extract the ZIP file to `C:\Program Files\poppler`
   - The folder structure should be: `C:\Program Files\poppler\Library\bin\`

3. **Add to System PATH**:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find and select "Path", click "Edit"
   - Click "New" and add: `C:\Program Files\poppler\Library\bin`
   - Click "OK" on all windows

4. **Verify Installation**:
   - Close and reopen Command Prompt
   - Type: `pdftoppm -version`
   - You should see version information

### Step 4: Install Git (Version Control)

1. **Download Git**:
   - Go to [git-scm.com](https://git-scm.com/download/win)
   - Download and run the installer
   - Use default settings throughout

---

## Azure Services Setup

### Understanding Azure Services

Think of Azure as Microsoft's cloud computing platform - like renting powerful computers and services online instead of buying them. We'll use four specific services:

1. **Azure AI Document Intelligence**: Reads and understands PDF documents
2. **Azure Blob Storage**: Stores images in the cloud (like Google Drive for our app)
3. **Azure OpenAI**: Provides the AI brain that answers questions
4. **Azure AI Search**: Creates a searchable index (like Google for your handbook)

### Step 1: Create an Azure Account

1. Go to [azure.microsoft.com](https://azure.microsoft.com)
2. Click "Free account" or "Start free"
3. Follow the sign-up process (you'll need a credit card, but won't be charged for free tier usage)

### Step 2: Create a Resource Group

A resource group is like a folder that holds all your Azure services together.

1. Log in to [Azure Portal](https://portal.azure.com)
2. Click "Resource groups" in the left menu (or search for it)
3. Click "+ Create"
4. Fill in:
   - **Subscription**: Select your subscription
   - **Resource group name**: `clinical-assistant-rg`
   - **Region**: Choose one close to you (e.g., "East US")
5. Click "Review + create" then "Create"

### Step 3: Set Up Azure AI Document Intelligence

This service reads PDFs intelligently.

1. In Azure Portal, click "+ Create a resource"
2. Search for "Document Intelligence"
3. Click "Create"
4. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `clinical-assistant-rg`
   - **Region**: Same as your resource group
   - **Name**: `clinicalagentdocumentintelligence`
   - **Pricing tier**: F0 (free) or S0 (standard)
5. Click "Review + create" then "Create"
6. Once deployed, go to the resource
7. Click "Keys and Endpoint" in the left menu
8. Copy the "KEY 1" and "Endpoint" - you'll need these later

### Step 4: Set Up Azure Blob Storage

This stores all the images we extract.

1. Click "+ Create a resource"
2. Search for "Storage account"
3. Click "Create"
4. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `clinical-assistant-rg`
   - **Storage account name**: `clinicalagentstorage` (must be unique globally)
   - **Region**: Same as before
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally-redundant storage)
5. Click "Review + create" then "Create"
6. Once deployed, go to the resource
7. Click "Access keys" in the left menu
8. Copy the "Connection string" under key1

#### Create a Container for Images

1. In your storage account, click "Containers" in the left menu
2. Click "+ Container"
3. Name: `handbook-images`
4. Public access level: Private
5. Click "Create"

### Step 5: Set Up Azure OpenAI

This provides the AI capabilities.

1. **Request Access** (if needed):
   - Go to [Azure OpenAI access request](https://aka.ms/oai/access)
   - Fill out the form (approval is usually quick for legitimate use)

2. Once approved, create the service:
   - Click "+ Create a resource"
   - Search for "Azure OpenAI"
   - Click "Create"
   - Fill in:
     - **Subscription**: Your subscription
     - **Resource group**: `clinical-assistant-rg`
     - **Region**: Choose from available regions
     - **Name**: `clinicalagentopenaisrvc`
     - **Pricing tier**: S0
   - Click "Review + create" then "Create"

3. Deploy AI Models:
   - Go to your Azure OpenAI resource
   - Click "Go to Azure OpenAI Studio"
   - Click "Deployments" → "Create new deployment"
   - Deploy these models:
     - **Model 1**: `text-embedding-3-large` (Name it: `text-embedding-3-large`)
     - **Model 2**: `gpt-4o` (Name it: `gpt-4o`)

4. Get your credentials:
   - Back in Azure Portal, go to your OpenAI resource
   - Click "Keys and Endpoint"
   - Copy "KEY 1" and "Endpoint"

### Step 6: Set Up Azure AI Search

This creates the searchable index.

1. Click "+ Create a resource"
2. Search for "Azure AI Search"
3. Click "Create"
4. Fill in:
   - **Subscription**: Your subscription
   - **Resource group**: `clinical-assistant-rg`
   - **Service name**: `clinicalagnetsearchsrvc`
   - **Location**: Same region
   - **Pricing tier**: Free (F) or Basic (B)
5. Click "Review + create" then "Create"
6. Once deployed, go to the resource
7. Click "Keys" in the left menu
8. Copy the "Primary admin key"

---

## Project Installation

### Step 1: Download the Project

1. Open Command Prompt
2. Navigate to where you want to install (e.g., `cd C:\Projects`)
3. Clone the repository:
   ```bash
   git clone [repository-url]
   cd final
   ```

### Step 2: Set Up Python Environment

A virtual environment is like a separate workspace for this project's Python packages.

1. Create virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate it:
   ```bash
   venv\Scripts\activate
   ```
   You should see `(venv)` at the start of your command line

3. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Set Up the Frontend

1. Navigate to the frontend folder:
   ```bash
   cd my-medical-chatbot
   ```

2. Install JavaScript packages:
   ```bash
   npm install
   ```

3. Go back to main folder:
   ```bash
   cd ..
   ```

---

## Configuration

### Create Environment File

The `.env` file stores all your secret credentials.

1. Copy the example file:
   ```bash
   copy env.example .env
   ```

2. Open `.env` in a text editor (like Notepad)

3. Replace the placeholder values with your actual Azure credentials:

```env
# Azure AI Document Intelligence
AZURE_DOC_INTEL_ENDPOINT=your_document_intelligence_endpoint
AZURE_DOC_INTEL_KEY=your_document_intelligence_key

# Azure Blob Storage
AZURE_BLOB_CONNECTION_STRING=your_storage_connection_string

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint

# Azure AI Search
AZURE_SEARCH_ENDPOINT=your_search_endpoint
AZURE_SEARCH_KEY=your_search_admin_key
```

4. Save the file

**Important**: Never share this file or commit it to Git - it contains your secret keys!

---

## Understanding the System Components

### The Ingestion Pipeline

Think of this as preparing a cookbook for easy searching:

1. **`ingest_document.py`**: The Master Chef
   - Takes your PDF handbook
   - Reads each page carefully
   - Extracts all text and images
   - Saves everything in an organized format

2. **`upload_to_search.py`**: The Librarian
   - Takes the extracted content
   - Creates a searchable index in Azure
   - Like creating a detailed table of contents with keywords

3. **`generate_page_images.py`**: The Photographer
   - Converts each PDF page to an image
   - Uploads them to cloud storage
   - Creates references for quick access

4. **`sync_images.py`**: The Backup Manager
   - Downloads images from cloud to local storage
   - Ensures images are available offline

### The Web Application

1. **`main.py`**: The Brain
   - Receives questions from users
   - Searches for relevant information
   - Uses AI to generate accurate answers
   - Sends back answers with images

2. **Frontend (Vue.js)**: The Face
   - Provides the chat interface
   - Displays answers and images
   - Handles user interactions

---

## Running the Ingestion Pipeline

This is a one-time process to prepare your handbook.

### Step 1: Prepare Your PDF

1. Place your PDF file in the project folder
2. Rename it to something simple like `handbook.pdf`

### Step 2: Extract Content

```bash
python ingest_document.py --file handbook.pdf
```

This will:
- Read your PDF
- Extract text and images
- Create `processed_handbook.jsonl` file
- Save extracted images to `static/images/`

**What to expect**: This may take 10-30 minutes depending on PDF size

### Step 3: Generate Page Images

```bash
python generate_page_images.py handbook.pdf
```

This will:
- Convert each page to an image
- Upload to Azure Blob Storage
- Create `page_urls.json` mapping file

### Step 4: Create Search Index

First, check if an index exists:
```bash
python check_index.py
```

If it doesn't exist or you want to recreate it:
```bash
python upload_to_search.py --recreate
```

This will:
- Create a searchable index in Azure
- Upload all content with AI-generated embeddings
- Enable semantic search capabilities

### Step 5: Verify Everything

```bash
python check_embeddings.py
```

This checks that all content has proper search embeddings.

---

## Launching the Web Application

### Step 1: Start the Backend Server

1. Make sure you're in the main project folder
2. Activate virtual environment if not already active:
   ```bash
   venv\Scripts\activate
   ```
3. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start the Frontend

1. Open a **new** Command Prompt window
2. Navigate to the project:
   ```bash
   cd C:\Projects\final\my-medical-chatbot
   ```
3. Start the frontend:
   ```bash
   npm run dev
   ```

You should see:
```
VITE v5.x.x ready in xxx ms
➜  Local:   http://localhost:5173/
```

### Step 3: Use the Application

1. Open your web browser
2. Go to: http://localhost:5173/
3. Start asking questions about clinical skills!

Example questions:
- "How do I perform a cardiovascular examination?"
- "What are the steps for taking blood pressure?"
- "Show me how to examine the respiratory system"

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Python not found" Error
- **Solution**: Make sure Python is added to PATH. Reinstall Python and check the "Add to PATH" box

#### 2. "Module not found" Errors
- **Solution**: Activate virtual environment and reinstall requirements:
  ```bash
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

#### 3. PDF Processing Fails
- **Solution**: 
  - Check if PDF file exists and is not corrupted
  - Ensure Poppler is installed correctly
  - Try with a smaller PDF first

#### 4. Azure Authentication Errors
- **Solution**: 
  - Double-check all keys in `.env` file
  - Ensure no extra spaces or quotes
  - Verify services are deployed in Azure

#### 5. Images Not Showing
- **Solution**:
  - Check if images exist in `static/images/`
  - Verify Azure Blob Storage container exists
  - Run `sync_images.py` to download images

#### 6. Search Returns No Results
- **Solution**:
  - Verify index was created successfully
  - Run `check_index.py` to see index details
  - Re-run `upload_to_search.py --recreate`

### Getting Help

If you encounter issues:
1. Check the error message carefully
2. Look for similar issues in the Troubleshooting section
3. Ensure all Azure services are running
4. Verify all environment variables are set correctly

---

## Architecture Diagram

Here's how all the pieces fit together:

```
┌─────────────────┐
│   PDF Handbook  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Ingest Document │────▶│  Azure Doc      │
│     Script      │     │  Intelligence   │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Process & Store │────▶│  Azure Blob     │
│    Content      │     │   Storage       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Create Search   │────▶│  Azure AI       │
│     Index       │     │    Search       │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐              │
│   User asks     │              │
│   a question    │              │
└────────┬────────┘              │
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Web Interface  │────▶│  FastAPI        │
│   (Vue.js)      │     │   Backend       │
└─────────────────┘     └────────┬────────┘
         ▲                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │  Azure OpenAI   │
         │              │   (GPT-4o)      │
         │              └────────┬────────┘
         │                       │
         └───────────────────────┘
            Answer + Images
```

---

## Next Steps

Once everything is running:

1. **Test the System**: Ask various medical questions to ensure accuracy
2. **Monitor Usage**: Keep an eye on Azure costs (most services have free tiers)
3. **Backup Data**: Regularly backup your processed data and index
4. **Update Content**: Re-run ingestion pipeline when handbook updates
5. **Customize**: Modify the UI or add features as needed

---

## Important Security Notes

1. **Never share your `.env` file** - it contains secret keys
2. **Keep your Azure account secure** - use strong passwords and 2FA
3. **Monitor Azure usage** - to avoid unexpected charges
4. **Restrict access** - in production, limit who can access the application
5. **Regular updates** - keep all packages and services updated

---

## Conclusion

Congratulations! You've built a sophisticated AI-powered medical reference system. This system can:
- Answer questions using only verified handbook content
- Show relevant medical diagrams and images
- Provide page references for verification
- Work from any web browser

Remember, this system is designed to be a reference tool and should always be used in conjunction with professional medical judgment.

For questions or issues, refer back to this guide or consult the troubleshooting section. 