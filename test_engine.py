"""Test script para verificar el engine ontológico v2.0"""
import sys
sys.path.insert(0, '.')

def test_all():
    from ontology_engine import OntologyEnginePipeline, PipelineConfig

    config = PipelineConfig(verbose=True, use_spec_tree=True)
    pipeline = OntologyEnginePipeline(config)

    # ── TEST 1: Spec tree ─────────────────────────────────────────────────
    print("=" * 60)
    print("TEST 1: SPEC TREE")
    print("=" * 60)
    result = pipeline.get_spec_graph()
    stats = result.phase4.graph.stats()
    print(f"  Total nodes:    {stats['total_nodes']}")
    print(f"  Atomic nodes:   {stats['atomic_nodes']}")
    print(f"  Max depth:      {stats['max_depth']}")
    print(f"  Top concepts:   {stats['top_concepts']}")
    print(f"  SAT valid:      {result.validation.is_satisfiable}")
    print(f"  MECE violations:{len(result.phase4.mece_violations)}")
    assert stats['total_nodes'] > 0, "Grafo vacío"
    assert result.validation.is_satisfiable, "KB no satisfacible"
    print("  [PASS]")

    # ── TEST 2: Corpus processing ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 2: CORPUS PROCESSING")
    print("=" * 60)
    corpus = (
        "El procesamiento del lenguaje natural requiere extraccion de sintagmas "
        "nominales canonicos mediante etiquetado morfosintactico y analisis de "
        "dependencias. La lematizacion formal reduce variaciones morfologicas al "
        "lema canonico. El clustering por distancia coseno agrupa sintagmas con "
        "similitud semantica. La desambiguacion de polisemia asigna identificadores "
        "univocos IRI y UUID a cada sentido contextual detectado."
    )
    result2 = pipeline.process(corpus)
    print(f"  {result2.summary()}")
    assert result2.phase1.filtered_count >= 0, "Phase 1 failed"
    assert result2.phase4.graph.stats()['total_nodes'] > 0, "Graph empty"
    print("  [PASS]")

    # ── TEST 3: JSON-LD export ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 3: JSON-LD EXPORT")
    print("=" * 60)
    jsonld = result.jsonld_export
    print(f"  Schema ID:    {jsonld['@id']}")
    print(f"  Top concepts: {len(jsonld['skos:hasTopConcept'])}")
    print(f"  MECE OK:      {jsonld['_meta']['mece_compliant']}")
    assert jsonld['@id'] == 'urn:engine:ontologia:grafo-imperativo-v2', "Wrong ID"
    assert len(jsonld['skos:hasTopConcept']) == 4, f"Expected 4 top concepts, got {len(jsonld['skos:hasTopConcept'])}"
    print("  [PASS]")

    # ── TEST 4: Árbol ASCII ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 4: TREE RENDER")
    print("=" * 60)
    tree = result.tree_render
    assert "├──" in tree or "└──" in tree, "No tree characters"
    print(tree[:1200])
    print("  [PASS]")

    # ── TEST 5: Exportación multi-formato ────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 5: MULTI-FORMAT EXPORT")
    print("=" * 60)
    tree_out = pipeline.export_format(result, 'tree')
    json_out = pipeline.export_format(result, 'jsonld')
    flat_out = pipeline.export_format(result, 'flat')
    assert len(tree_out) > 0, "Empty tree output"
    assert len(json_out) > 0, "Empty JSON-LD output"
    assert len(flat_out) > 0, "Empty flat output"
    print(f"  Tree:   {len(tree_out)} chars")
    print(f"  JSON-LD:{len(json_out)} chars")
    print(f"  Flat:   {len(flat_out)} chars")
    print("  [PASS]")

    # ── TEST 6: SAT/CDCL validation ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 6: SAT/CDCL VALIDATION")
    print("=" * 60)
    import json
    val_result = pipeline.validate_only(jsonld)
    print(f"  Satisfiable: {val_result['is_satisfiable']}")
    print(f"  KB consistent: {val_result['kb_consistent']}")
    print(f"  CNF clauses: {val_result['cnf_clauses']}")
    print(f"  Orphans purged: {val_result['orphans_purged']}")
    assert val_result['is_satisfiable'], "JSON-LD not satisfiable"
    print("  [PASS]")

    # ── TEST 7: Importar JSON-LD ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 7: JSON-LD ROUND-TRIP (export → import)")
    print("=" * 60)
    json_str = pipeline.export_format(result, 'jsonld')
    reconstructed = pipeline.exporter.from_jsonld(json_str)
    recon_stats = reconstructed.stats()
    print(f"  Reconstructed nodes: {recon_stats['total_nodes']}")
    assert recon_stats['top_concepts'] == stats['top_concepts'], "Round-trip failed"
    print("  [PASS]")

    print("\n" + "=" * 60)
    print("  ✓ ALL 7 TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
