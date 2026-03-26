from typing import List, Dict
import json
from langchain_openai import OpenAIEmbeddings

# CONFIG
BATCH_SIZE = 20
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Initialize once (important)
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"  # cost-effective
)


def create_embeddings(chunks: List[str], message) -> List[Dict]:
    """
    Generate embeddings for text chunks (production-grade)
    """

    results = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        vectors = embedding_model.embed_documents(batch)

        for j, vector in enumerate(vectors):
            results.append({
                "document_id":message['id'],
                "chunk_text": batch[j],
                "chunk_embedding": vector,
                "chunk_order": i + j,
                "chunk_metadata": json.dumps({  "file_name": message['file'], "file_type": message['file_type'] }),
                "token_count": len(batch[j].split())
            })

    return results