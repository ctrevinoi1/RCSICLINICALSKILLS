import os
import json
import sys
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticSearch,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
)

def main():
    load_dotenv()

    # ---------- CONFIG ----------
    FORCE_RECREATE_INDEX = True
    SERVICE = os.getenv("AZURE_SEARCH_ENDPOINT")
    ADMIN_KEY = os.getenv("AZURE_SEARCH_KEY")
    INDEX = "clinical-skills-index"
    DATAFILE = "processed_handbook.jsonl"

    # ---------- INDEX SCHEMA ----------
    def build_index() -> SearchIndex:
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
            SearchField(name="source_page", type=SearchFieldDataType.Int32, filterable=True, sortable=True, facetable=True),
            SearchField(name="content_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(name="image_reference", type=SearchFieldDataType.String),
            SearchField(name="image_summary", type=SearchFieldDataType.String, searchable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="vec-prof"
            ),
            SearchField(
                name="image_summary_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="vec-prof"
            ),
        ]

        vector_cfg = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-cfg")],
            profiles=[VectorSearchProfile(name="vec-prof", algorithm_configuration_name="hnsw-cfg")]
        )

        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                content_fields=[SemanticField(field_name="content")],
                keywords_fields=[SemanticField(field_name="image_summary")],
            )
        )
        semantic_search = SemanticSearch(configurations=[semantic_config])

        return SearchIndex(name=INDEX, fields=fields, vector_search=vector_cfg, semantic_search=semantic_search)

    # ---------- VALIDATE / (RE)CREATE INDEX ----------
    cred = AzureKeyCredential(ADMIN_KEY)
    idx_client = SearchIndexClient(endpoint=SERVICE, credential=cred)

    try:
        existing = idx_client.get_index(INDEX)
        existing_fields = {f.name for f in existing.fields}
        required = {f.name for f in build_index().fields}
        missing = required - existing_fields
        if missing:
            if FORCE_RECREATE_INDEX:
                print(f"Index '{INDEX}' is missing fields {missing}. Deleting & recreating…")
                idx_client.delete_index(INDEX)
                idx_client.create_index(build_index())
                print("Index recreated ✅")
            else:
                print(f"ERROR: Index exists but is missing fields: {missing}")
                sys.exit(1)
        else:
            print(f"Index '{INDEX}' already exists and is valid ✅")
    except Exception:
        print(f"Creating index '{INDEX}'…")
        idx_client.create_index(build_index())
        print("Index created ✅\n")

    # ---------- LOAD DOCUMENTS ----------
    docs = []
    with open(DATAFILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                doc = json.loads(line)
                # Remove null or empty image_summary_vector to avoid indexing errors
                if doc.get("image_summary_vector") is None:
                    doc.pop("image_summary_vector", None)
                docs.append(doc)
            except json.JSONDecodeError:
                print("⚠️  Skipping a corrupt line in data file")

    if not docs:
        print("No documents to upload – exiting.")
        sys.exit(0)

    # ---------- UPLOAD ----------
    search_client = SearchClient(SERVICE, INDEX, cred)
    batch_size = 1000
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        print(f"Uploading batch {i // batch_size + 1} ({len(batch)} docs)...")
        search_client.upload_documents(batch)
    print("✅  All documents uploaded")


if __name__ == "__main__":
    main()