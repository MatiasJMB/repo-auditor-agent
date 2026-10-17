import tempfile
import unittest
from pathlib import Path

from repo_auditor.analyzer import RepositoryAnalyzer


class RepositoryAnalyzerTests(unittest.TestCase):
    def test_analyzer_detects_languages_dependencies_endpoints_and_findings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "sample"
            repo.mkdir()
            (repo / "package.json").write_text('{"scripts":{"start":"node src/index.js"},"dependencies":{"express":"latest"}}')
            (repo / "Dockerfile").write_text("EXPOSE 8080\n")
            src = repo / "src"
            src.mkdir()
            (src / "index.js").write_text(
                "const api = 'https://api.example.com/v1';\n"
                "const password = 'secret123';\n"
                "function unusedHelper() { return true; }\n"
            )
            (repo / ".env.example").write_text("DATABASE_URL=postgres://localhost/app\nAPI_KEY=change-me\n")

            report = RepositoryAnalyzer(repo).analyze()

            self.assertEqual(report.name, "sample")
            self.assertEqual(report.languages["JavaScript"], 1)
            self.assertIn("npm", report.dependency_managers)
            self.assertIn("Docker", report.runtime_hints)
            self.assertTrue(any(endpoint.url == "https://api.example.com/v1" for endpoint in report.connectivity.endpoints))
            self.assertTrue(any(item.name == "DATABASE_URL" for item in report.connectivity.environment_variables))
            self.assertTrue(any(finding.category == "Seguridad" for finding in report.findings))
            self.assertTrue(any(finding.category == "Código muerto / limpieza" for finding in report.findings))

    def test_analyzer_ignores_vendor_and_generated_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "sample"
            (repo / "node_modules" / "pkg").mkdir(parents=True)
            (repo / "src").mkdir(parents=True)
            (repo / "node_modules" / "pkg" / "index.js").write_text("console.log('vendor')")
            (repo / "src" / "main.py").write_text("print('ok')")

            report = RepositoryAnalyzer(repo).analyze()

            self.assertEqual(report.total_files, 1)
            self.assertEqual(report.languages, {"Python": 1})


if __name__ == "__main__":
    unittest.main()
