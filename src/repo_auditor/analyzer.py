from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "target",
    ".next",
    ".turbo",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript/React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
}

DEPENDENCY_FILES = {
    "package.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "Yarn",
    "requirements.txt": "pip",
    "pyproject.toml": "Python packaging",
    "Pipfile": "Pipenv",
    "poetry.lock": "Poetry",
    "go.mod": "Go modules",
    "Cargo.toml": "Cargo/Rust",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "composer.json": "Composer/PHP",
    "Gemfile": "Bundler/Ruby",
}

RUNTIME_FILES = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose",
    "Procfile": "Procfile/PaaS",
    "serverless.yml": "Serverless",
    "vercel.json": "Vercel",
    "netlify.toml": "Netlify",
    "terraform.tf": "Terraform",
}

ENTRYPOINT_CANDIDATES = {
    "main.py",
    "app.py",
    "wsgi.py",
    "asgi.py",
    "manage.py",
    "index.js",
    "server.js",
    "app.js",
    "main.ts",
    "index.ts",
    "cmd/main.go",
    "src/main.rs",
}

SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|private[_-]?key)\s*[:=]\s*['\"]([^'\"]{8,})['\"]")
URL_RE = re.compile(r"https?://[^\s'\"`)>]+")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
PORT_PATTERNS = [
    re.compile(r"(?i)\bEXPOSE\s+(\d{2,5})\b"),
    re.compile(r"\bPORT\s*[:=]\s*['\"]?(\d{2,5})\b"),
    re.compile(r"(?i)\b(?:localhost|127\.0\.0\.1):([0-9]{2,5})\b"),
    re.compile(r"(?i)\blisten\s*\(\s*['\"]?(\d{2,5})\b"),
]
UNUSED_RE = re.compile(r"(?m)^\s*(?:function\s+(unused\w*)|def\s+(unused\w*)|const\s+(unused\w*)|let\s+(unused\w*)|var\s+(unused\w*))")


@dataclass(frozen=True)
class Endpoint:
    url: str
    file: str
    line: int


@dataclass(frozen=True)
class ConnectivityItem:
    name: str
    file: str
    line: int


@dataclass
class Connectivity:
    endpoints: list[Endpoint] = field(default_factory=list)
    environment_variables: list[ConnectivityItem] = field(default_factory=list)
    ports: list[ConnectivityItem] = field(default_factory=list)


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    title: str
    location: str
    recommendation: str


@dataclass
class RepositoryReport:
    name: str
    root: Path
    total_files: int
    total_lines: int
    languages: dict[str, int]
    dependency_managers: list[str]
    runtime_hints: list[str]
    entrypoints: list[str]
    top_level_structure: list[str]
    connectivity: Connectivity
    findings: list[Finding]
    suggested_removals: list[str]
    architecture_summary: str


class RepositoryAnalyzer:
    """Analizador heurístico offline para repositorios de software."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"No existe el repositorio: {self.root}")

    def analyze(self) -> RepositoryReport:
        files = list(self._iter_files())
        language_counter: Counter[str] = Counter()
        dependency_managers: set[str] = set()
        runtime_hints: set[str] = set()
        entrypoints: list[str] = []
        connectivity = Connectivity()
        findings: list[Finding] = []
        total_lines = 0

        for file in files:
            rel = self._rel(file)
            if file.suffix in LANGUAGE_BY_EXTENSION:
                language_counter[LANGUAGE_BY_EXTENSION[file.suffix]] += 1
            if file.name in DEPENDENCY_FILES:
                dependency_managers.add(DEPENDENCY_FILES[file.name])
            if file.name in RUNTIME_FILES:
                runtime_hints.add(RUNTIME_FILES[file.name])
            if rel in ENTRYPOINT_CANDIDATES or file.name in ENTRYPOINT_CANDIDATES:
                entrypoints.append(rel)

            text = self._read_text(file)
            if text is None:
                continue
            lines = text.splitlines()
            total_lines += len(lines)
            self._collect_connectivity(rel, lines, connectivity)
            findings.extend(self._collect_findings(rel, text, lines))

        suggested_removals = self._suggest_removals(files)
        return RepositoryReport(
            name=self.root.name,
            root=self.root,
            total_files=len(files),
            total_lines=total_lines,
            languages=dict(language_counter.most_common()),
            dependency_managers=sorted(dependency_managers),
            runtime_hints=sorted(runtime_hints),
            entrypoints=sorted(set(entrypoints)),
            top_level_structure=self._top_level_structure(),
            connectivity=connectivity,
            findings=self._dedupe_findings(findings),
            suggested_removals=suggested_removals,
            architecture_summary=self._summarize_architecture(language_counter, dependency_managers, runtime_hints, entrypoints),
        )

    def _iter_files(self) -> Iterable[Path]:
        for path in self.root.rglob("*"):
            if path.is_dir():
                continue
            parts = set(path.relative_to(self.root).parts)
            if parts & IGNORED_DIRS:
                continue
            yield path

    def _read_text(self, path: Path) -> str | None:
        try:
            if path.stat().st_size > 1_000_000:
                return None
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _collect_connectivity(self, rel: str, lines: list[str], connectivity: Connectivity) -> None:
        for idx, line in enumerate(lines, start=1):
            for url in URL_RE.findall(line):
                connectivity.endpoints.append(Endpoint(url=url.rstrip(".,;"), file=rel, line=idx))
            if rel.endswith((".env", ".env.example", "settings.py", "config.py", "config.js", "config.ts", "yaml", "yml")):
                for env_name in ENV_RE.findall(line):
                    if env_name not in {"TRUE", "FALSE", "NULL", "HTTP", "HTTPS", "GET", "POST"}:
                        connectivity.environment_variables.append(ConnectivityItem(name=env_name, file=rel, line=idx))
            for pattern in PORT_PATTERNS:
                for port in pattern.findall(line):
                    if 1 <= int(port) <= 65535:
                        connectivity.ports.append(ConnectivityItem(name=port, file=rel, line=idx))

    def _collect_findings(self, rel: str, text: str, lines: list[str]) -> list[Finding]:
        findings: list[Finding] = []
        for idx, line in enumerate(lines, start=1):
            if SECRET_RE.search(line) and "change-me" not in line.lower():
                findings.append(Finding("Alta", "Seguridad", "Posible secreto o credencial en código", f"{rel}:{idx}", "Mover secretos a un gestor seguro o variables de entorno; rotar la credencial si es real."))
            if "TODO" in line or "FIXME" in line:
                findings.append(Finding("Media", "Mantenibilidad", "TODO/FIXME pendiente", f"{rel}:{idx}", "Convertirlo en issue priorizado o resolverlo para reducir deuda técnica."))
            if "console.log" in line or "print(" in line and rel.endswith(".py"):
                findings.append(Finding("Baja", "Observabilidad", "Logs informales detectados", f"{rel}:{idx}", "Usar un logger estructurado con niveles, contexto y correlación."))
        for match in UNUSED_RE.finditer(text):
            symbol = next(group for group in match.groups() if group)
            findings.append(Finding("Baja", "Código muerto / limpieza", f"Símbolo candidato a no usado: {symbol}", rel, "Confirmar con tests/cobertura y eliminar si no tiene referencias."))
        if rel in {"package.json", "requirements.txt", "pyproject.toml"} and "latest" in text.lower():
            findings.append(Finding("Media", "Dependencias", "Dependencia sin versión fija", rel, "Fijar versiones o rangos explícitos para builds reproducibles."))
        return findings

    def _suggest_removals(self, files: list[Path]) -> list[str]:
        suggestions: list[str] = []
        removable_extensions = {".log", ".tmp", ".bak", ".orig", ".swp"}
        removable_files = [self._rel(file) for file in files if file.suffix in removable_extensions]
        if removable_files:
            suggestions.append("Revisar y eliminar artefactos temporales: " + ", ".join(removable_files[:10]))
        if any(path.name in {"dist", "build", "coverage"} for path in self.root.iterdir() if path.is_dir()):
            suggestions.append("No versionar salidas generadas como dist/, build/ o coverage/ salvo que exista una razón de distribución.")
        if not (self.root / "README.md").exists():
            suggestions.append("Crear README.md; hoy falta documentación de arranque en la raíz.")
        return suggestions

    def _top_level_structure(self) -> list[str]:
        items = []
        for child in sorted(self.root.iterdir(), key=lambda p: p.name.lower()):
            if child.name in IGNORED_DIRS:
                continue
            items.append(child.name + ("/" if child.is_dir() else ""))
        return items[:40]

    def _summarize_architecture(self, languages: Counter[str], deps: set[str], runtime: set[str], entrypoints: list[str]) -> str:
        main_language = languages.most_common(1)[0][0] if languages else "no identificado"
        parts = [f"El repositorio parece centrarse en {main_language}."]
        if deps:
            parts.append("Gestores de dependencias detectados: " + ", ".join(sorted(deps)) + ".")
        if runtime:
            parts.append("Tiene señales de despliegue/ejecución: " + ", ".join(sorted(runtime)) + ".")
        if entrypoints:
            parts.append("Puntos de entrada probables: " + ", ".join(sorted(set(entrypoints))) + ".")
        return " ".join(parts)

    def _dedupe_findings(self, findings: list[Finding]) -> list[Finding]:
        seen = set()
        result = []
        for finding in findings:
            key = (finding.category, finding.title, finding.location)
            if key not in seen:
                seen.add(key)
                result.append(finding)
        severity_rank = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3}
        return sorted(result, key=lambda f: (severity_rank.get(f.severity, 9), f.category, f.location))

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()
