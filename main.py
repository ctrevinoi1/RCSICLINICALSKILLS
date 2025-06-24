import os
import base64
import httpx
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# --- Configuration ---
load_dotenv()

# Azure AI Search
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
search_index_name = "clinical-skills-index"

# Azure Blob Storage
connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
storage_account_name = blob_service_client.account_name

# Azure OpenAI
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
openai_embedding_model = "text-embedding-3-large"
openai_generation_model = "gpt-4o"

# Load page URLs mapping
PAGE_URLS = {}
try:
    with open("page_urls.json", "r") as f:
        PAGE_URLS = json.load(f)
    print(f"Loaded {len(PAGE_URLS)} page URLs")
except Exception as e:
    print(f"Warning: Could not load page_urls.json: {e}")

# --- FastAPI App Setup ---
app = FastAPI()

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    chat_history: list = []

# --- Helper Functions ---
def generate_sas_url(blob_url: str) -> str:
    """Generates a SAS URL for a given Azure Blob Storage URL."""
    try:
        parsed_url = urlparse(blob_url)
        # Assumes blob_url is in the format: https://<account_name>.blob.core.windows.net/<container_name>/<blob_name>
        container_name = parsed_url.path.split('/')[1]
        blob_name = '/'.join(parsed_url.path.split('/')[2:])

        sas_token = generate_blob_sas(
            account_name=storage_account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        return f"{blob_url}?{sas_token}"
    except Exception as e:
        print(f"Error generating SAS URL for {blob_url}: {e}")
        return blob_url # Fallback to original URL on error

def create_text_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model=openai_embedding_model,
        dimensions=1536  # Ensure embeddings match index dimensions
    )
    return response.data[0].embedding

async def get_image_as_base64(url):
    """Fetches an image from a URL and returns it as a Base64 string."""
    # This function now expects a fully qualified URL (including SAS token if needed)
    if not url.startswith("http"):
        print(f"Warning: get_image_as_base64 received a non-URL: {url}")
        # Return a placeholder or raise an error, as local paths are no longer supported
        raise HTTPException(status_code=400, detail="Invalid image URL format")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return base64.b64encode(response.content).decode('utf-8')
        except httpx.HTTPStatusError as e:
            print(f"Error fetching image {url}: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch image from URL: {url}")

# --- API Endpoint ---
@app.post("/api/query")
async def process_query(request: QueryRequest):
    # 1. Perform Hybrid Search on Azure AI Search
    search_client = SearchClient(search_endpoint, search_index_name, AzureKeyCredential(search_key))
    
    query_vector = create_text_embedding(request.query)
    
    vector_query = VectorizedQuery(
        vector=query_vector, 
        k_nearest_neighbors=5, 
        fields="content_vector, image_summary_vector"
    )

    results = search_client.search(
        search_text=request.query,
        vector_queries=[vector_query],
        select=["id", "content", "image_summary", "source_page", "content_type", "image_reference"],
        top=5,
        semantic_configuration_name='my-semantic-config',  # Use Semantic Ranker
        query_type='semantic',  # Explicitly set the query type
        query_caption="extractive",
        query_answer="extractive",
    )

    # 2. Construct the Prompt Context
    retrieved_context = []
    citations = []
    unique_image_refs = set()
    relevant_pages = set()  # Track which pages are relevant

    for result in results:
        # Track relevant pages
        source_page = result['source_page']
        relevant_pages.add(source_page)
        
        # Combine text and image summaries for context
        context_text = f"Source (Page {source_page}): {result['content']}"
        if result['image_summary']:
            context_text += f"\nAssociated Visual Description: {result['image_summary']}"
        retrieved_context.append(context_text)

        # Collect unique image references for display
        if result['image_reference']:
            # Generate a SAS URL for the private blob
            sas_image_url = generate_sas_url(result['image_reference'])
            citations.append({
                "chunk_id": result['id'],
                "source_page": source_page,
                "content_type": result['content_type'],
                "image_url": sas_image_url,
                "extracted_visual": True  # Mark as extracted visual
            })
            unique_image_refs.add(result['image_reference'])

    # Add full page images for all relevant pages
    for page_num in sorted(relevant_pages):
        page_url = PAGE_URLS.get(str(page_num))
        if page_url:
            # Generate a SAS URL for the private blob
            sas_page_url = generate_sas_url(page_url)
            citations.append({
                "chunk_id": f"full_page_{page_num}",
                "source_page": page_num,
                "content_type": "full_page",
                "image_url": sas_page_url,
                "caption": f"Full Page {page_num}",
                "extracted_visual": False  # Mark as full page
            })

    context_str = "\n---\n".join(retrieved_context)

    # 3. Build the Multimodal Prompt for GPT-4o
    system_message = """
    ### Your Role and Goal
    You are a specialized AI assistant for medical professionals. Your single purpose is to provide accurate, verifiable answers derived exclusively from the provided excerpts of the RCSI Handbook of Clinical Skills.

    ### Core Directives
    - **Strictly Grounded:** Your knowledge is strictly limited to the provided text, tables, and image descriptions. DO NOT use any external knowledge or pre-existing training data.
    - **No Inference or Invention:** Never invent, infer, or assume information that is not explicitly stated in the provided context. This includes things like drug dosages, procedural steps, or diagnoses if they are not mentioned.
    - **Verbatim Rule:** If the provided context does not contain the information to answer the user's question, you MUST follow the "Safety Guardrail" instruction below.

    ### Rules for Formulating Your Answer
    - **Be Concise:** Provide clear and direct answers. Use professional language suitable for a clinical setting.
    - **Refer to Visuals:** When your answer is based on a diagram, table, or image, you MUST refer to it directly in your response. For example, "As shown in the diagram on page 40..." or "The table on page 83 lists the following systolic murmurs:".
    - **Cite Your Sources:** At the very end of your response, you MUST include a "Sources:" section. List the specific page numbers from which you derived your information.
        - Example Format:
          Sources: Page 53, Page 84

    ### Safety Guardrail
    - If the answer cannot be found in the provided context, abandon all other instructions and respond with this *exact* phrase and nothing more:
    `I could not find relevant information on this topic in the clinical skills handbook.`
    """

    prompt_messages = [{"role": "system", "content": system_message}]
    # Add chat history for conversational context
    prompt_messages.extend(request.chat_history)
    
    # Add current query and context
    user_prompt_content = [
        {
            "type": "text",
            "text": f"Context from handbook:\n{context_str}\n\nQuestion: {request.query}"
        }
    ]
    
    # Only add extracted visuals to the prompt (not full pages)
    for citation in citations:
        if citation.get('extracted_visual', False):
            try:
                base64_image = await get_image_as_base64(citation['image_url'])
                user_prompt_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                })
            except Exception as e:
                print(f"Could not fetch image for prompt: {e}")
            
    prompt_messages.append({"role": "user", "content": user_prompt_content})

    # 4. Call Azure OpenAI to Generate the Response
    response = openai_client.chat.completions.create(
        model=openai_generation_model,
        messages=prompt_messages,
        max_tokens=2048,
        temperature=0.4
    )

    final_response = response.choices[0].message.content

    # 5. Package the final payload for the frontend
    return {
        "text_response": final_response,
        "citations": citations
    } 