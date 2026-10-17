import tempfile
import unittest
from pathlib import Path

from repo_auditor.analyzer import Connectivity, ConnectivityItem, Endpoint, Finding, RepositoryReport
from repo_auditor.docs import DocumentationGenerator


class DocumentationGeneratorTests(unittest.TestCase):
    def test_documentation_generator_writes_expected_sections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            report = RepositoryReport(
                name="demo",
                root=tmp_path,
                total_files=3,
                total_lines=42,
                languages={"Python": 2},
                dependency_managers=["pip"],
                runtime_hints=["Docker"],
                entrypoints=["src/app.py"],
                top_level_structure=["src/", "README.md"],
                connectivity=Connectivity(
                    endpoints=[Endpoint(url="https://api.example.com", file="src/app.py", line=3)],
                    environment_variables=[ConnectivityItem(name="API_KEY", file=".env.example", line=1)],
                    ports=[ConnectivityItem(name="8000", file="Dockerfile", line=1)],
                ),
                findings=[Finding("Alta", "Seguridad", "Credencial expuesta", "src/app.py", "Mover a variables de entorno")],
                suggested_removals=["Eliminar archivos temporales y build artifacts"],
                architecture_summary="Aplicación pequeña con entrada Python.",
            )

            output_file = DocumentationGenerator(tmp_path).write(report)
            content = output_file.read_text()

            self.assertEqual(output_file.name, "AUDITORIA_REPOSITORIO.md")
            self.assertIn("# Auditoría técnica del repositorio: demo", content)
            self.assertIn("## Cómo funciona el proyecto", content)
            self.assertIn("## Conectividades detectadas", content)
            self.assertIn("Credencial expuesta", content)
            self.assertIn("## Mejoras recomendadas", content)


if __name__ == "__main__":
    unittest.main()
