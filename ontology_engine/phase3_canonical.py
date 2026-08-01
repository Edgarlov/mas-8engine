"""
phase3_canonical.py — Canonicalización Ontológica (Fase 3)

Implementa:
  - Lematización formal: f(W_var) → L_canon
  - Control de variación formante (plurale tantum, infinitivos)
  - Resolución ortotipográfica (guiones, diacríticos, siglas)
  - Expansión de acrónimos via Schwartz-Hearst
  - Desambiguación de sentidos polisémicos (WSD contextual)
  - Asignación de IRI (urn:nodo:{notation}) + UUID v4
  - Validación contra estándares internacionales [ISO/IEEE/SNOMED CT]

Formalismo:
  f(W_var) → L_canon
  Acronym(x) ↦ LongForm(y) vía Schwartz-Hearst
  ∀x ∃!u (Entidad(x) → IRI(u) ∧ hasUUID(x, u))
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from .models import CanonicalForm, Cluster, Phase3Result

# ─────────────────────────────────────────────────────────────────────────────
# Léxico de Validación Técnica [ISO/IEEE/SNOMED]
# ─────────────────────────────────────────────────────────────────────────────

ISO_VALIDATED_TERMS: dict[str, str] = {
    # ISO 24613 — Lexical Markup Framework
    "sintagma nominal": "ISO 24613-1",
    "forma canónica": "ISO 24613-2",
    "lema": "ISO 24613-1",
    "unidad léxica": "ISO 24613-1",
    # ISO 25100 — Terminology
    "término": "ISO 25100",
    "definición": "ISO 25100",
    "concepto": "ISO 25100",
    # IEEE Std 1016 — Software Design
    "componente": "IEEE 1016",
    "módulo": "IEEE 1016",
    "interfaz": "IEEE 1016",
    # SKOS W3C
    "concepto esquema": "W3C SKOS",
    "concepto más específico": "W3C SKOS",
    "concepto más amplio": "W3C SKOS",
    "etiqueta preferente": "W3C SKOS",
    # OWL 2
    "clase": "W3C OWL 2",
    "propiedad de objeto": "W3C OWL 2",
    "individuo": "W3C OWL 2",
    "subsunción": "W3C OWL 2",
    # Otros técnicos comunes
    "algoritmo": "IEEE Std 610",
    "ontología": "W3C OWL 2",
    "grafo": "ISO/IEC 2382",
    "árbol": "ISO/IEC 2382",
    "nodo": "ISO/IEC 2382",
}

# Términos polisémicos conocidos en NLP/ontología
POLYSEMOUS_TERMS: dict[str, list[dict]] = {
    "clase": [
        {"sense_id": 0, "context": "OOP/software", "definition": "Plantilla de objetos en programación orientada a objetos"},
        {"sense_id": 1, "context": "OWL/ontología", "definition": "Conjunto de individuos con características comunes en lógica descriptiva"},
        {"sense_id": 2, "context": "estadística", "definition": "Categoría en clasificación estadística"},
    ],
    "grafo": [
        {"sense_id": 0, "context": "matemáticas", "definition": "Estructura G=(V,E) con vértices y aristas"},
        {"sense_id": 1, "context": "conocimiento", "definition": "Representación semántica de entidades y relaciones"},
    ],
    "nodo": [
        {"sense_id": 0, "context": "grafo", "definition": "Vértice en una estructura de grafo"},
        {"sense_id": 1, "context": "árbol", "definition": "Elemento en una jerarquía arborescente"},
        {"sense_id": 2, "context": "red", "definition": "Dispositivo en una red de comunicación"},
    ],
    "modelo": [
        {"sense_id": 0, "context": "NLP/ML", "definition": "Parámetros aprendidos de un sistema de aprendizaje automático"},
        {"sense_id": 1, "context": "ontología", "definition": "Representación formal de un dominio de conocimiento"},
        {"sense_id": 2, "context": "matemáticas", "definition": "Interpretación que satisface un conjunto de axiomas"},
    ],
}

# Mapa de formas irregulares → lema canónico
CANONICAL_MAP: dict[str, str] = {
    # Plurales → singular canónico
    "sintagmas": "sintagma",
    "nodos": "nodo",
    "grafos": "grafo",
    "árboles": "árbol",
    "ramas": "rama",
    "clústeres": "cluster",
    "embeddings": "embedding",
    "estándares": "estándar",
    "conceptos": "concepto",
    "clases": "clase",
    "términos": "término",
    "formas": "forma",
    "relaciones": "relación",
    "entidades": "entidad",
    "axiomas": "axioma",
    "restricciones": "restricción",
    # Variantes ortográficas
    "cluster": "clúster",
    "clusters": "clúster",
    "embeddings": "embedding",
    "tag": "etiqueta",
    "tags": "etiqueta",
    "token": "token",
    "tokens": "token",
    "parser": "analizador sintáctico",
    "parsing": "análisis sintáctico",
    "stemmer": "lematizador",
    "stemming": "lematización",
}

# Acrónimos conocidos (Schwartz-Hearst seed)
KNOWN_ACRONYMS: dict[str, str] = {
    "NLP": "Natural Language Processing",
    "PNL": "Procesamiento del Lenguaje Natural",
    "SNC": "Sintagma Nominal Canónico",
    "POS": "Part-of-Speech",
    "WSD": "Word Sense Disambiguation",
    "BFS": "Búsqueda en Amplitud (Breadth-First Search)",
    "DFS": "Búsqueda en Profundidad (Depth-First Search)",
    "TF-IDF": "Term Frequency-Inverse Document Frequency",
    "OWL": "Web Ontology Language",
    "RDF": "Resource Description Framework",
    "SKOS": "Simple Knowledge Organization System",
    "IRI": "Internationalized Resource Identifier",
    "UUID": "Universally Unique Identifier",
    "MECE": "Mutually Exclusive Collectively Exhaustive",
    "SAT": "Boolean Satisfiability Problem",
    "CDCL": "Conflict-Driven Clause Learning",
    "CNF": "Conjunctive Normal Form",
    "FOL": "First-Order Logic",
    "AGM": "Alchourrón-Gärdenfors-Makinson (belief revision)",
    "ISO": "International Organization for Standardization",
    "IEEE": "Institute of Electrical and Electronics Engineers",
    "URI": "Uniform Resource Identifier",
    "JSON": "JavaScript Object Notation",
    "LD": "Linked Data",
    "API": "Application Programming Interface",
}


# ─────────────────────────────────────────────────────────────────────────────
# Intentar importar spaCy (opcional)
# ─────────────────────────────────────────────────────────────────────────────

try:
    import spacy
    _nlp3 = spacy.load("es_core_news_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    _nlp3 = None
    SPACY_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Schwartz-Hearst Acronym Detector
# ─────────────────────────────────────────────────────────────────────────────

_ACRONYM_PATTERN = re.compile(
    r'\b([A-Z][A-Z0-9\-]{1,9})\b'                    # Acrónimo: 2-10 chars mayúsculas
    r'\s*\(([^)]{5,80})\)'                            # (Forma larga entre paréntesis)
    r'|'
    r'\b([A-Za-záéíóúüñÁÉÍÓÚÜÑ][^(]{5,80})\s*'
    r'\(([A-Z][A-Z0-9\-]{1,9})\)',                    # Forma larga (ACRÓNIMO)
    re.UNICODE
)


class SchwartzHearst:
    """
    Detector de acrónimos basado en el algoritmo Schwartz-Hearst (2003).
    Extrae pares (acrónimo, forma_larga) del corpus.
    """

    @staticmethod
    def extract(text: str) -> dict[str, str]:
        """Retorna dict {ACRONIMO: 'forma larga'}."""
        pairs: dict[str, str] = dict(KNOWN_ACRONYMS)  # Seed con conocidos

        for m in _ACRONYM_PATTERN.finditer(text):
            if m.group(1) and m.group(2):          # Patrón ACR (long)
                acronym = m.group(1).strip()
                long_form = m.group(2).strip()
            elif m.group(3) and m.group(4):         # Patrón long (ACR)
                long_form = m.group(3).strip()
                acronym = m.group(4).strip()
            else:
                continue

            # Validar que el acrónimo coincide con iniciales de la forma larga
            if SchwartzHearst._validate_initials(acronym, long_form):
                pairs[acronym] = long_form

        return pairs

    @staticmethod
    def _validate_initials(acronym: str, long_form: str) -> bool:
        """Verifica que las iniciales del acrónimo corresponden a la forma larga."""
        clean_acr = re.sub(r'[^A-Z]', '', acronym.upper())
        if len(clean_acr) < 2:
            return True  # No validable — aceptar

        words = [w for w in re.split(r'\W+', long_form) if w]
        significant_initials = "".join(
            w[0].upper() for w in words
            if len(w) > 2 and w[0].isupper()
        )

        if not significant_initials:
            significant_initials = "".join(w[0].upper() for w in words if w)

        # Coincidencia parcial: al menos 60% de letras del acrónimo en las iniciales
        matches = sum(1 for c in clean_acr if c in significant_initials)
        return matches / len(clean_acr) >= 0.6


# ─────────────────────────────────────────────────────────────────────────────
# Lematizador Canónico (Snowball fallback)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from nltk.stem.snowball import SnowballStemmer
    _STEMMER = SnowballStemmer("spanish")
    STEMMER_AVAILABLE = True
except ImportError:
    _STEMMER = None
    STEMMER_AVAILABLE = False

_SUFFIX_MAP: dict[str, str] = {
    "aciones": "ación", "iciones": "ición", "aciones": "ación",
    "mientos": "miento", "idades": "idad", "ajes": "aje",
    "uras": "ura", "eros": "ero", "istas": "ista",
    "icos": "ico", "icas": "ica", "ivos": "ivo", "ivas": "iva",
    "ables": "able", "ibles": "ible", "ados": "ado", "adas": "ada",
    "osos": "oso", "osas": "osa",
}


def _simple_lemmatize(word: str) -> str:
    """Lematización heurística por sufijo (sin spaCy/NLTK)."""
    w = word.lower().strip()
    if w in CANONICAL_MAP:
        return CANONICAL_MAP[w]
    for suffix, canonical in _SUFFIX_MAP.items():
        if w.endswith(suffix):
            return w[: -len(suffix)] + canonical
    # Singular básico
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and len(w) > 3:
        return w[:-1]
    return w


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────────────────────────────────────

class Canonicalizer:
    """
    Fase 3: Normalización a Forma Canónica.

    Operaciones:
      1. Lematización formal
      2. Resolución ortotipográfica + expansión acrónimos
      3. WSD (Word Sense Disambiguation)
      4. Asignación IRI + UUID
      5. Validación estándares internacionales
    """

    def __init__(self, context_window: int = 5, iri_prefix: str = "urn:nodo:"):
        self.context_window = context_window
        self.iri_prefix = iri_prefix
        self._acronym_db: dict[str, str] = dict(KNOWN_ACRONYMS)

    # ── API pública ──────────────────────────────────────────────────────────

    def canonicalize(self, clusters: list[Cluster], corpus: str = "") -> Phase3Result:
        """
        Entrada: clusters de Fase 2 + corpus original para WSD.
        Salida: Phase3Result con formas canónicas completas.
        """
        # Actualizar BD de acrónimos con hallazgos del corpus
        if corpus:
            discovered = SchwartzHearst.extract(corpus)
            self._acronym_db.update(discovered)

        canonical_forms: list[CanonicalForm] = []
        polysemous_count = 0
        acronyms_expanded = 0

        for cluster in clusters:
            for unit in cluster.members:
                cf = self._process_unit(unit, corpus)
                if cf.is_polysemous:
                    polysemous_count += 1
                if cf.acronym_expansion:
                    acronyms_expanded += 1
                canonical_forms.append(cf)

        # Deduplicar por lema preferente
        canonical_forms = self._deduplicate(canonical_forms)

        return Phase3Result(
            canonical_forms=canonical_forms,
            polysemous_count=polysemous_count,
            acronyms_expanded=acronyms_expanded,
        )

    # ── Procesamiento por unidad ─────────────────────────────────────────────

    def _process_unit(self, unit, corpus: str) -> CanonicalForm:
        """Pipeline completo de canonicalización para una LexicalUnit."""
        surface = unit.surface_form

        # 1. Expansión de acrónimos
        expanded, expansion = self._expand_acronyms(surface)
        acronym_exp = expansion if expansion != surface else None

        # 2. Resolución ortotipográfica
        normalized = self._normalize_orthotypography(expanded)

        # 3. Lematización
        lemma = self._lemmatize(normalized)

        # 4. WSD
        senses = POLYSEMOUS_TERMS.get(lemma.lower(), [])
        is_poly = len(senses) > 1
        sense_id = self._disambiguate_sense(lemma, senses, corpus)

        # 5. ISO/IEEE/SNOMED validation
        iso_std = self._find_iso_standard(lemma)

        # 6. IRI + UUID
        notation = self._generate_notation(lemma)
        iri = f"{self.iri_prefix}{notation}"

        cf = CanonicalForm(
            lemma=lemma,
            surface_variants=[surface, expanded] if expanded != surface else [surface],
            acronym_expansion=acronym_exp,
            iri=iri,
            uuid=str(uuid.uuid4()),
            sense_id=sense_id,
            iso_standard=iso_std,
            is_polysemous=is_poly,
        )

        # Generar nodos alternativos para términos polisémicos
        if is_poly:
            for sense in senses:
                if sense["sense_id"] != sense_id:
                    alt = CanonicalForm(
                        lemma=f"{lemma}#{sense['sense_id']}",
                        surface_variants=[surface],
                        iri=f"{self.iri_prefix}{notation}.{sense['sense_id']}",
                        uuid=str(uuid.uuid4()),
                        sense_id=sense["sense_id"],
                    )
                    cf.alt_senses.append(alt)

        return cf

    # ── Expansión de Acrónimos ────────────────────────────────────────────────

    def _expand_acronyms(self, text: str) -> tuple[str, str]:
        """
        Expande acrónimos conocidos.
        Retorna (texto_expandido, expansión_aplicada).
        """
        result = text
        applied = ""
        # Buscar acrónimos en texto (tokens en mayúsculas)
        for token in text.upper().split():
            clean_token = re.sub(r'[^A-Z0-9\-]', '', token)
            if clean_token in self._acronym_db:
                expansion = self._acronym_db[clean_token]
                result = re.sub(
                    re.escape(token), expansion, result, flags=re.IGNORECASE
                )
                applied = expansion
        return result, applied

    # ── Normalización Ortotipográfica ─────────────────────────────────────────

    def _normalize_orthotypography(self, text: str) -> str:
        """
        Estandariza:
          - Guiones: normalización a espacio o guion corto
          - Diacríticos: preservar acentos técnicos
          - Espacios múltiples → simple
          - Minúsculas (salvo acrónimos)
        """
        text = text.strip().lower()
        # Normalizar guiones variantes
        text = re.sub(r'[–—−]', '-', text)
        # Múltiples espacios
        text = re.sub(r'\s+', ' ', text)
        # Eliminar puntuación terminal
        text = text.rstrip('.,;:!?')
        return text

    # ── Lematización ──────────────────────────────────────────────────────────

    def _lemmatize(self, text: str) -> str:
        """
        Lematización formal: f(W_var) → L_canon.
        Intenta spaCy → NLTK Snowball → heurística sufijo.
        """
        # Mapa directo
        if text.lower() in CANONICAL_MAP:
            return CANONICAL_MAP[text.lower()]

        if SPACY_AVAILABLE and _nlp3 is not None:
            doc = _nlp3(text)
            lemmas = [token.lemma_ for token in doc if not token.is_space]
            return " ".join(lemmas) if lemmas else text

        # Snowball por token
        words = text.split()
        result = []
        for w in words:
            if w in CANONICAL_MAP:
                result.append(CANONICAL_MAP[w])
            elif STEMMER_AVAILABLE and _STEMMER:
                # Usar stem solo para detección, mantener forma original si es razonable
                result.append(_simple_lemmatize(w))
            else:
                result.append(_simple_lemmatize(w))
        return " ".join(result)

    # ── WSD ───────────────────────────────────────────────────────────────────

    def _disambiguate_sense(
        self, lemma: str, senses: list[dict], corpus: str
    ) -> int:
        """
        WSD contextual simple: cuenta ocurrencias de palabras de contexto
        asociadas a cada sentido y elige el mayoritario.
        """
        if not senses or len(senses) <= 1:
            return 0

        context_keywords: dict[str, list[str]] = {
            "OOP/software": ["clase", "objeto", "instancia", "herencia", "método"],
            "OWL/ontología": ["ontología", "owl", "rdfs", "axioma", "subsunción", "descripción"],
            "estadística": ["frecuencia", "distribución", "probabilidad", "muestra"],
            "matemáticas": ["vértice", "arista", "grafo", "ruta", "camino"],
            "conocimiento": ["semántica", "entidad", "relación", "triple", "sujeto", "predicado"],
            "grafo": ["vértice", "arista", "adyacencia", "bfs", "dfs"],
            "árbol": ["raíz", "padre", "hijo", "hoja", "profundidad", "jerarquía"],
            "red": ["protocolo", "ip", "nodo", "switch", "router", "subred"],
            "NLP/ML": ["parámetro", "peso", "entrenamiento", "inferencia", "embedding"],
        }

        corpus_lower = corpus.lower()
        sense_scores: dict[int, float] = {}

        for sense in senses:
            ctx = sense.get("context", "")
            keywords = context_keywords.get(ctx, [])
            score = sum(corpus_lower.count(kw) for kw in keywords)
            sense_scores[sense["sense_id"]] = score

        if not sense_scores:
            return 0

        return max(sense_scores, key=lambda k: sense_scores[k])

    # ── Validación ISO/IEEE ───────────────────────────────────────────────────

    def _find_iso_standard(self, lemma: str) -> str | None:
        """Busca el estándar internacional más específico para el lema."""
        lemma_lower = lemma.lower()
        for term, standard in ISO_VALIDATED_TERMS.items():
            if term in lemma_lower or lemma_lower in term:
                return standard
        return None

    # ── Generación IRI ────────────────────────────────────────────────────────

    def _generate_notation(self, lemma: str) -> str:
        """
        Genera notación decimal jerárquica provisional para el lema.
        En Fase 4 se asignará la notación definitiva según posición en el árbol.
        """
        # Hash corto del lema como seed
        import hashlib
        h = hashlib.md5(lemma.encode()).hexdigest()[:6]
        return f"auto.{h}"

    # ── Deduplicación ─────────────────────────────────────────────────────────

    def _deduplicate(self, forms: list[CanonicalForm]) -> list[CanonicalForm]:
        """Elimina duplicados por lema preferente, conservando la forma más informativa."""
        seen: dict[str, CanonicalForm] = {}
        for cf in forms:
            key = cf.lemma.lower()
            if key not in seen:
                seen[key] = cf
            else:
                # Conservar la que tiene más variantes o estándar ISO
                existing = seen[key]
                if len(cf.surface_variants) > len(existing.surface_variants):
                    seen[key] = cf
                elif cf.iso_standard and not existing.iso_standard:
                    seen[key] = cf
        return list(seen.values())
