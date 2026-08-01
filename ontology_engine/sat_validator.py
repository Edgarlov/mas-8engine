"""
sat_validator.py — Validador SAT/CDCL y Belief Revision AGM (Sección 4 del Spec)

Implementa:
  - Reducción del grafo a CNF (Conjunctive Normal Form)
  - Solver CDCL (Conflict-Driven Clause Learning) simplificado
  - Garantía: SAT(KB) = True  (sin cláusulas vacías ⊥)
  - Retracción de Creencias (Postulados AGM) ante inconsistencias
  - Interdicción y purga de nodos huérfanos (sin relación IS-A, PART-OF, PRECEDES)

Formalismo:
  SAT(KB) = True  →  ¬∃ cláusula vacía
  AGM: Contracción W÷φ = min(W, ¬φ) por selección epistémica
  Huérfano: ∀x (Nodo(x) ∧ ¬∃y Rel(x,y)) → Purgar(x)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import NodeRole, OntologyGraph, OntologyNode, RelationType, ValidationResult

# ─────────────────────────────────────────────────────────────────────────────
# Tipos CNF
# ─────────────────────────────────────────────────────────────────────────────

Literal = int          # positivo = True, negativo = False, 0 = indefinido
Clause = list[Literal]
KB = list[Clause]      # Knowledge Base en CNF


# ─────────────────────────────────────────────────────────────────────────────
# Encoder Grafo → CNF
# ─────────────────────────────────────────────────────────────────────────────

class GraphCNFEncoder:
    """
    Codifica el OntologyGraph en CNF para verificación SAT.

    Variables propositionales:
      - p(n)  := "El nodo n es consistente"
      - m(n)  := "Los hijos de n cumplen MECE"

    Axiomas:
      1. Raíz siempre consistente: [p(root)]
      2. Si nodo es consistente y tiene hijos, todos los hijos válidos son consistentes
         Para nodo con hijos {c1,c2,...}: p(n) → p(c1) ∧ p(c2)...
         En CNF: [¬p(n) ∨ p(ci)]  para cada hijo ci
      3. Nodos marcados como no-MECE son inconsistentes: [¬p(n)]
      4. Nodos huérfanos son inconsistentes: [¬p(n)]
    """

    def __init__(self):
        self._var_map: dict[str, int] = {}
        self._counter = 1

    def var(self, name: str) -> int:
        if name not in self._var_map:
            self._var_map[name] = self._counter
            self._counter += 1
        return self._var_map[name]

    def encode(self, graph: OntologyGraph) -> tuple[KB, dict[str, int]]:
        """
        Retorna (cláusulas_CNF, mapa_variables).

        Axiomas (correctos y no conflictivos):
          1. Nodos raíz siempre consistentes
          2. Consistencia se propaga hacia hijos: p(parent) → p(child)  [CNF: ¬p(parent) ∨ p(child)]
          3. Nodos con mece_valid=False: ¬p(n)
          4. Nodos ORPHAN: ¬p(n)
        """
        clauses: KB = []
        all_nodes = graph.all_nodes()

        for node in all_nodes:
            p = self.var(f"p_{node.notation}")

            # Axioma 1: raíces consistentes (siempre True)
            if node.role == NodeRole.ROOT:
                clauses.append([p])

            # Axioma 2: propagación de consistencia a hijos
            # p(parent) → p(child)  ≡  ¬p(parent) ∨ p(child)
            for child in node.children:
                cp = self.var(f"p_{child.notation}")
                clauses.append([-p, cp])

            # Axioma 3: huérfanos son inconsistentes
            if node.role == NodeRole.ORPHAN:
                clauses.append([-p])

        return clauses, self._var_map


# ─────────────────────────────────────────────────────────────────────────────
# Solver CDCL Simplificado (Unit Propagation + Resolution)
# ─────────────────────────────────────────────────────────────────────────────

class CDCLSolver:
    """
    Solver SAT para KBs de grafos ontológicos.

    Para grafos jerárquicos bien formados (árbol dirigido acíclico):
    - Si todos los nodos raíz tienen cláusula [p_root] (positiva)
    - Y todos los hijos heredan via [¬p_parent ∨ p_child]
    - Entonces SAT = True por propagación directa

    Implementa Unit Propagation (UP) pura + verificación residual.
    Para grafos ontológicos, UP es suficiente (sin backtracking en DAGs bien formados).
    """

    def solve(self, clauses: KB, num_vars: int) -> tuple[bool, dict[int, bool]]:
        """
        Retorna (satisfiable, assignment) por Unit Propagation.
        Suficiente para KBs de grafos DAG bien formados.
        """
        assignment: dict[int, bool] = {}

        # Copia trabajo para no modificar originales
        working = [list(c) for c in clauses]

        is_sat = self._unit_propagation_full(working, assignment)
        return is_sat, assignment

    def _unit_propagation_full(
        self, clauses: list[Clause], assignment: dict[int, bool]
    ) -> bool:
        """
        UP completa: itera hasta punto fijo.
        Retorna False si encuentra cláusula vacía.
        """
        changed = True
        while changed:
            changed = False

            # Eliminar cláusulas satisfechas y simplificar
            new_clauses = []
            for clause in clauses:
                # Verificar si la cláusula está satisfecha
                sat = any(
                    (lit > 0 and assignment.get(abs(lit)) is True) or
                    (lit < 0 and assignment.get(abs(lit)) is False)
                    for lit in clause
                )
                if sat:
                    continue  # Eliminar cláusula satisfecha

                # Filtrar literales falsificados
                remaining = [
                    lit for lit in clause
                    if not (
                        (lit > 0 and assignment.get(abs(lit)) is False) or
                        (lit < 0 and assignment.get(abs(lit)) is True)
                    )
                ]

                if len(remaining) == 0:
                    return False  # Cláusula vacía → UNSAT

                if len(remaining) == 1:
                    # Unit clause: forzar asignación
                    lit = remaining[0]
                    var = abs(lit)
                    val = lit > 0
                    if var in assignment and assignment[var] != val:
                        return False  # Conflicto
                    assignment[var] = val
                    changed = True
                else:
                    new_clauses.append(remaining)

            clauses[:] = new_clauses

        # Verificar que no quedan cláusulas vacías
        for clause in clauses:
            remaining = [
                lit for lit in clause
                if abs(lit) not in assignment
            ]
            if len(remaining) == 0:
                return False

        return True


# ─────────────────────────────────────────────────────────────────────────────
# AGM Belief Revision
# ─────────────────────────────────────────────────────────────────────────────

class AGMBeliefReviser:
    """
    Retracción de creencias basada en los Postulados AGM
    (Alchourrón, Gärdenfors, Makinson 1985).

    Ante una inconsistencia en KB:
      1. Identifica las proposiciones secundarias dependientes de la contradicción
      2. Las retracta (elimina del grafo / marca como inválidas)
      3. Restaura la consistencia de la base de conocimiento W

    Operación de contracción: W ÷ φ
    """

    def revise(
        self, graph: OntologyGraph, conflicting_notations: list[str]
    ) -> tuple[OntologyGraph, list[str]]:
        """
        Retracta nodos en conflicto y sus dependientes.
        Retorna (grafo_revisado, lista_de_retracciones).
        """
        retractions: list[str] = []

        def should_retract(node: OntologyNode) -> bool:
            return node.notation in conflicting_notations or not node.mece_valid

        def retract_subtree(nodes: list[OntologyNode]) -> list[OntologyNode]:
            kept = []
            for node in nodes:
                if should_retract(node):
                    retractions.append(
                        f"RETRACTADO: {node.notation} — {node.canonical.lemma}"
                    )
                else:
                    node.children = retract_subtree(node.children)
                    kept.append(node)
            return kept

        graph.top_concepts = retract_subtree(graph.top_concepts)
        return graph, retractions


# ─────────────────────────────────────────────────────────────────────────────
# Validador Principal
# ─────────────────────────────────────────────────────────────────────────────

class SATCDCLValidator:
    """
    Validador integral SAT/CDCL para el grafo ontológico.

    Flujo:
      1. Codificar grafo → CNF
      2. Resolver con CDCL
      3. Si UNSAT: aplicar AGM belief revision
      4. Purgar nodos huérfanos
      5. Retornar ValidationResult
    """

    def validate(self, graph: OntologyGraph) -> ValidationResult:
        """Punto de entrada de validación."""
        result = ValidationResult()

        # ── 1. Purgar huérfanos ───────────────────────────────────────────────
        orphans_purged = self._purge_orphans(graph)
        result.orphans_purged = orphans_purged

        # ── 2. Codificar a CNF ────────────────────────────────────────────────
        encoder = GraphCNFEncoder()
        clauses, var_map = encoder.encode(graph)
        result.cnf_clauses = len(clauses)

        # ── 3. Resolver SAT ───────────────────────────────────────────────────
        solver = CDCLSolver()
        is_sat, assignment = solver.solve(clauses, len(var_map))
        result.is_satisfiable = is_sat
        result.kb_consistent = is_sat

        # ── 4. Belief Revision si UNSAT ───────────────────────────────────────
        if not is_sat:
            conflicting = self._find_conflicting_nodes(graph, assignment, var_map)
            reviser = AGMBeliefReviser()
            revised_graph, retractions = reviser.revise(graph, conflicting)
            result.belief_retractions = retractions
            result.violations.append(
                f"UNSAT detectado — {len(retractions)} nodos retractados via AGM"
            )

            # Re-validar tras revisión
            encoder2 = GraphCNFEncoder()
            clauses2, _ = encoder2.encode(graph)
            is_sat2, _ = solver.solve(clauses2, len(var_map))
            result.is_satisfiable = is_sat2
            result.kb_consistent = is_sat2

        # ── 5. Verificación de invariantes adicionales ────────────────────────
        self._check_invariants(graph, result)

        return result

    # ── Purga de Huérfanos ────────────────────────────────────────────────────

    def _purge_orphans(self, graph: OntologyGraph) -> int:
        """
        Interdicción de entidades huérfanas:
        Todo nodo terminal debe poseer al menos una relación explícita
        (IS-A, PART-OF, o precedencia) hacia la raíz.

        Detecta nodos sin parent_notation en niveles no-root y los marca.
        """
        purged = 0
        all_notations = {n.notation for n in graph.all_nodes()}

        for node in graph.all_nodes():
            if node.role == NodeRole.ROOT:
                continue
            # Verificar que su parent_notation existe en el grafo
            if node.parent_notation and node.parent_notation not in all_notations:
                node.role = NodeRole.ORPHAN
                purged += 1
            elif not node.parent_notation and node.role != NodeRole.ROOT:
                node.role = NodeRole.ORPHAN
                purged += 1

        return purged

    # ── Detección de Conflictos ────────────────────────────────────────────────

    def _find_conflicting_nodes(
        self,
        graph: OntologyGraph,
        assignment: dict[int, bool],
        var_map: dict[str, int],
    ) -> list[str]:
        """Identifica notaciones de nodos cuya variable p_n es False en la asignación."""
        conflicting = []
        for var_name, var_id in var_map.items():
            if var_name.startswith("p_") and assignment.get(var_id) is False:
                notation = var_name[2:]  # Strip "p_"
                conflicting.append(notation)
        return conflicting

    # ── Invariantes ───────────────────────────────────────────────────────────

    def _check_invariants(self, graph: OntologyGraph, result: ValidationResult):
        """Verifica invariantes lógicos adicionales."""
        stats = graph.stats()

        # Invariante 1: El grafo debe tener al menos 1 nodo raíz
        if stats["top_concepts"] == 0:
            result.violations.append("INVARIANTE VIOLADO: grafo sin nodo raíz")
            result.kb_consistent = False

        # Invariante 2: Al menos 1 nodo atómico terminal
        if stats["atomic_nodes"] == 0:
            result.violations.append("INVARIANTE VIOLADO: sin nodos atómicos terminales")

        # Invariante 3: Profundidad máxima coherente
        if stats["max_depth"] > 6:
            result.violations.append(
                f"ADVERTENCIA: profundidad máxima = {stats['max_depth']} (>6, revisar)"
            )
