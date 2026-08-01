"""
ontology_agent.py — Agente CLI Interactivo del Engine Ontológico v2.0

Proporciona una interfaz de línea de comandos enriquecida para:
  - Procesar corpus arbitrarios a través del pipeline completo
  - Explorar el grafo imperativo interactivamente
  - Exportar en múltiples formatos (JSON-LD, Turtle, árbol ASCII, lista plana)
  - Ejecutar validación SAT/CDCL sobre esquemas existentes
  - Servir el frontend web (cuando se solicita)

Comandos:
  ontology process <corpus>     → pipeline completo
  ontology tree                 → árbol imperativo del spec
  ontology export --format      → exportación
  ontology validate <file>      → validación SAT/CDCL
  ontology serve                → servidor web local
  ontology interactive          → REPL interactivo
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

# Añadir el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ontology_engine import OntologyEnginePipeline, PipelineConfig

# ─────────────────────────────────────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────────────────────────────────────

class C:
    """ANSI color codes."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    PURPLE  = "\033[35m"
    CYAN    = "\033[36m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    RED     = "\033[31m"
    BLUE    = "\033[34m"
    WHITE   = "\033[37m"
    BG_DARK = "\033[48;5;17m"

    @staticmethod
    def header(text: str) -> str:
        return f"{C.BOLD}{C.PURPLE}{text}{C.RESET}"

    @staticmethod
    def success(text: str) -> str:
        return f"{C.BOLD}{C.GREEN}✓ {text}{C.RESET}"

    @staticmethod
    def error(text: str) -> str:
        return f"{C.BOLD}{C.RED}✗ {text}{C.RESET}"

    @staticmethod
    def warn(text: str) -> str:
        return f"{C.YELLOW}⚠  {text}{C.RESET}"

    @staticmethod
    def info(text: str) -> str:
        return f"{C.CYAN}ℹ  {text}{C.RESET}"

    @staticmethod
    def phase(n: int, text: str) -> str:
        colors = ["", C.BLUE, C.PURPLE, C.CYAN, C.GREEN]
        color = colors[min(n, 4)]
        return f"{color}{C.BOLD}[P{n}]{C.RESET} {text}"


# ─────────────────────────────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────────────────────────────

BANNER = f"""
{C.PURPLE}{C.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║      ONTOLOGY ENGINE v2.0 — Motor de Ingeniería Ontológica      ║
║      Minería Léxica de Resolución Atómica · MECE · SAT/CDCL     ║
╚══════════════════════════════════════════════════════════════════╝{C.RESET}
{C.DIM}  Basado en: ESPECIFICACION_INGENIERIA_ONTOLOGICA.md v2.0
  4 Fases: Filtrado Morfosintáctico → BFS Clustering → Canonicalización → Grafo Imperativo{C.RESET}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Clase Agente
# ─────────────────────────────────────────────────────────────────────────────

class OntologyAgent:
    """Agente CLI interactivo para el Engine Ontológico v2.0."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig(verbose=True)
        self.pipeline = OntologyEnginePipeline(self.config)
        self._last_result = None

    # ── Comandos principales ─────────────────────────────────────────────────

    def cmd_process(self, corpus: str, output_format: str = "tree") -> None:
        """Procesa un corpus y muestra los resultados."""
        if not corpus.strip():
            print(C.error("Corpus vacío. Proporciona texto de entrada."))
            return

        print(C.header("\n⚡ EJECUTANDO PIPELINE v2.0"))
        print(f"{C.DIM}  Corpus: {corpus[:80]}...{C.RESET}\n")

        result = self.pipeline.process(corpus)
        self._last_result = result

        # Mostrar estadísticas por fase
        self._print_phase_stats(result)

        # Mostrar resultado según formato
        print(C.header("\n📊 RESULTADO:"))
        if output_format == "tree":
            print(f"\n{result.tree_render}\n")
        elif output_format == "jsonld":
            print(json.dumps(result.jsonld_export, ensure_ascii=False, indent=2))
        elif output_format == "summary":
            print(f"\n  {result.summary()}\n")

        # SAT/CDCL status
        v = result.validation
        status = C.success("SATISFIABLE") if v.is_satisfiable else C.error("UNSAT")
        print(f"\n{C.header('🔐 VALIDACIÓN SAT/CDCL:')} {status}")
        print(f"  CNF cláusulas: {v.cnf_clauses}")
        print(f"  Huérfanos purgados: {v.orphans_purged}")
        if v.violations:
            for viol in v.violations:
                print(C.warn(f"  {viol}"))
        if v.belief_retractions:
            print(C.info("  Retracciones AGM:"))
            for r in v.belief_retractions:
                print(f"    {C.DIM}{r}{C.RESET}")

        # MECE
        mece_viols = result.phase4.mece_violations
        if mece_viols:
            print(f"\n{C.header('⚖  MECE Violations:')} {C.warn(str(len(mece_viols)))}")
            for mv in mece_viols[:5]:
                print(f"  {C.DIM}{mv}{C.RESET}")
        else:
            print(f"\n{C.success('MECE compliant — sin violaciones detectadas')}")

        print(f"\n{C.DIM}  Tiempo total: {result.processing_time_ms:.1f}ms{C.RESET}")

    def cmd_tree(self, use_imperative: bool = True) -> None:
        """Muestra el árbol imperativo del spec."""
        print(C.header("\n🌳 ÁRBOL IMPERATIVO NORMALIZADO (SPEC v2.0)"))
        result = self.pipeline.get_spec_graph()
        print(f"\n{result.tree_render}\n")
        stats = result.phase4.graph.stats()
        print(f"  Nodos totales:  {stats['total_nodes']}")
        print(f"  Nodos atómicos: {stats['atomic_nodes']}")
        print(f"  Profundidad max: {stats['max_depth']}")
        print(f"  Ramas raíz:    {stats['top_concepts']}")

    def cmd_export(self, fmt: str = "jsonld", output_file: Optional[str] = None) -> None:
        """Exporta el grafo en el formato especificado."""
        if self._last_result is None:
            result = self.pipeline.get_spec_graph()
        else:
            result = self._last_result

        content = self.pipeline.export_format(result, fmt)

        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(content, encoding="utf-8")
            print(C.success(f"Exportado a: {output_file}"))
        else:
            print(content)

    def cmd_validate(self, json_file: str) -> None:
        """Valida un archivo JSON-LD existente."""
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(C.error(f"Archivo no encontrado: {json_file}"))
            return
        except json.JSONDecodeError as e:
            print(C.error(f"JSON inválido: {e}"))
            return

        result = self.pipeline.validate_only(data)
        status = C.success("SATISFIABLE") if result["is_satisfiable"] else C.error("UNSAT")
        print(C.header("\n🔐 Resultado de Validación SAT/CDCL"))
        print(f"  Estado KB:      {status}")
        print(f"  CNF cláusulas:  {result['cnf_clauses']}")
        print(f"  Huérfanos:      {result['orphans_purged']}")
        if result["violations"]:
            print(C.warn("  Violaciones:"))
            for v in result["violations"]:
                print(f"    {v}")

    def cmd_serve(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        """Inicia servidor web local para el frontend."""
        try:
            self._start_server(host, port)
        except KeyboardInterrupt:
            print(C.info("\nServidor detenido."))

    def cmd_interactive(self) -> None:
        """REPL interactivo."""
        print(BANNER)
        print(C.info("Modo interactivo. Escribe 'help' para ver comandos, 'exit' para salir.\n"))

        while True:
            try:
                user_input = input(f"{C.PURPLE}ontology>{C.RESET} ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not user_input:
                continue

            parts = user_input.split(None, 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd in ("exit", "quit", "q"):
                print(C.info("Hasta luego."))
                break
            elif cmd == "help":
                self._print_help()
            elif cmd == "tree":
                self.cmd_tree()
            elif cmd == "process":
                if args:
                    self.cmd_process(args)
                else:
                    corpus = self._get_multiline_input()
                    self.cmd_process(corpus)
            elif cmd == "export":
                fmt = args if args in ("jsonld", "turtle", "tree", "flat") else "jsonld"
                self.cmd_export(fmt)
            elif cmd == "validate":
                self.cmd_validate(args)
            elif cmd == "stats":
                self._print_stats()
            elif cmd == "demo":
                self.cmd_process(DEMO_CORPUS)
            elif cmd == "serve":
                self.cmd_serve()
            else:
                print(C.warn(f"Comando desconocido: '{cmd}'. Escribe 'help'."))

    # ── Servidor Web ─────────────────────────────────────────────────────────

    def _start_server(self, host: str, port: int) -> None:
        """Servidor HTTP simple para el frontend web."""
        import http.server
        import socketserver
        import urllib.parse

        web_dir = Path(__file__).parent / "web_interface"
        agent = self

        class OntologyHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(web_dir), **kwargs)

            def do_POST(self):
                if self.path == "/api/process":
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    try:
                        payload = json.loads(body.decode("utf-8"))
                        corpus = payload.get("corpus", "")
                        fmt = payload.get("format", "jsonld")

                        result = agent.pipeline.process(corpus)
                        response = {
                            "tree": result.tree_render,
                            "jsonld": result.jsonld_export,
                            "flat": agent.pipeline.exporter.to_flat_list(result.phase4.graph),
                            "stats": result.phase4.graph.stats(),
                            "validation": {
                                "is_satisfiable": result.validation.is_satisfiable,
                                "kb_consistent": result.validation.kb_consistent,
                                "orphans_purged": result.validation.orphans_purged,
                                "cnf_clauses": result.validation.cnf_clauses,
                                "violations": result.validation.violations,
                            },
                            "mece_violations": result.phase4.mece_violations,
                            "summary": result.summary(),
                            "phases": {
                                "p1": {"extracted": result.phase1.filtered_count, "noise_removed": result.phase1.noise_removed},
                                "p2": {"clusters": len(result.phase2.clusters), "tau": result.phase2.tau_threshold},
                                "p3": {"canonical_forms": len(result.phase3.canonical_forms), "polysemous": result.phase3.polysemous_count},
                                "p4": {"nodes": result.phase4.graph.stats()["total_nodes"], "violations": len(result.phase4.mece_violations)},
                            },
                            "processing_time_ms": result.processing_time_ms,
                        }
                    except Exception as e:
                        response = {"error": str(e)}

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

                elif self.path == "/api/spec":
                    result = agent.pipeline.get_spec_graph()
                    response = {
                        "tree": result.tree_render,
                        "jsonld": result.jsonld_export,
                        "flat": agent.pipeline.exporter.to_flat_list(result.phase4.graph),
                        "stats": result.phase4.graph.stats(),
                    }
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_error(404)

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def log_message(self, format, *args):
                pass  # Silenciar logs HTTP

        with socketserver.TCPServer((host, port), OntologyHandler) as httpd:
            url = f"http://{host}:{port}"
            print(C.success(f"Servidor iniciado: {url}"))
            print(C.info(f"Abre en tu navegador: {url}"))
            print(C.dim("  Ctrl+C para detener\n"))
            httpd.serve_forever()

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _print_phase_stats(self, result):
        """Imprime estadísticas por fase del pipeline."""
        print(C.phase(1, f"Filtrado morfosintáctico: {result.phase1.filtered_count} SNC extraídos, {result.phase1.noise_removed} ruido eliminado"))
        print(C.phase(2, f"BFS Clustering: {len(result.phase2.clusters)} clusters (τ={result.phase2.tau_threshold})"))
        print(C.phase(3, f"Canonicalización: {len(result.phase3.canonical_forms)} formas canónicas, {result.phase3.polysemous_count} polisémicos, {result.phase3.acronyms_expanded} acrónimos expandidos"))
        print(C.phase(4, f"Grafo Imperativo: {result.phase4.graph.stats()['total_nodes']} nodos ({result.phase4.graph.stats()['atomic_nodes']} atómicos)"))

    def _get_multiline_input(self) -> str:
        """Lee corpus multilínea hasta línea en blanco."""
        print(C.info("Introduce el corpus (línea en blanco para terminar):"))
        lines = []
        while True:
            try:
                line = input()
                if line == "":
                    break
                lines.append(line)
            except (KeyboardInterrupt, EOFError):
                break
        return "\n".join(lines)

    def _print_help(self):
        """Muestra ayuda de comandos."""
        print(f"""
{C.header('Comandos disponibles:')}
  {C.CYAN}process{C.RESET} [corpus]    Procesar corpus por el pipeline completo
  {C.CYAN}tree{C.RESET}               Mostrar árbol imperativo del spec
  {C.CYAN}export{C.RESET} [formato]   Exportar grafo (jsonld|turtle|tree|flat)
  {C.CYAN}validate{C.RESET} <file>    Validar JSON-LD existente (SAT/CDCL)
  {C.CYAN}stats{C.RESET}              Estadísticas del último resultado
  {C.CYAN}demo{C.RESET}               Ejecutar con corpus de demostración
  {C.CYAN}serve{C.RESET}              Iniciar servidor web (localhost:8080)
  {C.CYAN}help{C.RESET}               Esta ayuda
  {C.CYAN}exit{C.RESET}               Salir
""")

    def _print_stats(self):
        """Muestra estadísticas del último resultado procesado."""
        if self._last_result is None:
            result = self.pipeline.get_spec_graph()
        else:
            result = self._last_result
        stats = result.phase4.graph.stats()
        print(f"\n{C.header('📈 Estadísticas del Grafo:')}")
        for k, v in stats.items():
            print(f"  {k:20s} {C.CYAN}{v}{C.RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Corpus de Demostración
# ─────────────────────────────────────────────────────────────────────────────

DEMO_CORPUS = """
El procesamiento del lenguaje natural (NLP) requiere la extracción de sintagmas nominales
canónicos (SNC) mediante etiquetado morfosintáctico y análisis de dependencias sintácticas.

La lematización formal reduce variaciones morfológicas al lema canónico: f(W_var) → L_canon.
La desambiguación de sentidos polisémicos (WSD) asigna identificadores unívocos (IRI / UUID v4)
a cada sentido contextual detectado.

El clustering por distancia coseno agrupa sintagmas con similitud semántica ≥ τ, donde la
búsqueda en amplitud (BFS) garantiza cobertura horizontal de las dimensiones temáticas.
La exhaustividad colectiva y exclusión mutua (MECE) validan la coherencia del grafo resultante.

Exportar el grafo de conocimiento a JSON-LD / SKOS RDF permite integración con sistemas
de representación del conocimiento basados en ontologías OWL 2 y razonadores lógicos.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Punto de Entrada del Agente
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = OntologyAgent()
    agent.cmd_interactive()
