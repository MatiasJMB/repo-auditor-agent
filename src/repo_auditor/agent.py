from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repo_auditor.analyzer import RepositoryAnalyzer, RepositoryReport
from repo_auditor.docs import DocumentationGenerator
from repo_auditor.git_client import GitRepositoryClient


@dataclass(frozen=True)
class AuditResult:
    repository_path: Path
    documentation_path: Path
    report: RepositoryReport


class RepoAuditorAgent:
    """Orquestador: clona repositorio, analiza y produce documentación."""

    def __init__(self, workspace: Path, output_dir: Path):
        self.workspace = workspace
        self.output_dir = output_dir

    def audit_url(self, repo_url: str, token: str | None = None, ask_token: bool = True) -> AuditResult:
        clone = GitRepositoryClient(self.workspace).clone(repo_url, token=token, ask_token=ask_token)
        return self.audit_path(clone.path)

    def audit_path(self, repository_path: Path) -> AuditResult:
        report = RepositoryAnalyzer(repository_path).analyze()
        docs_dir = self.output_dir / report.name
        documentation_path = DocumentationGenerator(docs_dir).write(report)
        return AuditResult(repository_path=repository_path, documentation_path=documentation_path, report=report)
