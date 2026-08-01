"""
MAS-8ENGINE │ vector_store.py
Capa de Persistencia Vectorial usando ChromaDB y Ollama Embeddings.
Proporciona memoria semántica persistente a largo plazo.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import chromadb
from chromadb.config import Settings


class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    distance: Optional[float] = None


class VectorStoreEngine:
    """Motor de Almacenamiento Vectorial Persistente con ChromaDB."""

    def __init__(self, persist_directory: str = r"C:\Users\edgar\Desktop\agentes\mas_8engine\chroma_db"):
        self.persist_dir = persist_directory
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="mas8_semantic_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[DocumentChunk]) -> int:
        if not documents:
            return 0
            
        ids = [doc.chunk_id for doc in documents]
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        return len(documents)

    def query_similarity(
        self,
        query_text: str,
        n_results: int = 3,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        kwargs = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)
        
        chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            ids = results["ids"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)
            
            for doc_id, text, meta, dist in zip(ids, docs, metas, distances):
                chunks.append(DocumentChunk(
                    chunk_id=doc_id,
                    text=text,
                    metadata=meta,
                    distance=round(dist, 4)
                ))
        return chunks
