import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

def get_document_count():
    """
    Connects to the Azure Search index and retrieves only the document count.
    """
    try:
        # --- Load Environment Variables ---
        load_dotenv()
        service_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        index_name = "clinical-skills-index"
        admin_key = os.getenv("AZURE_SEARCH_KEY")

        if not all([service_endpoint, index_name, admin_key]):
            print("❌ Error: Missing required environment variables.")
            return

        # --- Initialize Search Client ---
        credential = AzureKeyCredential(admin_key)
        search_client = SearchClient(
            endpoint=service_endpoint,
            index_name=index_name,
            credential=credential
        )

        # --- Get Document Count ---
        doc_count = search_client.get_document_count()
        print(f"Total documents in index '{index_name}': {doc_count}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    get_document_count() 