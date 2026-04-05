"""
Build / refresh local Chroma DB for fashion rules.

Uses the same embedding model as FastAPI RAG (Ollama nomic-embed-text) and the same
persist path + collection name as config / Langflow.

Embeddings use POST /api/embeddings (httpx), matching utils/outfit_chat.ollama_embed —
not LangChain's OllamaEmbeddings, which can return empty vectors with some Ollama versions.

Reads `data.txt` in the project root (same folder as this script).

Requires: Ollama running with `ollama pull nomic-embed-text`

Usage (venv active):
  python ingest.py
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import chromadb
import httpx
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE = Path(__file__).resolve().parent

PERSIST = os.getenv("CHROMA_PERSIST_DIR", r"D:\langflow_db")
COLLECTION = os.getenv("CHROMA_COLLECTION", "fashion_rules_db")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_TIMEOUT = float(os.getenv("OLLAMA_EMBED_TIMEOUT", "60"))


def ollama_embed(text: str) -> List[float]:
    """Same contract as utils/outfit_chat.ollama_embed (nomic-embed-text → 768-d)."""
    url = f"{OLLAMA_BASE.rstrip('/')}/api/embeddings"
    payload = {"model": EMBED_MODEL, "prompt": text}
    with httpx.Client(timeout=EMBED_TIMEOUT) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        emb = data.get("embedding")
        if not emb:
            raise ValueError(
                "Ollama returned no embedding. Is Ollama running and is "
                f"{EMBED_MODEL!r} pulled? Raw: {data!r}"
            )
        return emb


class OllamaHttpEmbeddings(Embeddings):
    """LangChain Embeddings backed by Ollama HTTP API (matches RAG query path)."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [ollama_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return ollama_embed(text)


def load_documents():
    data_txt = BASE / "data.txt"
    if not data_txt.exists():
        raise SystemExit(f"Missing {data_txt} — create it in the project root next to ingest.py.")
    return TextLoader(str(data_txt), encoding="utf-8").load()


def main():
    documents = load_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)

    if not docs:
        raise SystemExit("No text chunks after split — check data.txt is not empty.")

    # Full rebuild: drop collection so we never mix 384-d (old default) with 768-d (nomic).
    client = chromadb.PersistentClient(path=PERSIST)
    try:
        client.delete_collection(name=COLLECTION)
    except Exception:
        pass

    embeddings = OllamaHttpEmbeddings()

    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=PERSIST,
        collection_name=COLLECTION,
    )

    print(
        f"Done. collection={COLLECTION!r} persist={PERSIST!r} "
        f"embed_model={EMBED_MODEL!r} chunks={len(docs)}"
    )


if __name__ == "__main__":
    main()
