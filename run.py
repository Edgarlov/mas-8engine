"""
run.py — Entry Point CLI del Engine Ontológico v2.0

Uso:
  python run.py                          # Modo interactivo (REPL)
  python run.py --corpus "texto..."      # Procesar corpus directo
  python run.py --corpus-file path.txt   # Procesar archivo de corpus
  python run.py --tree                   # Mostrar árbol imperativo del spec
  python run.py --export jsonld          # Exportar JSON-LD a stdout
  python run.py --export tree            # Exportar árbol ASCII
  python run.py --export turtle          # Exportar RDF Turtle
  python run.py --validate schema.json   # Validar JSON-LD (SAT/CDCL)
  python run.py --serve [--port 8080]    # Servidor web local
  python run.py --demo                   # Ejecutar con corpus de demostración
  python run.py --stats                  # Estadísticas del spec tree
"""

import argparse
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from agent.ontology_agent import OntologyAgent, DEMO_CORPUS, BANNER, C
from ontology_engine import PipelineConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ontology",
        description="Ontology Engine v2.0 — Motor de Ingeniería Ontológica y Minería Léxica",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run.py --demo
  python run.py --corpus "Procesamiento del lenguaje natural y minería léxica"
  python run.py --tree
  python run.py --export jsonld --output schemas/mi_grafo.json
  python run.py --serve --port 8080
  python run.py --validate schemas/ontologia_v2_full.json
        """,
    )

    # Fuente del corpus
    corpus_group = parser.add_mutually_exclusive_group()
    corpus_group.add_argument(
        "--corpus", "-c",
        metavar="TEXT",
        help="Corpus de texto a procesar",
    )
    corpus_group.add_argument(
        "--corpus-file", "-f",
        metavar="FILE",
        help="Archivo de texto con el corpus",
    )
    corpus_group.add_argument(
        "--demo",
        action="store_true",
        help="Ejecutar con corpus de demostración",
    )

    # Comandos
    parser.add_argument(
        "--tree",
        action="store_true",
        help="Mostrar árbol imperativo del spec",
    )
    parser.add_argument(
        "--export",
        choices=["jsonld", "turtle", "tree", "flat"],
        metavar="FORMAT",
        help="Exportar grafo en formato: jsonld|turtle|tree|flat",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Archivo de salida para la exportación",
    )
    parser.add_argument(
        "--validate",
        metavar="FILE",
        help="Validar JSON-LD existente con SAT/CDCL",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Iniciar servidor web local",
    )

    # Configuración
    parser.add_argument(
        "--tau",
        type=float,
        default=0.25,
        help="Umbral de similitud coseno τ para clustering (default: 0.25)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Profundidad máxima del árbol k-máximo (default: 5)",
    )
    parser.add_argument(
        "--no-spec-tree",
        action="store_true",
        help="Construir árbol desde corpus (no usar spec tree predefinido)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Puerto para el servidor web (default: 8080)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar salida detallada por fase",
    )
    parser.add_argument(
        "--format", "-fmt",
        choices=["tree", "jsonld", "summary"],
        default="tree",
        help="Formato de salida del resultado (default: tree)",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Configurar pipeline
    config = PipelineConfig(
        tau=args.tau,
        max_depth=args.max_depth,
        use_spec_tree=not args.no_spec_tree,
        verbose=args.verbose,
    )

    agent = OntologyAgent(config=config)

    # ── Determinar acción ─────────────────────────────────────────────────

    # 1. Servidor web
    if args.serve:
        print(BANNER)
        agent.cmd_serve(port=args.port)
        return

    # 2. Validar JSON-LD
    if args.validate:
        agent.cmd_validate(args.validate)
        return

    # 3. Árbol del spec
    if args.tree:
        agent.cmd_tree()
        if args.export:
            print()
            agent.cmd_export(args.export, args.output)
        return

    # 4. Procesar corpus
    corpus = None
    if args.corpus:
        corpus = args.corpus
    elif args.corpus_file:
        try:
            corpus = Path(args.corpus_file).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(C.error(f"Archivo no encontrado: {args.corpus_file}"))
            sys.exit(1)
    elif args.demo:
        corpus = DEMO_CORPUS

    if corpus:
        agent.cmd_process(corpus, output_format=args.format)
        if args.export:
            print()
            agent.cmd_export(args.export, args.output)
        return

    # 5. Solo exportar (sin corpus → usar spec tree)
    if args.export:
        agent.cmd_export(args.export, args.output)
        return

    # 6. Sin argumentos → modo interactivo
    agent.cmd_interactive()


if __name__ == "__main__":
    main()
