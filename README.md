# Repo Auditor Agent

Agente CLI en Python que clona (o lee) un repositorio Git y genera un documento Markdown que explica cómo funciona el proyecto, sus dependencias, conectividades y riesgos. Para quien recibe o revisa un repositorio y necesita entenderlo rápido.

## Qué hace

- Acepta una URL HTTPS o SSH de un repositorio, o una ruta local.
- Clona repositorios remotos en una carpeta de trabajo. Si el clone falla por permisos, pide un token de solo lectura por consola (se omite con `--no-prompt`).
- Analiza estructura, lenguajes, dependencias y puntos de entrada.
- Detecta conectividades: URLs, variables de entorno y puertos.
- Genera hallazgos de seguridad, mantenibilidad, observabilidad, dependencias y limpieza.
- Escribe `AUDITORIA_REPOSITORIO.md` en `docs/audits/<nombre-repo>/` (carpeta configurable con `--output`).

## Stack

- Python 3.10 o superior (`requires-python`).
- Sin dependencias de runtime; `pytest` >=8 solo como dependencia de desarrollo opcional.
- Git por línea de comandos para clonar.

## Cómo correrlo en local

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
repo-auditor /ruta/al/repositorio
repo-auditor https://github.com/usuario/proyecto.git
```

Repositorio privado: pasar un token de solo lectura con `--token` o con la variable `GITHUB_TOKEN` (valor a definir por el usuario, nunca se guarda). Otras opciones: `--workspace` (carpeta de clones) y `--output` (carpeta del documento).

Tests, sin instalar el paquete:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Estructura

```text
src/repo_auditor/   Paquete: cli, agent, git_client, analyzer, docs
tests/              Pruebas de analizador y generador de documentos
docs/plans/         Plan de implementación del proyecto
docs/audits/        Salida generada por el agente (no versionada)
```

## Estado

MVP. El análisis es estático y heurístico: no reemplaza la ejecución de tests, un análisis SAST/DAST profesional, el escaneo de dependencias ni la revisión manual de arquitectura.

## Licencia

MIT — ver LICENSE.

---
Hecho por Matías Moreno · github.com/MatiasJMB
