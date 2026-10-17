# Repo Auditor Agent Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Crear un agente CLI que reciba un repositorio Git/GitHub, obtenga accesos cuando sean necesarios, analice el proyecto y genere documentación de uso/auditoría.

**Architecture:** CLI en Python con módulos separados para clonación, análisis estático, orquestación y generación Markdown. El primer alcance evita dependencias externas para que sea fácil de instalar y ejecutar.

**Tech Stack:** Python 3.10+, git CLI, pytest.

---

## Fases implementadas

1. Crear pruebas para el analizador estático.
2. Crear pruebas para el generador de documentación.
3. Implementar `RepositoryAnalyzer` con detección de lenguajes, dependencias, runtime, entrypoints, conectividades y hallazgos.
4. Implementar `DocumentationGenerator` para producir `AUDITORIA_REPOSITORIO.md`.
5. Implementar `GitRepositoryClient` para clonar repositorios públicos/privados y pedir token cuando falte acceso.
6. Implementar `RepoAuditorAgent` y CLI `repo-auditor`.
7. Documentar instalación, uso y próximos pasos en README.

## Próximos incrementos recomendados

### Task 1: Agregar salida JSON

**Objective:** Permitir consumo por CI/CD o dashboards.

**Files:**
- Modify: `src/repo_auditor/cli.py`
- Modify: `src/repo_auditor/analyzer.py`
- Test: `tests/test_cli.py`

**Steps:** agregar `--format markdown|json`, serializar dataclasses y verificar salida.

### Task 2: Agregar Mermaid

**Objective:** Generar diagrama de conectividades.

**Files:**
- Modify: `src/repo_auditor/docs.py`
- Test: `tests/test_docs.py`

**Steps:** convertir endpoints, puertos y env vars en bloque Mermaid simple.

### Task 3: Integrar escáneres opcionales

**Objective:** Ejecutar herramientas si existen sin hacerlas obligatorias.

**Files:**
- Create: `src/repo_auditor/external_tools.py`
- Test: `tests/test_external_tools.py`

**Steps:** detectar `semgrep`, `trivy`, `npm audit`, `pip-audit`; ejecutar con timeout; anexar resultados.
