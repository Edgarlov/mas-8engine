"""
exporter.py — Exportador JSON-LD SKOS (Sección 5 del Spec)

Implementa:
  - Serialización completa del OntologyGraph a JSON-LD + SKOS RDF
  - Contexto @context: skos, schema, dc, xsd, owl
  - Expansión de todos los nodos con relaciones skos:narrower / skos:broader
  - Metadatos dc:title, dc:creator, dc:created
  - Exportación a string JSON, RDF Turtle (si rdflib disponible)
  - Importación desde JSON-LD para reconstrucción del grafo

Estándar: W3C JSON-LD 1.1, W3C SKOS Core
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import CanonicalForm, NodeRole, OntologyGraph, OntologyNode, RelationType

# ─────────────────────────────────────────────────────────────────────────────
# Intentar importar rdflib (opcional)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from rdflib import Graph as RDFGraph, Literal, Namespace, RDF, SKOS, URIRef, XSD
    from rdflib.namespace import DC, DCTERMS
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False


# Namespaces
SKOS_NS = "http://www.w3.org/2004/02/skos/core#"
SCHEMA_NS = "http://schema.org/"
DC_NS = "http://purl.org/dc/terms/"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
OWL_NS = "http://www.w3.org/2002/07/owl#"


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────────────────────────────────────

class SKOSExporter:
    """
    Exportador bidireccional JSON-LD ↔ OntologyGraph.

    Soporta:
      - Exportación a JSON-LD (siempre disponible)
      - Exportación a RDF Turtle (requiere rdflib)
      - Importación desde JSON-LD
    """

    def __init__(self, language: str = "es"):
        self.lang = language

    # ── Exportación JSON-LD ───────────────────────────────────────────────────

    def to_jsonld(self, graph: OntologyGraph) -> dict[str, Any]:
        """Serializa el grafo completo a JSON-LD SKOS."""
        doc: dict[str, Any] = {
            "@context": {
                "skos": SKOS_NS,
                "schema": SCHEMA_NS,
                "dc": DC_NS,
                "xsd": XSD_NS,
                "owl": OWL_NS,
                "skos:prefLabel": {"@language": self.lang},
                "skos:altLabel": {"@language": self.lang},
                "skos:definition": {"@language": self.lang},
                "skos:notation": {"@type": "xsd:string"},
                "dc:created": {"@type": "xsd:dateTime"},
            },
            "@type": "skos:ConceptScheme",
            "@id": graph.scheme_id,
            "dc:title": graph.title,
            "dc:creator": graph.creator,
            "dc:created": datetime.now(tz=timezone.utc).isoformat(),
            "skos:hasTopConcept": [
                self._node_to_jsonld(node) for node in graph.top_concepts
            ],
            # Estadísticas del grafo
            "_meta": {
                "engine_version": "2.0",
                "spec_source": "ESPECIFICACION_INGENIERIA_ONTOLOGICA.md",
                "stats": graph.stats(),
                "mece_compliant": all(
                    n.mece_valid for n in graph.all_nodes()
                ),
            },
        }
        return doc

    def _node_to_jsonld(self, node: OntologyNode) -> dict[str, Any]:
        """Serializa un nodo y sus descendientes recursivamente."""
        obj: dict[str, Any] = {
            "@type": "skos:Concept",
            "@id": node.iri,
            "skos:notation": node.notation,
            "skos:prefLabel": node.canonical.lemma,
            "owl:imperative": node.imperative_label,
            "skos:inScheme": {"@id": "urn:engine:ontologia:grafo-imperativo-v2"},
        }

        # Variantes alternativas
        if len(node.canonical.surface_variants) > 1:
            obj["skos:altLabel"] = node.canonical.surface_variants[1:]

        # Expansión de acrónimo
        if node.canonical.acronym_expansion:
            obj["skos:note"] = f"Acronym expansion: {node.canonical.acronym_expansion}"

        # Estándar ISO
        if node.canonical.iso_standard:
            obj["dc:source"] = node.canonical.iso_standard

        # UUID para desambiguación
        if node.canonical.uuid:
            obj["owl:hasKey"] = node.canonical.uuid

        # Metadata MECE
        obj["_mece"] = {
            "valid": node.mece_valid,
            "role": node.role.value,
            "violations": node.mece_violations,
        }

        # Relación broader (padre)
        if node.parent_notation:
            obj["skos:broader"] = {"@id": f"urn:nodo:{node.parent_notation}"}

        # Nodos hijos (skos:narrower)
        if node.children:
            obj["skos:narrower"] = [
                self._node_to_jsonld(child) for child in node.children
            ]

        # Nodos atómicos: marcar como skos:Concept de nivel terminal
        if node.is_atomic:
            obj["skos:topConceptOf"] = None  # Placeholder — reemplazado en validación

        return obj

    def to_json_string(self, graph: OntologyGraph, indent: int = 2) -> str:
        """Serializa a string JSON con indentación."""
        return json.dumps(self.to_jsonld(graph), ensure_ascii=False, indent=indent)

    # ── Exportación RDF Turtle ────────────────────────────────────────────────

    def to_turtle(self, graph: OntologyGraph) -> str:
        """
        Serializa a RDF Turtle (requiere rdflib).
        Retorna string Turtle o JSON-LD como fallback.
        """
        if not RDFLIB_AVAILABLE:
            return f"# rdflib no disponible — exportando JSON-LD como fallback\n{self.to_json_string(graph)}"

        g = RDFGraph()
        skos_ns = Namespace(SKOS_NS)
        dc_ns = Namespace(DC_NS)

        scheme_uri = URIRef(graph.scheme_id)
        g.add((scheme_uri, RDF.type, skos_ns.ConceptScheme))
        g.add((scheme_uri, dc_ns.title, Literal(graph.title, lang=self.lang)))
        g.add((scheme_uri, dc_ns.creator, Literal(graph.creator)))

        def add_node(node: OntologyNode):
            node_uri = URIRef(node.iri)
            g.add((node_uri, RDF.type, skos_ns.Concept))
            g.add((node_uri, skos_ns.prefLabel, Literal(node.canonical.lemma, lang=self.lang)))
            g.add((node_uri, skos_ns.notation, Literal(node.notation)))
            g.add((node_uri, skos_ns.inScheme, scheme_uri))

            if node.imperative_label:
                imp_ns = Namespace("urn:engine:imperative:")
                g.add((node_uri, imp_ns.label, Literal(node.imperative_label, lang=self.lang)))

            if node.canonical.iso_standard:
                g.add((node_uri, dc_ns.source, Literal(node.canonical.iso_standard)))

            if node.parent_notation:
                parent_uri = URIRef(f"urn:nodo:{node.parent_notation}")
                g.add((node_uri, skos_ns.broader, parent_uri))

            for child in node.children:
                child_uri = URIRef(child.iri)
                g.add((node_uri, skos_ns.narrower, child_uri))
                add_node(child)

        for root in graph.top_concepts:
            g.add((scheme_uri, skos_ns.hasTopConcept, URIRef(root.iri)))
            add_node(root)

        return g.serialize(format="turtle")

    # ── Importación desde JSON-LD ─────────────────────────────────────────────

    def from_jsonld(self, data: dict | str) -> OntologyGraph:
        """Reconstruye OntologyGraph desde un documento JSON-LD SKOS."""
        if isinstance(data, str):
            data = json.loads(data)

        graph = OntologyGraph(
            scheme_id=data.get("@id", "urn:engine:ontologia:grafo-imperativo-v2"),
            title=data.get("dc:title", ""),
            creator=data.get("dc:creator", ""),
        )

        for concept_data in data.get("skos:hasTopConcept", []):
            node = self._jsonld_to_node(concept_data, parent_notation=None)
            if node:
                node.role = NodeRole.ROOT
                graph.top_concepts.append(node)

        return graph

    def _jsonld_to_node(
        self, data: dict, parent_notation: str | None
    ) -> OntologyNode | None:
        """Deserializa un nodo JSON-LD a OntologyNode."""
        notation = data.get("skos:notation", "")
        if not notation:
            return None

        lemma = data.get("skos:prefLabel", notation)
        iri = data.get("@id", f"urn:nodo:{notation}")
        iso = data.get("dc:source")
        imperative = data.get("owl:imperative", "")

        cf = CanonicalForm(
            lemma=lemma,
            iri=iri,
            iso_standard=iso,
            uuid=data.get("owl:hasKey", str(uuid.uuid4())),
        )

        node = OntologyNode(
            notation=notation,
            canonical=cf,
            imperative_label=imperative,
            parent_notation=parent_notation,
        )

        for child_data in data.get("skos:narrower", []):
            child = self._jsonld_to_node(child_data, parent_notation=notation)
            if child:
                node.children.append(child)

        return node

    # ── Exportación a dict para el agente web ────────────────────────────────

    def to_flat_list(self, graph: OntologyGraph) -> list[dict[str, Any]]:
        """
        Exporta el grafo como lista plana de nodos para el frontend.
        Más eficiente para rendering en el cliente.
        """
        flat: list[dict[str, Any]] = []
        for node in graph.all_nodes():
            flat.append({
                "notation": node.notation,
                "iri": node.iri,
                "lemma": node.canonical.lemma,
                "imperative": node.imperative_label,
                "iso": node.canonical.iso_standard,
                "role": node.role.value,
                "parent": node.parent_notation,
                "depth": node.depth,
                "is_atomic": node.is_atomic,
                "mece_valid": node.mece_valid,
                "children_count": len(node.children),
            })
        return flat
