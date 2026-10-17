from __future__ import annotations

import getpass
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class CloneResult:
    path: Path
    used_authentication: bool


class GitRepositoryClient:
    """Clona repositorios Git/GitHub usando git CLI."""

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def clone(self, repo_url: str, token: str | None = None, ask_token: bool = True) -> CloneResult:
        self.workspace.mkdir(parents=True, exist_ok=True)
        target = self.workspace / self._safe_name(repo_url)
        if target.exists():
            return CloneResult(path=target, used_authentication=False)

        authenticated_url = repo_url
        used_authentication = False
        if token:
            authenticated_url = self._inject_token(repo_url, token)
            used_authentication = True

        try:
            self._run_git_clone(authenticated_url, target)
            return CloneResult(path=target, used_authentication=used_authentication)
        except subprocess.CalledProcessError as exc:
            if token or not ask_token or not self._looks_like_auth_error(exc):
                raise RuntimeError(self._clean_git_error(exc)) from exc

        token = getpass.getpass("El repositorio parece requerir acceso. Ingresa un GitHub token/PAT con permisos de lectura: ")
        if not token.strip():
            raise RuntimeError("No se entregó token; no se puede clonar un repositorio privado.")
        authenticated_url = self._inject_token(repo_url, token.strip())
        self._run_git_clone(authenticated_url, target)
        return CloneResult(path=target, used_authentication=True)

    def _run_git_clone(self, url: str, target: Path) -> None:
        subprocess.run(["git", "clone", "--depth", "1", url, str(target)], check=True, text=True, capture_output=True)

    def _safe_name(self, repo_url: str) -> str:
        parsed = urlparse(repo_url)
        raw = Path(parsed.path).name or "repository"
        name = re.sub(r"\.git$", "", raw)
        name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip(".-")
        return name or "repository"

    def _inject_token(self, repo_url: str, token: str) -> str:
        parsed = urlparse(repo_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Para usar token, entrega una URL HTTPS del repositorio.")
        netloc = parsed.netloc
        if "@" in netloc:
            netloc = netloc.split("@", 1)[1]
        return urlunparse(parsed._replace(netloc=f"x-access-token:{token}@{netloc}"))

    def _looks_like_auth_error(self, exc: subprocess.CalledProcessError) -> bool:
        output = f"{exc.stdout}\n{exc.stderr}".lower()
        return any(marker in output for marker in ["authentication", "permission denied", "not found", "could not read username", "repository not found"])

    def _clean_git_error(self, exc: subprocess.CalledProcessError) -> str:
        output = f"{exc.stdout}\n{exc.stderr}"
        return re.sub(r"x-access-token:[^@\s]+@", "x-access-token:***@", output).strip() or "git clone falló"
