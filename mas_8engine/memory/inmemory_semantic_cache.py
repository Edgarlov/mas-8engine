"""
MAS-8ENGINE │ inmemory_semantic_cache.py
Filtro de Caché Semántica Vectorial In-Memory LRU previo a ChromaDB para consultas repetitivas de ultraloma latencia.
"""
from __future__ import annotations

import hashlib
import time
from typing import Dict, Optional, Any
from collections import OrderedDict
from pydantic import BaseModel


class CachedVectorQueryResult(BaseModel):
    query_hash: str
    cached_response: str
    latency_ms: float
    hit: bool


class InMemorySemanticCache:
    """Caché Vectorial LRU In-Memory para consultas semánticas."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, str] = OrderedDict()

    def get(self, query: str) -> CachedVectorQueryResult:
        start_t = time.perf_counter()
        q_hash = hashlib.sha256(query.strip().lower().encode('utf-8')).hexdigest()
        
        if q_hash in self.cache:
            self.cache.move_to_end(q_hash)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return CachedVectorQueryResult(
                query_hash=q_hash,
                cached_response=self.cache[q_hash],
                latency_ms=round(elapsed_ms, 3),
                hit=True
            )
            
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return CachedVectorQueryResult(
            query_hash=q_hash,
            cached_response="",
            latency_ms=round(elapsed_ms, 3),
            hit=False
        )

    def put(self, query: str, response: str) -> None:
        q_hash = hashlib.sha256(query.strip().lower().encode('utf-8')).hexdigest()
        if q_hash in self.cache:
            self.cache.move_to_end(q_hash)
        self.cache[q_hash] = response
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
