from __future__ import annotations
from typing import List, Tuple

from core.schemas import BayesianPrior, BayesianResult, FuzzySet

class UncertaintyEngine:
    """Motor de incertidumbre que integra inferencia bayesiana y lógica difusa."""

    def update_bayes(self, prior: BayesianPrior) -> BayesianResult:
        """
        Computa P(H|E) = P(E|H)*P(H) / [P(E|H)*P(H) + P(E|¬H)*(1-P(H))]
        """
        evidence_total = prior.likelihood * prior.prior_prob + prior.evidence_given_not_h * (1.0 - prior.prior_prob)
        if evidence_total == 0.0:
            raise ValueError(f"Total evidence probability is zero for hypothesis: {prior.hypothesis}")
            
        posterior = (prior.likelihood * prior.prior_prob) / evidence_total
        
        return BayesianResult(
            hypothesis=prior.hypothesis,
            prior=prior.prior_prob,
            likelihood=prior.likelihood,
            evidence_given_not_h=prior.evidence_given_not_h,
            posterior=posterior,
            evidence_total=evidence_total
        )

    def batch_update_bayes(self, priors: List[BayesianPrior]) -> List[BayesianResult]:
        """Procesa múltiples hipótesis devolviendo la lista de resultados."""
        return [self.update_bayes(prior) for prior in priors]

    def defuzzify_centroid(self, memberships: List[Tuple[float, float]]) -> float:
        """
        Defusificación por Centroide (CoG).
        Cada tupla es (membership_degree, crisp_value).
        CoG = sum(μ(z)*z) / sum(μ(z))
        """
        numerator = sum(mu * z for mu, z in memberships)
        denominator = sum(mu for mu, z in memberships)
        
        if denominator == 0.0:
            raise ValueError("Sum of membership degrees is zero; cannot compute centroid.")
            
        return numerator / denominator

    def fuzzify(self, value: float, sets: List[FuzzySet]) -> List[FuzzySet]:
        """
        Dado un valor nítido (crisp value) y un conjunto de definiciones difusas, 
        recalcula el grado de pertenencia usando una función de pertenencia triangular.
        Se asume que el `crisp_value` original del FuzzySet actúa como el pico.
        """
        # Calcular dinámicamente un ancho de base razonable basado en la distribución de picos
        if len(sets) > 1:
            peaks = sorted([s.crisp_value for s in sets])
            # La distancia promedio entre picos sirve como el semiancho de la base
            width = sum(peaks[i+1] - peaks[i] for i in range(len(peaks)-1)) / (len(peaks) - 1)
            width = max(width, 1e-9)
        else:
            width = 1.0

        updated_sets = []
        for s in sets:
            # Triangular membership degree
            distance = abs(value - s.crisp_value)
            membership = max(0.0, 1.0 - (distance / width))
            
            # Create a new FuzzySet with the updated membership_degree
            updated_sets.append(FuzzySet(
                variable_name=s.variable_name,
                crisp_value=s.crisp_value,
                membership_degree=membership,
                label=s.label
            ))
            
        return updated_sets

    def evaluate_fuzzy_rules(self, antecedents: List[float], consequent_range: List[Tuple[float, float]]) -> float:
        """
        Toma las fuerzas de las reglas disparadas (antecedentes) y pares (membership, crisp_value)
        del consecuente. Recorta cada consecuente por su fuerza antecedente (Mamdani) y defusifica.
        """
        if len(antecedents) != len(consequent_range):
            raise ValueError("Mismatch between number of antecedents and consequents.")
            
        clipped_memberships = []
        for antecedent_strength, (cons_membership, crisp_value) in zip(antecedents, consequent_range):
            clipped_mu = min(antecedent_strength, cons_membership)
            clipped_memberships.append((clipped_mu, crisp_value))
            
        return self.defuzzify_centroid(clipped_memberships)
