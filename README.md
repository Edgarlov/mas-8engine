# Ontology Engine v2.0

**Motor de Ingeniería Ontológica y Minería Léxica de Resolución Atómica**

Implementación completa de la especificación `ESPECIFICACION_INGENIERIA_ONTOLOGICA.md v2.0`.

---

## Arquitectura del Pipeline

```
corpus → [P1: Filtrado Morfosintáctico]
           → [P2: BFS Clustering Coseno]
             → [P3: Canonicalización + WSD + IRI]
               → [P4: Grafo Imperativo MECE]
                 → [SAT/CDCL Validation]
                   → [JSON-LD SKOS Export]
```

| Fase | Módulo | Formalismo |
|------|--------|------------|
| P1 Filtrado | `phase1_filter.py` | SNC ⊑ Sustantivo ⊓ ∃tieneAdjetivo.Especificador |
| P2 Clustering | `phase2_clustering.py` | Sim(v1,v2) = (v1·v2)/(‖v1‖·‖v2‖) ≥ τ |
| P3 Canónica | `phase3_canonical.py` | f(W_var) → L_canon + ∀x∃!u (IRI(u) ∧ UUID(x,u)) |
| P4 Imperativa | `phase4_graph.py` | g(NP) → VP_imp: [Verbo]+[Objeto]+[Estándar] |
| Validación | `sat_validator.py` | SAT(KB)=True, AGM Belief Revision |
| Exportación | `exporter.py` | W3C JSON-LD 1.1 + SKOS Core |

---

## Instalación Rápida

```bash
pip install -r requirements.txt

# Opcional: NLP avanzado
pip install spacy && python -m spacy download es_core_news_sm

# Opcional: embeddings densos
pip install sentence-transformers

# Opcional: RDF export
pip install rdflib
```

---

## Uso

### Modo Interactivo (REPL)
```bash
python run.py
```

### Procesar Corpus
```bash
python run.py --corpus "Procesamiento del lenguaje natural y minería léxica ontológica"
python run.py --corpus-file mi_documento.txt
python run.py --demo
```

### Árbol Imperativo del Spec
```bash
python run.py --tree
```

### Exportación
```bash
python run.py --export jsonld --output schemas/mi_grafo.json
python run.py --export tree
python run.py --export turtle   # requiere rdflib
python run.py --export flat
```

### Validación SAT/CDCL
```bash
python run.py --validate schemas/ontologia_v2_full.json
```

### Interfaz Web
```bash
python run.py --serve --port 8080
# Abrir: http://localhost:8080
```

---

## Estructura del Proyecto

```
agentes/
├── ontology_engine/           # Engine Python (4 fases + validador + exporter)
│   ├── __init__.py
│   ├── models.py              # Dataclasses: Node, Graph, CanonicalForm...
│   ├── phase1_filter.py       # Filtrado morfosintáctico (SNC)
│   ├── phase2_clustering.py   # BFS + similitud coseno
│   ├── phase3_canonical.py    # Lematización + WSD + IRI/UUID
│   ├── phase4_graph.py        # MECE + renderizado imperativo
│   ├── sat_validator.py       # SAT/CDCL + AGM belief revision
│   ├── exporter.py            # JSON-LD SKOS
│   └── pipeline.py            # Orquestador
├── agent/
│   ├── ontology_agent.py      # CLI interactivo + servidor web
│   └── web_interface/         # Frontend HTML/CSS/JS premium
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── schemas/
│   └── ontologia_v2_full.json # JSON-LD completo (todos los nodos atómicos)
├── audit/
│   └── mece_audit.md          # Auditoría MECE completa
├── requirements.txt
├── run.py                     # Entry point
└── ESPECIFICACION_INGENIERIA_ONTOLOGICA.md
```

---

## API Python

```python
from ontology_engine import OntologyEnginePipeline, PipelineConfig

config = PipelineConfig(
    tau=0.25,          # Umbral similitud coseno
    max_depth=5,       # k-máximo (Level-k Maximum)
    use_spec_tree=True # Usar árbol del spec como base
)

pipeline = OntologyEnginePipeline(config)

# Procesar corpus arbitrario
result = pipeline.process("Tu corpus técnico aquí...")

# Resultados disponibles
print(result.tree_render)           # Árbol ASCII
print(result.validation.is_satisfiable)  # SAT/CDCL
print(result.phase4.mece_violations)     # Violaciones MECE

# Exportar
json_str = pipeline.export_format(result, "jsonld")
turtle_str = pipeline.export_format(result, "turtle")

# Obtener grafo del spec sin corpus adicional
spec_result = pipeline.get_spec_graph()
```

---

## Opciones CLI

```
python run.py [OPTIONS]

  --corpus, -c TEXT      Corpus de texto a procesar
  --corpus-file, -f FILE Archivo con el corpus
  --demo                 Corpus de demostración
  --tree                 Árbol del spec
  --export FORMAT        jsonld|turtle|tree|flat
  --output, -o FILE      Archivo de salida
  --validate FILE        Validar JSON-LD con SAT/CDCL
  --serve                Servidor web
  --port INT             Puerto (default: 8080)
  --tau FLOAT            Umbral coseno τ (default: 0.25)
  --max-depth INT        Profundidad máxima k (default: 5)
  --no-spec-tree         Construir árbol desde corpus
  --verbose, -v          Salida detallada por fase
  --format FORMAT        tree|jsonld|summary (default: tree)
```

---

## Especificación Formal

Basado en: **ESPECIFICACION_INGENIERIA_ONTOLOGICA.md v2.0**

Formalismos implementados:
- **MECE**: Ci ⊓ Cj ⊑ ⊥ ∀i≠j + ∪Ci = Parent
- **Similitud Coseno**: Sim(v1,v2) = (v1·v2)/(‖v1‖·‖v2‖) ≥ τ
- **Canonicalización**: f(W_var) → L_canon
- **IRI/UUID**: ∀x∃!u (Entidad(x) → IRI(u) ∧ hasUUID(x,u))
- **SAT/CDCL**: SAT(KB) = True (sin cláusulas vacías ⊥)
- **AGM**: W÷φ = min(W, ¬φ) por selección epistémica
- **Transmutación**: g(NP) → VP_imp = [Verbo_Imp]+[Obj_Téc]+[Estándar_ISO]

---

## Versión

Engine: `2.0.0` | Spec: `ESPECIFICACION_INGENIERIA_ONTOLOGICA.md v2.0`
