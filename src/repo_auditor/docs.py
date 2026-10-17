from __future__ import annotations

from pathlib import Path

from repo_auditor.analyzer import Finding, RepositoryReport


class DocumentationGenerator:
    """Genera documentación técnica y ejecutiva en Markdown."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def write(self, report: RepositoryReport) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / "AUDITORIA_REPOSITORIO.md"
        output_file.write_text(self.render(report), encoding="utf-8")
        return output_file

    def render(self, report: RepositoryReport) -> str:
        lines: list[str] = []
        lines.append(f"# Auditoría técnica del repositorio: {report.name}")
        lines.append("")
        lines.append("## Resumen ejecutivo")
        lines.append(f"- Archivos analizados: {report.total_files}")
        lines.append(f"- Líneas aproximadas: {report.total_lines}")
        lines.append(f"- Lenguajes principales: {self._format_dict(report.languages)}")
        lines.append(f"- Riesgos detectados: {len(report.findings)}")
        lines.append("")
        lines.append("## Cómo funciona el proyecto")
        lines.append(report.architecture_summary or "No se pudo inferir arquitectura con las heurísticas actuales.")
        lines.append("")
        lines.append("### Estructura principal")
        lines.extend(self._bullets(report.top_level_structure))
        lines.append("")
        lines.append("### Puntos de entrada probables")
        lines.extend(self._bullets(report.entrypoints or ["No detectados automáticamente; revisar README, scripts y configuración de despliegue."]))
        lines.append("")
        lines.append("### Dependencias y runtime")
        lines.append(f"- Gestores/manifest detectados: {', '.join(report.dependency_managers) if report.dependency_managers else 'No detectados'}")
        lines.append(f"- Señales de ejecución/despliegue: {', '.join(report.runtime_hints) if report.runtime_hints else 'No detectadas'}")
        lines.append("")
        lines.append("## Conectividades detectadas")
        lines.append("### Endpoints externos")
        if report.connectivity.endpoints:
            for item in report.connectivity.endpoints[:100]:
                lines.append(f"- `{item.url}` en `{item.file}:{item.line}`")
        else:
            lines.append("- No se detectaron URLs HTTP/HTTPS en texto plano.")
        lines.append("")
        lines.append("### Variables de entorno / configuración")
        if report.connectivity.environment_variables:
            for item in report.connectivity.environment_variables[:100]:
                lines.append(f"- `{item.name}` en `{item.file}:{item.line}`")
        else:
            lines.append("- No se detectaron variables relevantes en archivos de configuración conocidos.")
        lines.append("")
        lines.append("### Puertos")
        if report.connectivity.ports:
            for item in report.connectivity.ports[:100]:
                lines.append(f"- `{item.name}` en `{item.file}:{item.line}`")
        else:
            lines.append("- No se detectaron puertos explícitos.")
        lines.append("")
        lines.append("## Hallazgos del auditor")
        lines.extend(self._findings(report.findings))
        lines.append("")
        lines.append("## Mejoras recomendadas")
        lines.extend(self._recommendations(report))
        lines.append("")
        lines.append("## Cosas a eliminar o simplificar")
        lines.extend(self._bullets(report.suggested_removals or ["No se detectaron candidatos obvios; revisar carpetas generadas, binarios y código no referenciado."]))
        lines.append("")
        lines.append("## Checklist de revisión manual sugerida")
        lines.extend(self._bullets([
            "Confirmar que los puntos de entrada detectados coinciden con producción.",
            "Revisar permisos de tokens, secretos y variables de entorno.",
            "Ejecutar tests, linters y análisis de dependencias vulnerables.",
            "Validar flujos de datos entre frontend, backend, bases de datos y servicios externos.",
            "Revisar si existen módulos duplicados, dependencias sin uso o abstracciones innecesarias.",
            "Documentar runbook: instalación, desarrollo local, despliegue, rollback y monitoreo.",
        ]))
        lines.append("")
        lines.append("## Limitaciones")
        lines.append("Este reporte se genera con análisis estático heurístico. Debe complementarse con ejecución de tests, entrevistas técnicas y herramientas específicas de seguridad/dependencias.")
        lines.append("")
        return "\n".join(lines)

    def _format_dict(self, data: dict[str, int]) -> str:
        if not data:
            return "No detectados"
        return ", ".join(f"{key} ({value})" for key, value in data.items())

    def _bullets(self, items: list[str]) -> list[str]:
        return [f"- {item}" for item in items]

    def _findings(self, findings: list[Finding]) -> list[str]:
        if not findings:
            return ["- No se detectaron hallazgos automáticos de alto impacto."]
        lines = []
        for finding in findings:
            lines.append(f"- **{finding.severity} | {finding.category}**: {finding.title} (`{finding.location}`). Recomendación: {finding.recommendation}")
        return lines

    def _recommendations(self, report: RepositoryReport) -> list[str]:
        recs = [
            "Agregar o actualizar documentación: README, arquitectura, variables de entorno y guía de despliegue.",
            "Definir una matriz de calidad: tests unitarios, integración, lint, seguridad y revisión de dependencias en CI.",
            "Modelar conectividades críticas en un diagrama: clientes, APIs, colas, bases de datos, proveedores externos y puertos.",
            "Separar configuración sensible de código y aplicar principio de mínimo privilegio en tokens.",
            "Priorizar hallazgos por impacto negocio/técnico antes de refactorizar.",
        ]
        if not report.entrypoints:
            recs.append("Declarar claramente cómo se arranca el sistema: comando local, comando de producción y healthcheck.")
        if "Docker" not in report.runtime_hints and "Docker Compose" not in report.runtime_hints:
            recs.append("Evaluar contenedorización o al menos documentar dependencias del entorno para reproducibilidad.")
        if not report.dependency_managers:
            recs.append("Agregar manifiesto de dependencias o documentar explícitamente si el proyecto no requiere dependencias externas.")
        return self._bullets(recs)
