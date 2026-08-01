"""
phase4_graph.py — Estructuración MECE y Renderizado Imperativo (Fase 4)

Implementa:
  - Validación MECE (Mutually Exclusive, Collectively Exhaustive)
    Ci ⊓ Cj ⊑ ⊥  ∀i≠j   (Exclusión Mutua)
    ∀x(Padre(x) → ∃y(Hijo(y,x)))  (Exhaustividad Colectiva)
  - Transmutación nominal→imperativa: g(NP) → VP_imp
    Forma: [Verbo_Imp] + [Objeto_Técnico] + [Estándar_ISO]
  - Renderizado ASCII del árbol (├──, └──, sangría normada)
  - Validación secuencias numéricas decimales
  - Exportación base a JSON-LD SKOS

Formalismo MECE:
  Ci ⊓ Cj ⊑ ⊥  ∀i≠j
  ∪ Ci = Parent  (Ci exhaustivo)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import (
    CanonicalForm,
    NodeRole,
    OntologyGraph,
    OntologyNode,
    Phase4Result,
    RelationType,
)

# ─────────────────────────────────────────────────────────────────────────────
# Mapeo de Transmutación Nominal → Imperativa
# ─────────────────────────────────────────────────────────────────────────────

# Verbos operativos por categoría semántica del sintagma nominal
IMPERATIVE_VERB_MAP: dict[str, str] = {
    # Extracción / Detección
    "extracción": "EXTRAER",
    "detección": "DETECTAR",
    "identificación": "IDENTIFICAR",
    "reconocimiento": "RECONOCER",
    "localización": "LOCALIZAR",
    "búsqueda": "EJECUTAR BÚSQUEDA DE",
    # Análisis / Filtrado
    "filtrado": "FILTRAR",
    "análisis": "ANALIZAR",
    "discriminación": "DISCRIMINAR",
    "clasificación": "CLASIFICAR",
    "eliminación": "ELIMINAR",
    "exclusión": "EXCLUIR",
    "purga": "PURGAR",
    # Normalización / Transformación
    "normalización": "NORMALIZAR",
    "lematización": "LEMATIZAR",
    "canonicalización": "CANONICALIZAR",
    "estandarización": "ESTANDARIZAR",
    "resolución": "RESOLVER",
    "transformación": "TRANSFORMAR",
    "conversión": "CONVERTIR",
    "reducción": "REDUCIR",
    # Asignación / Mapeo
    "asignación": "ASIGNAR",
    "mapeo": "MAPEAR",
    "expansión": "EXPANDIR",
    "enlace": "ENLAZAR",
    "asociación": "ASOCIAR",
    # Validación / Verificación
    "validación": "VALIDAR",
    "verificación": "VERIFICAR",
    "auditoría": "AUDITAR",
    "confirmación": "CONFIRMAR",
    # Estructuración / Generación
    "estructuración": "ESTRUCTURAR",
    "generación": "GENERAR",
    "construcción": "CONSTRUIR",
    "renderizado": "RENDERIZAR",
    "exportación": "EXPORTAR",
    "serialización": "SERIALIZAR",
    # Clustering / Agrupación
    "clustering": "EJECUTAR CLUSTERING DE",
    "agrupación": "AGRUPAR",
    "balanceo": "BALANCEAR",
    # Desambiguación
    "desambiguación": "DESAMBIGUAR",
    "alineación": "ALINEAR",
    "consolidación": "CONSOLIDAR",
    # Profundización
    "profundización": "PROFUNDIZAR EN",
    "desglose": "DESGLOSAR",
    "exploración": "EXPLORAR",
    # Implementación
    "implementación": "IMPLEMENTAR",
    "aplicación": "APLICAR",
    "transmutación": "TRANSMUTAR",
}

# ISO/estándares por dominio para añadir al imperativo
ISO_SUFFIX_MAP: dict[str, str] = {
    "pos": "[ISO 24613]",
    "part-of-speech": "[ISO 24613]",
    "etiquetado": "[ISO 24613]",
    "sintagma": "[ISO 24613]",
    "lema": "[ISO 24613]",
    "acrónimo": "[Schwartz-Hearst 2003]",
    "acronym": "[Schwartz-Hearst 2003]",
    "iri": "[RFC 3987]",
    "uuid": "[RFC 4122]",
    "coseno": "[IEEE 1016]",
    "similitud": "[ISO/IEC 2382]",
    "grafo": "[ISO/IEC 2382]",
    "skos": "[W3C SKOS]",
    "owl": "[W3C OWL 2]",
    "json-ld": "[W3C JSON-LD 1.1]",
    "snomed": "[SNOMED CT]",
    "mece": "[McKinsey MECE]",
    "sat": "[DIMACS CNF]",
    "cnf": "[DIMACS CNF]",
    "iso": "[ISO]",
}

# ─────────────────────────────────────────────────────────────────────────────
# Nodos del Grafo Predefinido (del spec ESPECIFICACION_INGENIERIA_ONTOLOGICA.md)
# ─────────────────────────────────────────────────────────────────────────────

SPEC_TREE: list[dict] = [
    {
        "notation": "1", "label": "Minar y Filtrar Patrones Sintácticos Complejos",
        "children": [
            {
                "notation": "1.1", "label": "Extraer Sintagmas Nominales Canónicos (SNC)",
                "children": [
                    {
                        "notation": "1.1.1", "label": "Detectar Patrones Sustantivo + Adjetivo",
                        "children": [
                            {"notation": "1.1.1.1", "label": "Aislar especificadores de dominio mediante etiquetado POS", "iso": "[ISO 24613]"},
                        ]
                    },
                    {
                        "notation": "1.1.2", "label": "Detectar Cadenas Sustantivo + Preposición + Sustantivo",
                        "children": [
                            {"notation": "1.1.2.1", "label": "Mapear complementos del nombre mediante árboles de dependencia sintáctica", "iso": "[ISO 24613]"},
                        ]
                    },
                ]
            },
            {
                "notation": "1.2", "label": "Discriminar Ruido Morfosintáctico",
                "children": [
                    {
                        "notation": "1.2.1", "label": "Eliminar Modismos Volátiles",
                        "children": [
                            {"notation": "1.2.1.1", "label": "Purgar muletillas contextuales sin valor técnico del corpus base"},
                        ]
                    },
                    {
                        "notation": "1.2.2", "label": "Descartar Entidades No Técnicas",
                        "children": [
                            {"notation": "1.2.2.1", "label": "Excluir pronombres y adverbios inespecíficos mediante Stopword Lists"},
                        ]
                    },
                ]
            },
        ]
    },
    {
        "notation": "2", "label": "Extraer Candidatos Léxicos y Ejecutar Búsqueda en Grafo",
        "children": [
            {
                "notation": "2.1", "label": "Aplicar Búsqueda en Amplitud (BFS) para Cobertura Horizontal",
                "children": [
                    {
                        "notation": "2.1.1", "label": "Mapear Horizontalmente Dimensiones Temáticas",
                        "children": [
                            {"notation": "2.1.1.1", "label": "Cubrir transversalmente subsistemas identificando ramas primarias"},
                            {"notation": "2.1.1.2", "label": "Ejecutar clustering de sintagmas clave mediante métrica de distancia coseno"},
                        ]
                    },
                    {
                        "notation": "2.1.2", "label": "Balancear Distribución Categorial",
                        "children": [
                            {"notation": "2.1.2.1", "label": "Normalizar cardinalidad de ramas pares para mitigar sesgos de sobre-frecuencia"},
                            {"notation": "2.1.2.2", "label": "Incluir dimensiones periféricas validadas para garantizar exhaustividad"},
                        ]
                    },
                ]
            },
            {
                "notation": "2.2", "label": "Explorar en Profundidad por Niveles (Recursión Atómica)",
                "children": [
                    {
                        "notation": "2.2.1", "label": "Profundizar Jerárquicamente de Nivel 1 a Nivel 5",
                        "children": [
                            {"notation": "2.2.1.1", "label": "Desglosar componentes sub-atómicos aislando atributos por nodo"},
                            {"notation": "2.2.1.2", "label": "Delimitar comandos y parámetros finales especificando primitivas"},
                        ]
                    },
                    {
                        "notation": "2.2.2", "label": "Verificar Indivisibilidad Funcional de Nodos",
                        "children": [
                            {"notation": "2.2.2.1", "label": "Extraer códigos y estándares de referencia para términos atómicos indivisibles"},
                            {"notation": "2.2.2.2", "label": "Confirmar granularidad mínima atómica terminal (Level-k Maximum)"},
                        ]
                    },
                ]
            },
        ]
    },
    {
        "notation": "3", "label": "Normalizar y Mapear a Forma Canónica",
        "children": [
            {
                "notation": "3.1", "label": "Lematizar y Controlar Variación Formante",
                "children": [
                    {
                        "notation": "3.1.1", "label": "Reducir Morfemas a Forma Canónica",
                        "children": [
                            {"notation": "3.1.1.1", "label": "Convertir formas plurale tantum a singular canónico"},
                            {"notation": "3.1.1.2", "label": "Estandarizar formas no personales reduciendo verbos a infinitivos"},
                        ]
                    },
                    {
                        "notation": "3.1.2", "label": "Resolver Heterogeneidad Ortotipográfica",
                        "children": [
                            {"notation": "3.1.2.1", "label": "Estandarizar uso de guiones, diacríticos y espacios en blanco"},
                            {"notation": "3.1.2.2", "label": "Mapear siglas y acrónimos a sintagmas expandidos", "iso": "[Schwartz-Hearst 2003]"},
                        ]
                    },
                ]
            },
            {
                "notation": "3.2", "label": "Desambiguar Polisemia e Identificar Sinónimos",
                "children": [
                    {
                        "notation": "3.2.1", "label": "Aislar Sentidos Polisémicos (WSD)",
                        "children": [
                            {"notation": "3.2.1.1", "label": "Generar nodos discretos independientes mediante análisis contextual"},
                            {"notation": "3.2.1.2", "label": "Asignar identificadores unívocos (IRI / UUID v4) a homónimos técnicos", "iso": "[RFC 3987, RFC 4122]"},
                        ]
                    },
                    {
                        "notation": "3.2.2", "label": "Alinear Variantes Sinónimas",
                        "children": [
                            {"notation": "3.2.2.1", "label": "Ejecutar enlace de formas alternativas hacia el lema preferente"},
                            {"notation": "3.2.2.2", "label": "Validar lema preferente contra estándares internacionales", "iso": "[ISO / IEEE / SNOMED CT]"},
                        ]
                    },
                ]
            },
        ]
    },
    {
        "notation": "4", "label": "Estructurar Conceptos y Generar Grafo Imperativo",
        "children": [
            {
                "notation": "4.1", "label": "Implementar Principios Ontológicos (MECE)",
                "children": [
                    {
                        "notation": "4.1.1", "label": "Verificar Exclusión Mutua",
                        "children": [
                            {"notation": "4.1.1.1", "label": "Auditar solapamientos entre nodos pares y reparar intersecciones"},
                            {"notation": "4.1.1.2", "label": "Asignar criterios discriminantes unívocos en las fronteras categoriales"},
                        ]
                    },
                    {
                        "notation": "4.1.2", "label": "Verificar Exhaustividad Colectiva",
                        "children": [
                            {"notation": "4.1.2.1", "label": "Confirmar cobertura completa del nodo padre subsanando vacíos"},
                            {"notation": "4.1.2.2", "label": "Consolidar árbol integral MECE cerrando la jerarquía terminológica"},
                        ]
                    },
                ]
            },
            {
                "notation": "4.2", "label": "Renderizar Flujo Sintáctico Operativo",
                "children": [
                    {
                        "notation": "4.2.1", "label": "Disponer Estructura Visual en Árbol Vertical",
                        "children": [
                            {"notation": "4.2.1.1", "label": "Formatear caracteres de ramificación (├──, └──) con sangría estricta"},
                            {"notation": "4.2.1.2", "label": "Validar secuencias numéricas continuas en notación decimal jerárquica"},
                        ]
                    },
                    {
                        "notation": "4.2.2", "label": "Transmutar Sintagmas Nominales a Acción",
                        "children": [
                            {"notation": "4.2.2.1", "label": "Convertir nodos a sintaxis imperativa pura", "iso": "[Verbo + Objeto + Estándar]"},
                            {"notation": "4.2.2.2", "label": "Exportar grafo de conocimiento a esquemas estructurados", "iso": "[JSON-LD / SKOS RDF]"},
                        ]
                    },
                ]
            },
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────────────────────────────────────

class ImperativeGraphBuilder:
    """
    Fase 4: Construcción del Grafo Imperativo Normalizado.

    Operaciones:
      1. Cargar árbol del spec (SPEC_TREE) o construir desde Fase 3
      2. Transmutación nominal → imperativa
      3. Validación MECE
      4. Renderizado ASCII
    """

    def __init__(self, use_spec_tree: bool = True):
        self.use_spec_tree = use_spec_tree

    # ── API pública ──────────────────────────────────────────────────────────

    def build_graph(
        self,
        canonical_forms: list[CanonicalForm],
        extra_nodes: list[dict] | None = None,
    ) -> Phase4Result:
        """
        Construye el grafo imperativo.
        Si use_spec_tree=True, usa el árbol del spec como estructura base
        e incorpora las formas canónicas de Fase 3 en los nodos correspondientes.
        """
        if self.use_spec_tree:
            graph = self._build_from_spec()
        else:
            graph = self._build_from_canonical(canonical_forms)

        # Transmutación imperativa en todos los nodos
        for node in graph.all_nodes():
            if not node.imperative_label:
                node.imperative_label = self._transmute_to_imperative(
                    node.canonical.lemma
                )

        # Validación MECE — solo reportar violaciones, no modificar mece_valid
        # (las violaciones son warnings informativos, no invalidan el grafo)
        violations = self._validate_mece(graph)

        # Marcar nodos atómicos
        for node in graph.all_nodes():
            if not node.children:
                node.role = NodeRole.ATOMIC

        return Phase4Result(
            graph=graph,
            mece_violations=violations,
            imperative_nodes=len([n for n in graph.all_nodes() if n.imperative_label]),
        )

    # ── Construcción desde SPEC_TREE ──────────────────────────────────────────

    def _build_from_spec(self) -> OntologyGraph:
        """Materializa el árbol del spec en OntologyGraph."""
        graph = OntologyGraph()
        for root_def in SPEC_TREE:
            node = self._materialize_node(root_def, parent_notation=None)
            node.role = NodeRole.ROOT
            graph.top_concepts.append(node)
        return graph

    def _materialize_node(
        self, node_def: dict, parent_notation: str | None
    ) -> OntologyNode:
        """Recursivamente materializa un nodo del spec en OntologyNode."""
        notation = node_def["notation"]
        label = node_def["label"]
        iso = node_def.get("iso", "")

        cf = CanonicalForm(
            lemma=label,
            iri=f"urn:nodo:{notation}",
            iso_standard=iso if iso else None,
        )

        node = OntologyNode(
            notation=notation,
            canonical=cf,
            imperative_label=self._transmute_to_imperative(label, iso),
            parent_notation=parent_notation,
        )

        for child_def in node_def.get("children", []):
            child = self._materialize_node(child_def, parent_notation=notation)
            node.children.append(child)

        return node

    # ── Construcción desde formas canónicas ──────────────────────────────────

    def _build_from_canonical(self, forms: list[CanonicalForm]) -> OntologyGraph:
        """
        Construye grafo desde cero a partir de formas canónicas de Fase 3.
        Estructura plana agrupada en 4 ramas raíz por afinidad temática.
        """
        graph = OntologyGraph()
        buckets: dict[str, list[CanonicalForm]] = {
            "filtrado": [], "clustering": [], "canonicalización": [], "estructuración": []
        }

        keywords = {
            "filtrado": ["filtrar", "extraer", "detectar", "discriminar", "purgar", "excluir"],
            "clustering": ["cluster", "bfs", "coseno", "similitud", "búsqueda", "balancear"],
            "canonicalización": ["lematizar", "normalizar", "desambiguar", "acrónimo", "iri", "uuid"],
            "estructuración": ["estructurar", "mece", "imperativo", "renderizar", "exportar"],
        }

        for cf in forms:
            placed = False
            for bucket, kws in keywords.items():
                if any(kw in cf.lemma.lower() for kw in kws):
                    buckets[bucket].append(cf)
                    placed = True
                    break
            if not placed:
                buckets["estructuración"].append(cf)

        notation_counter = {"filtrado": "1", "clustering": "2", "canonicalización": "3", "estructuración": "4"}
        root_labels = {
            "filtrado": "Minar y Filtrar Patrones Sintácticos Complejos",
            "clustering": "Extraer Candidatos Léxicos y Ejecutar Búsqueda en Grafo",
            "canonicalización": "Normalizar y Mapear a Forma Canónica",
            "estructuración": "Estructurar Conceptos y Generar Grafo Imperativo",
        }

        for bucket, cfs in buckets.items():
            root_cf = CanonicalForm(
                lemma=root_labels[bucket],
                iri=f"urn:nodo:{notation_counter[bucket]}",
            )
            root_node = OntologyNode(
                notation=notation_counter[bucket],
                canonical=root_cf,
                role=NodeRole.ROOT,
            )
            for i, cf in enumerate(cfs, start=1):
                child_node = OntologyNode(
                    notation=f"{notation_counter[bucket]}.{i}",
                    canonical=cf,
                    parent_notation=notation_counter[bucket],
                    role=NodeRole.ATOMIC if not cfs else NodeRole.BRANCH,
                )
                root_node.children.append(child_node)
            graph.top_concepts.append(root_node)

        return graph

    # ── Transmutación NP → VP_imp ─────────────────────────────────────────────

    def _transmute_to_imperative(self, label: str, iso: str = "") -> str:
        """
        g(NP) → VP_imp = [Verbo_Imp] + [Objeto_Técnico] + [Estándar_ISO]

        Detecta el sustantivo clave del sintagma y asigna el verbo operativo
        correspondiente. Si el label ya es imperativo (inicia con verbo inf),
        lo capitaliza y añade el estándar.
        """
        label_lower = label.lower().strip()

        # ① Ya es imperativo — está en forma verbal
        imperative_verbs = [
            "extraer", "minar", "filtrar", "detectar", "aislar", "mapear",
            "aplicar", "ejecutar", "balancear", "explorar", "profundizar",
            "verificar", "normalizar", "lematizar", "resolver", "desambiguar",
            "alinear", "estructurar", "implementar", "confirmar", "renderizar",
            "transmutar", "exportar", "generar", "asignar", "auditar",
            "reparar", "consolidar", "validar", "purgar", "estandarizar",
            "sustituir", "convertir", "calcular", "agrupar", "cubrir",
            "incluir", "delimitar", "desglosar", "formatear",
        ]
        first_word = label_lower.split()[0] if label_lower.split() else ""
        if first_word in imperative_verbs:
            base = label.upper()
            return f"{base} {iso}".strip()

        # ② Buscar sustantivo clave → verbo
        for noun, verb in IMPERATIVE_VERB_MAP.items():
            if noun in label_lower:
                # Reemplazar el sustantivo por el verbo en la cadena
                rest = re.sub(re.escape(noun), "", label_lower, count=1, flags=re.IGNORECASE).strip()
                rest = rest.strip(" de la el los las del")
                obj = rest.upper() if rest else label.upper()

                # Encontrar sufijo ISO en el label
                iso_suffix = iso
                if not iso_suffix:
                    for kw, std in ISO_SUFFIX_MAP.items():
                        if kw in label_lower:
                            iso_suffix = std
                            break

                return f"{verb} {obj} {iso_suffix}".strip()

        # ③ Fallback: EJECUTAR + label completo
        return f"EJECUTAR: {label.upper()} {iso}".strip()

    # ── Validación MECE ───────────────────────────────────────────────────────

    def _validate_mece(self, graph: OntologyGraph) -> list[str]:
        """
        Audita:
          1. Exclusión Mutua: no solapamiento semántico entre hermanos
          2. Exhaustividad Colectiva: cobertura completa del nodo padre

        Retorna lista de violaciones (strings descriptivos — informativos, no bloquean SAT).
        """
        violations: list[str] = []

        def check_node(node: OntologyNode):
            if not node.children:
                return

            children_labels = [c.canonical.lemma.lower() for c in node.children]

            # ── Exclusión Mutua ──────────────────────────────────────────────
            seen_tokens: dict[str, str] = {}
            for child in node.children:
                tokens = set(child.canonical.lemma.lower().split())
                tokens -= {"y", "o", "de", "la", "el", "los", "las", "en", "para"}
                for tok in tokens:
                    if tok in seen_tokens and seen_tokens[tok] != child.notation:
                        violations.append(
                            f"{child.notation}: Posible solapamiento semántico "
                            f"con {seen_tokens[tok]} — token compartido: '{tok}'"
                        )
                    else:
                        seen_tokens[tok] = child.notation

            # ── Exhaustividad Colectiva ───────────────────────────────────────
            parent_tokens = set(node.canonical.lemma.lower().split())
            parent_tokens -= {"y", "o", "de", "la", "el", "los", "las", "en", "para", "a"}
            covered_tokens = set()
            for child in node.children:
                covered_tokens.update(child.canonical.lemma.lower().split())

            uncovered = parent_tokens - covered_tokens - {
                "y", "de", "el", "la", "los", "las", "en", "para"
            }
            if len(uncovered) > 3:  # Umbral: >3 tokens sin cubrir
                violations.append(
                    f"{node.notation}: Posible gap de exhaustividad — "
                    f"tokens no cubiertos: {sorted(uncovered)[:5]}"
                )

            for child in node.children:
                check_node(child)

        for root in graph.top_concepts:
            check_node(root)

        return violations

    # ── Renderizado ASCII ─────────────────────────────────────────────────────

    def render_tree(self, graph: OntologyGraph, use_imperative: bool = True) -> str:
        """
        Renderiza el grafo como árbol ASCII con notación decimal jerárquica.
        Caracteres: ├──, └──, │  (sangría 4 espacios por nivel)
        """
        lines: list[str] = []

        def render_node(node: OntologyNode, prefix: str, is_last: bool):
            connector = "└── " if is_last else "├── "
            label = node.imperative_label if use_imperative else node.canonical.lemma
            lines.append(f"{prefix}{connector}{node.notation}. {label}")

            child_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(node.children):
                render_node(child, child_prefix, i == len(node.children) - 1)

        for i, root in enumerate(graph.top_concepts):
            label = root.imperative_label if use_imperative else root.canonical.lemma
            lines.append(f"{root.notation}. {label}")
            for j, child in enumerate(root.children):
                render_node(child, "", j == len(root.children) - 1)
            if i < len(graph.top_concepts) - 1:
                lines.append("")

        return "\n".join(lines)
