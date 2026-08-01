"""
MAS-8ENGINE │ c_value_extractor.py
Extractor de Términos Multigramas mediante la métrica C-Value.
Extraído de las taxonomías de Extractología y Minería Léxica.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Tuple
from pydantic import BaseModel


class ExtractedTerm(BaseModel):
    term: str
    word_count: int
    frequency: int
    c_value: float


class CValueExtractor:
    """Extractor de candidatos a términos ontológicos usando la métrica C-Value."""

    @staticmethod
    def extract_candidates(text: str, max_ngram: int = 4) -> Dict[str, int]:
        # Preprocesamiento léxico básico
        clean_text = re.sub(r'[^\w\s-]', ' ', text.lower())
        words = [w for w in clean_text.split() if len(w) > 2]
        
        candidates = Counter()
        n = len(words)
        
        for length in range(2, max_ngram + 1):
            for i in range(n - length + 1):
                ngram = " ".join(words[i:i + length])
                candidates[ngram] += 1
                
        return dict(candidates)

    @classmethod
    def compute_c_values(cls, text: str, min_freq: int = 1) -> List[ExtractedTerm]:
        candidate_freqs = cls.extract_candidates(text)
        if not candidate_freqs:
            return []

        # Ordenar n-gramas por longitud descendente
        sorted_candidates = sorted(candidate_freqs.keys(), key=lambda x: len(x.split()), reverse=True)
        
        c_values: Dict[str, float] = {}
        nested_freqs: Dict[str, List[int]] = {c: [] for c in sorted_candidates}
        nested_counts: Dict[str, int] = {c: 0 for c in sorted_candidates}

        for candidate in sorted_candidates:
            words = candidate.split()
            length = len(words)
            freq = candidate_freqs[candidate]
            
            if freq < min_freq:
                continue

            # Métrica C-Value:
            # Si el término no es subcadena de términos más largos: C-Value = log2(|a|) * freq(a)
            # Si es subcadena: C-Value = log2(|a|) * (freq(a) - 1/P(T_a) * sum(freq(b)))
            count_b = nested_counts[candidate]
            sum_freq_b = sum(nested_freqs[candidate])
            
            if count_b == 0:
                c_val = math.log2(length) * freq
            else:
                c_val = math.log2(length) * (freq - (1.0 / count_b) * sum_freq_b)

            c_values[candidate] = max(0.0, c_val)

            # Registrar como subcadena en candidatos de menor longitud
            for other in sorted_candidates:
                if len(other.split()) < length and candidate in other:
                    nested_freqs[other].append(freq)
                    nested_counts[other] += 1

        results = [
            ExtractedTerm(
                term=term,
                word_count=len(term.split()),
                frequency=candidate_freqs[term],
                c_value=round(val, 4)
            )
            for term, val in c_values.items()
        ]

        # Ordenar por C-Value descendente
        results.sort(key=lambda x: x.c_value, reverse=True)
        return results
