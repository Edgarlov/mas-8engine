"""
phase1_filter.py — Filtrado Morfosintáctico (Fase 1 del Engine Ontológico v2.0)

Implementa:
  - Extracción de Sintagmas Nominales Canónicos (SNC)
  - Detección de patrones NOUN+ADJ y NOUN+PREP+NOUN
  - POS tagging via spaCy (con fallback regex robusto)
  - Árboles de dependencia sintáctica
  - Eliminación de stopwords, modismos volátiles y ruido morfosintáctico

Formalismos:
  SNC ⊑ Sustantivo ⊓ ∃tieneAdjetivo.Especificador  [ISO 24613]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import LexicalUnit, Phase1Result, SyntacticPattern

# ─────────────────────────────────────────────────────────────────────────────
# Stopwords y Modismos Volátiles
# ─────────────────────────────────────────────────────────────────────────────

STOPWORDS_ES = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "al", "a", "en", "con", "por", "para", "sin", "sobre", "ante", "bajo",
    "que", "se", "su", "sus", "este", "esta", "estos", "estas", "ese", "esa",
    "esos", "esas", "aquel", "aquella", "aquellos", "aquellas", "yo", "tú",
    "él", "ella", "nosotros", "vosotros", "ellos", "ellas", "me", "te",
    "le", "nos", "os", "les", "muy", "más", "menos", "también", "además",
    "pero", "sino", "aunque", "porque", "cuando", "donde", "como", "si",
    "todo", "toda", "todos", "todas", "cada", "cualquier", "algún", "alguna",
    "ningún", "ninguna", "hay", "es", "son", "fue", "eran", "será", "han",
    "ya", "bien", "así", "aquí", "allí", "entonces", "después", "antes",
    "durante", "mientras", "tanto", "tal", "cual", "cuyo", "cuya",
})

VOLATILE_IDIOMS = frozenset({
    "en general", "por ejemplo", "es decir", "entre otros", "sin embargo",
    "no obstante", "por tanto", "en consecuencia", "a continuación",
    "de hecho", "en efecto", "por lo tanto", "en principio", "a priori",
    "en resumen", "en definitiva", "dicho esto", "cabe mencionar",
    "cabe destacar", "es importante", "hay que tener en cuenta",
    "en este sentido", "en este contexto", "en primer lugar",
    "en segundo lugar", "por último", "finalmente",
})

# Preposiciones que forman cadenas NOUN+PREP+NOUN
PREPOSITIONS = frozenset({"de", "del", "para", "con", "en", "por", "sobre", "ante"})

# Adjetivos técnicos de alta densidad informacional (no filtrar)
TECHNICAL_ADJ_PREFIXES = (
    "morfosintáctic", "semántic", "ontológic", "léxic", "sintáctic",
    "axiomátic", "epistémic", "formal", "canónic", "atómic", "jerárquic",
    "imperativ", "recursiv", "determinist", "heurístic", "probabilístic",
    "estocástic", "categorial", "proposicional", "conjunctiv", "disyuntiv",
)


# ─────────────────────────────────────────────────────────────────────────────
# Patrones Regex para Fallback SNC
# ─────────────────────────────────────────────────────────────────────────────

# Patrón NOUN+ADJ: "procesamiento morfosintáctico", "grafo jerárquico"
PATTERN_NOUN_ADJ = re.compile(
    r'\b([A-Za-záéíóúüñÁÉÍÓÚÜÑ]{3,}(?:ción|ión|miento|idad|aje|ura|dad|ez|ismo|ista)?)'
    r'\s+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]{3,}(?:ico|ica|ional|ivo|iva|able|ible|ado|ada|oso|osa)?)\b',
    re.UNICODE
)

# Patrón NOUN+PREP+NOUN: "minería de datos", "árbol de dependencia"
PATTERN_NOUN_PREP_NOUN = re.compile(
    r'\b([A-Za-záéíóúüñÁÉÍÓÚÜÑ]{3,})\s+'
    r'(?:de(?:l)?|para|con|en|por|sobre)\s+'
    r'([A-Za-záéíóúüñÁÉÍÓÚÜÑ]{3,}(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{3,})?)\b',
    re.UNICODE
)

# Patrón imperativo [VERBO_INF + OBJETO]: "extraer candidatos", "normalizar formas"
PATTERN_IMPERATIVE = re.compile(
    r'\b(extraer|minar|filtrar|detectar|aislar|mapear|aplicar|ejecutar|balancear|'
    r'explorar|profundizar|verificar|normalizar|lematizar|resolver|desambiguar|'
    r'alinear|estructurar|implementar|confirmar|renderizar|transmutar|exportar|'
    r'generar|asignar|auditar|reparar|consolidar|validar|purgar|estandarizar|'
    r'sustituir|convertir|calcular|agrupar|cubrir|incluir|delimitar|desglosar|'
    r'formatear|confirmar)\s+'
    r'([A-Za-záéíóúüñÁÉÍÓÚÜÑ][A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]{2,40})',
    re.IGNORECASE | re.UNICODE
)


# ─────────────────────────────────────────────────────────────────────────────
# Intentar importar spaCy (opcional)
# ─────────────────────────────────────────────────────────────────────────────

try:
    import spacy
    _nlp = spacy.load("es_core_news_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    _nlp = None
    SPACY_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────────────────────────────────────

class MorphosyntacticFilter:
    """
    Fase 1: Extracción de Sintagmas Nominales Canónicos (SNC) y
    filtrado de ruido morfosintáctico.

    Formalmente:
        SNC ⊑ Sustantivo ⊓ ∃tieneAdjetivo.Especificador
    """

    def __init__(self, min_confidence: float = 0.5, lang: str = "es"):
        self.min_confidence = min_confidence
        self.lang = lang
        self._backend = "spacy" if SPACY_AVAILABLE else "regex"

    # ── API pública ──────────────────────────────────────────────────────────

    def extract_snc(self, corpus: str) -> Phase1Result:
        """
        Punto de entrada principal de Fase 1.
        Retorna Phase1Result con todas las unidades léxicas extraídas.
        """
        # Normalizar input
        cleaned = self._preprocess(corpus)

        # Eliminar modismos volátiles primero
        no_volatile = self._remove_volatile_idioms(cleaned)

        # Extraer SNC según backend disponible
        if SPACY_AVAILABLE and _nlp is not None:
            units = self._extract_spacy(no_volatile)
        else:
            units = self._extract_regex(no_volatile)

        # Filtrar por confianza mínima
        filtered = [u for u in units if u.confidence >= self.min_confidence]
        noise_count = len(units) - len(filtered)

        return Phase1Result(
            lexical_units=filtered,
            filtered_count=len(filtered),
            noise_removed=noise_count,
        )

    # ── Preprocesamiento ─────────────────────────────────────────────────────

    def _preprocess(self, text: str) -> str:
        """Normalización básica: espacios múltiples, puntuación residual."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-áéíóúüñÁÉÍÓÚÜÑ()[\]{}.,;:!?]', '', text, flags=re.UNICODE)
        return text.strip()

    def _remove_volatile_idioms(self, text: str) -> str:
        """Purga modismos contextuales sin valor técnico."""
        for idiom in VOLATILE_IDIOMS:
            pattern = re.compile(re.escape(idiom), re.IGNORECASE)
            text = pattern.sub(' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    # ── Backend spaCy ────────────────────────────────────────────────────────

    def _extract_spacy(self, text: str) -> list[LexicalUnit]:
        """
        Extracción via spaCy: POS tagging + dependency trees.
        Detecta chunks nominales nativos del parser.
        """
        doc = _nlp(text)
        units: list[LexicalUnit] = []
        seen: set[str] = set()

        for chunk in doc.noun_chunks:
            surface = chunk.text.strip().lower()
            if surface in seen or self._is_stopword_only(surface):
                continue
            seen.add(surface)

            pos_tags = [t.pos_ for t in chunk]
            dep_labels = [t.dep_ for t in chunk]
            pattern = self._classify_pattern_spacy(chunk)
            confidence = self._compute_confidence_spacy(chunk)

            units.append(LexicalUnit(
                surface_form=surface,
                pattern=pattern,
                pos_tags=pos_tags,
                dependency_labels=dep_labels,
                confidence=confidence,
                source_position=chunk.start_char,
            ))

        # Añadir frases imperativas detectadas
        units.extend(self._extract_imperatives_regex(text, seen))
        return units

    def _classify_pattern_spacy(self, chunk) -> SyntacticPattern:
        """Clasifica el patrón POS de un noun_chunk de spaCy."""
        pos_seq = [t.pos_ for t in chunk]
        if "NOUN" in pos_seq and "ADJ" in pos_seq:
            return SyntacticPattern.NOUN_ADJ
        elif "ADP" in pos_seq:
            return SyntacticPattern.NOUN_PREP_NOUN
        return SyntacticPattern.UNKNOWN

    def _compute_confidence_spacy(self, chunk) -> float:
        """Heurística: mayor longitud + presencia de términos técnicos → mayor confianza."""
        base = min(len(chunk) / 5.0, 1.0)
        text_lower = chunk.text.lower()
        boost = 0.2 if any(text_lower.startswith(p) for p in TECHNICAL_ADJ_PREFIXES) else 0.0
        return min(base + boost, 1.0)

    # ── Backend Regex (fallback) ──────────────────────────────────────────────

    def _extract_regex(self, text: str) -> list[LexicalUnit]:
        """
        Extracción regex pura — activa cuando spaCy no está disponible.
        Detecta patrones NOUN+ADJ, NOUN+PREP+NOUN e imperativos.
        """
        units: list[LexicalUnit] = []
        seen: set[str] = set()

        # Patrón NOUN+PREP+NOUN (mayor prioridad — más específico)
        for m in PATTERN_NOUN_PREP_NOUN.finditer(text):
            surface = m.group(0).strip().lower()
            if surface not in seen and not self._is_stopword_only(surface):
                seen.add(surface)
                units.append(LexicalUnit(
                    surface_form=surface,
                    pattern=SyntacticPattern.NOUN_PREP_NOUN,
                    confidence=self._regex_confidence(surface),
                    source_position=m.start(),
                ))

        # Patrón NOUN+ADJ
        for m in PATTERN_NOUN_ADJ.finditer(text):
            surface = m.group(0).strip().lower()
            n1, n2 = m.group(1).lower(), m.group(2).lower()
            if (surface not in seen
                    and n1 not in STOPWORDS_ES
                    and n2 not in STOPWORDS_ES
                    and not self._is_stopword_only(surface)):
                seen.add(surface)
                units.append(LexicalUnit(
                    surface_form=surface,
                    pattern=SyntacticPattern.NOUN_ADJ,
                    confidence=self._regex_confidence(surface),
                    source_position=m.start(),
                ))

        # Frases imperativas
        units.extend(self._extract_imperatives_regex(text, seen))
        return units

    def _extract_imperatives_regex(self, text: str, seen: set[str]) -> list[LexicalUnit]:
        """Extrae frases imperativas [VERBO_INF + OBJETO]."""
        units = []
        for m in PATTERN_IMPERATIVE.finditer(text):
            surface = m.group(0).strip().lower()
            obj_part = m.group(2).strip()
            # Limitar a 5 palabras máx
            words = obj_part.split()[:5]
            surface = m.group(1).lower() + " " + " ".join(words)
            if surface not in seen:
                seen.add(surface)
                units.append(LexicalUnit(
                    surface_form=surface,
                    pattern=SyntacticPattern.VERB_NOUN,
                    confidence=0.85,
                    source_position=m.start(),
                ))
        return units

    # ── Utilidades ───────────────────────────────────────────────────────────

    def _is_stopword_only(self, text: str) -> bool:
        """Retorna True si el sintagma solo contiene stopwords."""
        words = text.lower().split()
        return all(w in STOPWORDS_ES for w in words)

    def _regex_confidence(self, surface: str) -> float:
        """Heurística de confianza para extracción regex."""
        words = surface.split()
        if len(words) < 2:
            return 0.4
        technical_boost = 0.2 if any(
            w.startswith(p) for w in words for p in TECHNICAL_ADJ_PREFIXES
        ) else 0.0
        length_score = min(len(words) / 4.0, 0.8)
        return min(length_score + technical_boost, 1.0)
