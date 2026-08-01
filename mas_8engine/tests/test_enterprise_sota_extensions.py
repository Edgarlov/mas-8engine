"""
MAS-8ENGINE │ test_enterprise_sota_extensions.py
Pruebas unitarias para las 4 extensiones de vanguardia:
- Compilación JIT C++ (Sub-milisegundo)
- Caché Semántica Vectorial LRU In-Memory
- Hardening RAM Criterios Comunes CC EAL4+
"""
import pytest
from engines.cpp_jit_dispatcher import CppJitDispatcher
from memory.inmemory_semantic_cache import InMemorySemanticCache
from engines.memory_enclave_guard import MemoryEnclaveGuard


def test_cpp_jit_dispatcher_sub_millisecond():
    vector_in = [1.0, 2.0, 3.0, 4.0, 5.0]
    res = CppJitDispatcher.dispatch_fast_node(vector_in)
    
    assert res.input_vector_size == 5
    assert res.execution_time_us < 1000.0  # Menos de 1 ms (sub-milisegundo)
    assert res.status == "JIT_CPP_SUB_MILLISECOND_SUCCESS"


def test_inmemory_semantic_cache():
    cache = InMemorySemanticCache(capacity=10)
    query = "Diseño de red ontológica ISO-704"
    response = "Resultado pre-calculado en Z3"
    
    # 1. Miss inicial
    res_miss = cache.get(query)
    assert res_miss.hit is False
    
    # 2. Put & Hit
    cache.put(query, response)
    res_hit = cache.get(query)
    assert res_hit.hit is True
    assert res_hit.cached_response == response
    assert res_hit.latency_ms < 1.0  # Latencia ultra-baja en memoria


def test_memory_enclave_guard_cc_eal4():
    data = "CONFIDENTIAL_STATE_VECTOR"
    sealed = MemoryEnclaveGuard.seal_memory_buffer(data, "ENCLAVE-SECURE-01")
    
    assert sealed.is_sealed is True
    assert sealed.compliance_level == "CC_EAL4_PLUS_COMPLIANT"
    assert len(sealed.sealed_payload_base64) > 0
