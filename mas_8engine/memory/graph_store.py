"""
MAS-8ENGINE │ graph_store.py
Capa de Persistencia de Grafos de Conocimiento Ontológico (Knowledge Graph) usando RDFlib.
Persistencia de tripletas ISO-704 (Sujeto - Predicado - Objeto) en formato Turtle/N-Triples.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple
from pydantic import BaseModel
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL


class TripleStatement(BaseModel):
    subject: str
    predicate: str
    object_value: str


class KnowledgeGraphEngine:
    """Motor de Persistencia y Consultas Ontológicas en Grafo RDFlib."""

    def __init__(self, storage_path: str = r"C:\Users\edgar\Desktop\agentes\mas_8engine\ontology_graph.ttl"):
        self.storage_path = storage_path
        self.graph = Graph()
        self.MAS8 = Namespace("http://mas8engine.org/ontology#")
        self.graph.bind("mas8", self.MAS8)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)

        if os.path.exists(self.storage_path):
            try:
                self.graph.parse(self.storage_path, format="turtle")
            except Exception:
                pass

    def add_triples(self, triples: List[TripleStatement]) -> int:
        added = 0
        for t in triples:
            sub_uri = URIRef(self.MAS8[t.subject.replace(" ", "_")])
            pred_uri = URIRef(self.MAS8[t.predicate.replace(" ", "_")])
            
            if t.object_value.startswith("http://") or t.object_value.startswith("https://"):
                obj_ref = URIRef(t.object_value)
            else:
                obj_ref = Literal(t.object_value)
                
            self.graph.add((sub_uri, pred_uri, obj_ref))
            added += 1

        self.save()
        return added

    def query_sparql(self, sparql_query: str) -> List[Dict[str, str]]:
        qres = self.graph.query(sparql_query)
        results = []
        for row in qres:
            res_dict = {}
            for var in qres.vars:
                res_dict[str(var)] = str(row[var])
            results.append(res_dict)
        return results

    def save(self):
        self.graph.serialize(destination=self.storage_path, format="turtle")
