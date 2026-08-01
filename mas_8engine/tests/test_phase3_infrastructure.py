"""
MAS-8ENGINE │ test_phase3_infrastructure.py
Pruebas unitarias para la Fase 3 de Infraestructura:
- Persistencia Vectorial (ChromaDB)
- Persistencia de Grafos Ontológicos (RDFlib Turtle)
- Telemetría & Trazabilidad
"""
import pytest
import os
from memory.vector_store import VectorStoreEngine, DocumentChunk
from memory.graph_store import KnowledgeGraphEngine, TripleStatement
from telemetry.tracer import TelemetryTracer, MetricEvent


def test_chroma_vector_store():
    store = VectorStoreEngine()
    chunk = DocumentChunk(
        chunk_id="test_1",
        text="El motor de inferencia ontológica MAS-8ENGINE utiliza la lógica Z3 SMT.",
        metadata={"category": "test"}
    )
    added = store.add_documents([chunk])
    assert added == 1

    results = store.query_similarity("Z3 SMT solver", n_results=1)
    assert len(results) > 0
    assert results[0].chunk_id == "test_1"


def test_rdflib_graph_store():
    graph_engine = KnowledgeGraphEngine()
    triples = [
        TripleStatement(subject="MAS8Engine", predicate="usesSolver", object_value="Z3SATVerifier"),
        TripleStatement(subject="Z3SATVerifier", predicate="type", object_value="LogicEngine")
    ]
    added = graph_engine.add_triples(triples)
    assert added == 2
    assert os.path.exists(graph_engine.storage_path)


def test_telemetry_tracer():
    TelemetryTracer.events.clear()
    event = MetricEvent(
        tool_name="test_tool",
        execution_time_ms=12.5,
        status="SUCCESS"
    )
    TelemetryTracer.events.append(event)
    summary = TelemetryTracer.get_summary()
    
    assert summary["total_events"] == 1
    assert summary["avg_latency_ms"] == 12.5
    assert summary["success_rate_pct"] == 100.0
