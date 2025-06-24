import json
import os

# Check if the data file exists
if not os.path.exists("processed_handbook.jsonl"):
    print("No processed_handbook.jsonl file found")
    exit()

# Analyze the embeddings
total_docs = 0
dimension_stats = {
    "content_vector": {},
    "image_summary_vector": {}
}
docs_with_issues = []

with open("processed_handbook.jsonl", "r") as f:
    for line_num, line in enumerate(f, 1):
        try:
            doc = json.loads(line)
            total_docs += 1
            
            # Check content_vector dimensions
            if doc.get("content_vector"):
                dim = len(doc["content_vector"])
                dimension_stats["content_vector"][dim] = dimension_stats["content_vector"].get(dim, 0) + 1
                if dim != 1536:
                    docs_with_issues.append((doc["id"], "content_vector", dim))
            
            # Check image_summary_vector dimensions
            if doc.get("image_summary_vector"):
                dim = len(doc["image_summary_vector"])
                dimension_stats["image_summary_vector"][dim] = dimension_stats["image_summary_vector"].get(dim, 0) + 1
                if dim != 1536:
                    docs_with_issues.append((doc["id"], "image_summary_vector", dim))
                    
        except json.JSONDecodeError:
            print(f"Error parsing line {line_num}")

print(f"\nTotal documents: {total_docs}")
print("\nEmbedding dimension statistics:")
print("\ncontent_vector dimensions:")
for dim, count in sorted(dimension_stats["content_vector"].items()):
    print(f"  {dim} dimensions: {count} documents")

print("\nimage_summary_vector dimensions:")
for dim, count in sorted(dimension_stats["image_summary_vector"].items()):
    print(f"  {dim} dimensions: {count} documents")

if docs_with_issues:
    print(f"\n⚠️  Found {len(docs_with_issues)} documents with incorrect dimensions (expected 1536):")
    for doc_id, field, dim in docs_with_issues[:10]:  # Show first 10
        print(f"  - {doc_id}: {field} has {dim} dimensions")
    if len(docs_with_issues) > 10:
        print(f"  ... and {len(docs_with_issues) - 10} more")
    
    print("\n⚠️  RECOMMENDATION:")
    print("  1. Delete processed_handbook.jsonl")
    print("  2. Re-run: python ingest_document.py")
    print("  3. Then run: python upload_to_search.py")
else:
    print("\n✅ All embeddings have the correct dimensions (1536)") 