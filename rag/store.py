"""
RAG layer — seeds ChromaDB from markdown documents and exposes a retrieval function.

Design decisions:
- ChromaDB (local, no server) keeps the system fully self-contained for the demo.
- Embedding model: text-embedding-3-small (1536 dims, cheap, good quality).
- Two collections: 'style_guides' and 'remotion_api' — queried separately by agents that need them.
- Chunking: whole documents per file (≤ 400 tokens each), so retrieved context is always coherent.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Literal

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
DOCS_DIR = Path(__file__).parent / "documents"

Collection = Literal["style_guides", "remotion_api"]


def _embedding_fn() -> OpenAIEmbeddingFunction:
    return OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-small",
    )


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=CHROMA_DIR)


def seed_vector_store(force: bool = False) -> None:
    """Idempotently seed ChromaDB from the documents directory.

    Args:
        force: If True, drops and recreates collections even if they already exist.
    """
    client = _client()
    ef = _embedding_fn()

    for collection_name in ("style_guides", "remotion_api"):
        sub_dir = DOCS_DIR / collection_name

        if not sub_dir.exists():
            print(f"[RAG] Skipping {collection_name} — directory not found")
            continue

        # Collect markdown files
        docs = list(sub_dir.glob("*.md"))
        if not docs:
            print(f"[RAG] No documents found in {sub_dir}")
            continue

        if force:
            try:
                client.delete_collection(collection_name)
            except Exception:
                pass

        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

        # Check which docs are already indexed (avoid redundant re-embedding)
        existing_ids = set(collection.get()["ids"])
        new_docs = [d for d in docs if d.stem not in existing_ids]

        if not new_docs:
            print(f"[RAG] {collection_name}: already up-to-date ({len(docs)} docs)")
            continue

        texts = [d.read_text(encoding="utf-8") for d in new_docs]
        ids = [d.stem for d in new_docs]
        metadatas = [{"source": d.name, "collection": collection_name} for d in new_docs]

        collection.add(documents=texts, ids=ids, metadatas=metadatas)
        print(f"[RAG] {collection_name}: indexed {len(new_docs)} documents → {ids}")


def retrieve(query: str, collection: Collection, n_results: int = 2) -> List[str]:
    """Retrieve the top-k most relevant document chunks for a query.

    Returns a list of document text strings (already decoded), ready to be
    injected into an LLM prompt as context.
    """
    client = _client()
    ef = _embedding_fn()

    try:
        col = client.get_collection(name=collection, embedding_function=ef)
    except Exception:
        # Collection not yet seeded — return empty (agents gracefully handle this)
        return []

    results = col.query(query_texts=[query], n_results=min(n_results, col.count()))
    documents: List[List[str]] = results.get("documents", [[]])
    return documents[0] if documents else []
