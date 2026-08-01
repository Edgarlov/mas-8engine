from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Tuple

from core.schemas import RDFTriple, NormalizationResult


class ISO704Normalizer:
    """
    Normalizador bajo principios ISO 704.
    Realiza limpieza de texto, etiquetado POS y extracción de triples RDF (SVO).
    """

    def __init__(self) -> None:
        self._nltk_available = False
        try:
            import nltk
            import nltk.data
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger_eng')
            except LookupError:
                nltk.download('averaged_perceptron_tagger_eng', quiet=True)
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                nltk.download('punkt_tab', quiet=True)
            self._nltk_available = True
        except ImportError:
            self._nltk_available = False

    def clean_utf8(self, text: str) -> str:
        """
        Normaliza Unicode (NFC), remueve caracteres de control y colapsa espacios.
        """
        text = unicodedata.normalize('NFC', text)
        # Remueve caracteres de control excepto nueva línea y tabulación
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _fallback_pos_tag(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """
        Etiquetador POS simple basado en expresiones regulares (fallback).
        """
        tags = []
        for token in tokens:
            lower = token.lower()
            if re.match(r'^[A-Z]', token) or token.endswith(('ion', 'ment', 'ity', 'ness')):
                tags.append((token, 'NN'))
            elif lower.endswith(('ar', 'er', 'ir', 'ate', 'ize', 'ify', 'en')):
                tags.append((token, 'VB'))
            elif lower.endswith(('al', 'ive', 'ous', 'ble', 'ic', 'ish', 'y')):
                tags.append((token, 'JJ'))
            elif lower.endswith(('ly')):
                tags.append((token, 'RB'))
            else:
                tags.append((token, 'NN'))
        return tags

    def normalize_text(self, raw_text: str) -> NormalizationResult:
        """
        Ejecuta la limpieza UTF-8, etiquetado POS y extracción de NPs y Triples RDF.
        """
        cleaned_text = self.clean_utf8(raw_text)
        
        if self._nltk_available:
            import nltk
            tokens = nltk.word_tokenize(cleaned_text)
            pos_tags = nltk.pos_tag(tokens)
        else:
            tokens = re.findall(r'\b\w+\b', cleaned_text)
            pos_tags = self._fallback_pos_tag(tokens)

        # Extracción de Noun Phrases (NP)
        noun_phrases = []
        current_np = []
        
        for i, (word, tag) in enumerate(pos_tags):
            if tag.startswith('JJ') or tag.startswith('NN'):
                current_np.append(word)
            else:
                if current_np and i > 0 and pos_tags[i - 1][1].startswith('NN'):
                    noun_phrases.append(" ".join(current_np))
                current_np = []
                
        if current_np and pos_tags[-1][1].startswith('NN'):
            noun_phrases.append(" ".join(current_np))

        triples = self.extract_triples(pos_tags)

        return NormalizationResult(
            original_text=raw_text,
            cleaned_text=cleaned_text,
            pos_tags=pos_tags,
            noun_phrases=noun_phrases,
            triples=triples
        )

    def extract_triples(self, pos_tags: List[Tuple[str, str]]) -> List[RDFTriple]:
        """
        Extrae patrones Sujeto-Verbo-Objeto (SVO) de secuencias de etiquetas POS.
        """
        triples: List[RDFTriple] = []
        subject_parts = []
        verb_part = ""
        object_parts = []
        
        state = 0  # 0: sujeto, 1: verbo, 2: objeto

        for word, tag in pos_tags:
            if state == 0:
                if tag.startswith('NN') or tag.startswith('JJ'):
                    subject_parts.append(word)
                elif tag.startswith('VB') and subject_parts:
                    verb_part = word
                    state = 1
            elif state == 1:
                if tag.startswith('NN') or tag.startswith('JJ'):
                    object_parts.append(word)
                    state = 2
                elif tag.startswith('VB'):
                    verb_part = word
            elif state == 2:
                if tag.startswith('NN') or tag.startswith('JJ'):
                    object_parts.append(word)
                else:
                    if subject_parts and verb_part and object_parts:
                        triples.append(RDFTriple(
                            subject=" ".join(subject_parts),
                            predicate=verb_part,
                            object=" ".join(object_parts)
                        ))
                    subject_parts = []
                    verb_part = ""
                    object_parts = []
                    state = 0
                    
        if subject_parts and verb_part and object_parts:
             triples.append(RDFTriple(
                 subject=" ".join(subject_parts),
                 predicate=verb_part,
                 object=" ".join(object_parts)
             ))

        return triples
