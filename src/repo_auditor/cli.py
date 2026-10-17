from __future__ import annotations

import argparse
import os
from pathlib import Path

from repo_auditor.agent import RepoAuditorAgent
from repo_auditor.analyzer import RepositoryAnalyzer
from repo_auditor.docs import DocumentationGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-auditor",
        description="Agente auditor que analiza repositorios Git/GitHub y genera documentación técnica en Markdown.",
    )
    parser.add_argument("repository", help="URL HTTPS/SSH del repositorio o ruta local.")
    parser.add_argument("--workspace", default=".auditor-workspace", help="Directorio donde clonar repositorios remotos.")
    parser.add_argument("--output", default="docs/audits", help="Directorio donde guardar la documentación generada.")
    parser.add_argument("--token", default=None, help="Token/PAT de solo lectura. También puede usarse GITHUB_TOKEN.")
    parser.add_argument("--no-prompt", action="store_true", help="No pedir token si falla el clone; útil para CI.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = args.repository
    output_dir = Path(args.output).resolve()

    try:
        if Path(repository).exists():
            report = RepositoryAnalyzer(Path(repository)).analyze()
            documentation_path = DocumentationGenerator(output_dir / report.name).write(report)
            repository_path = Path(repository).resolve()
        else:
            token = args.token or os.getenv("GITHUB_TOKEN")
            result = RepoAuditorAgent(Path(args.workspace).resolve(), output_dir).audit_url(
                repository,
                token=token,
                ask_token=not args.no_prompt,
            )
            documentation_path = result.documentation_path
            repository_path = result.repository_path
            report = result.report
    except Exception as exc:  # noqa: BLE001 - CLI debe mostrar errores amigables.
        print(f"Error: {exc}")
        return 1

    print("Auditoría completada")
    print(f"Repositorio analizado: {repository_path}")
    print(f"Documentación generada: {documentation_path}")
    print(f"Hallazgos: {len(report.findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
