"""Release Candidate surum ve paketleme bilgilerinin senkron kalmasi."""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "1.1.0"


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def python_app_version():
    module = ast.parse(text("src/fortnite_splash_maker/main.py"))
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "APP_VERSION" for target in statement.targets):
                return ast.literal_eval(statement.value)
    raise AssertionError("APP_VERSION not defined")


class ReleaseMetadataTests(unittest.TestCase):
    def test_app_and_pyproject_versions_match(self):
        self.assertEqual(python_app_version(), EXPECTED)
        project = text("pyproject.toml")
        self.assertRegex(project, rf'(?m)^version\s*=\s*"{re.escape(EXPECTED)}"$')

    def test_powershell_scripts_have_same_version(self):
        for file in ("scripts/build.ps1", "scripts/build-installer.ps1", "scripts/release.ps1"):
            with self.subTest(file=file):
                content = text(file)
                versions = re.findall(r'(?m)^\$Version\s*=\s*"([^"]+)"', content)
                self.assertEqual(versions, [EXPECTED])
                self.assertNotIn('"1.0.0"', content)

    def test_installer_metadata_and_filename_are_consistent(self):
        iss = text("installer/installer.iss")
        self.assertIn(f'#define MyAppVersion "{EXPECTED}"', iss)
        self.assertIn(f'VersionInfoVersion={EXPECTED}.0', iss)
        self.assertIn(f'VersionInfoProductVersion={EXPECTED}.0', iss)
        self.assertIn('OutputBaseFilename=FortniteSplashMaker-v{#MyAppVersion}-Setup', iss)
        self.assertIn('AppVersion={#MyAppVersion}', iss)
        installer_script = text("scripts/build-installer.ps1")
        self.assertIn('FortniteSplashMaker-v$Version-Setup.exe', installer_script)

    def test_packaging_rejects_stale_executable(self):
        build = text("scripts/build.ps1")
        self.assertIn('build-version.txt', build)
        self.assertIn('Set-Content', build)
        for file in ("scripts/build-installer.ps1", "scripts/release.ps1"):
            with self.subTest(file=file):
                content = text(file)
                self.assertIn('build-version.txt', content)
                self.assertIn('Get-Content', content)
                self.assertIn('$BuiltVersion -ne $Version', content)
                self.assertIn('throw', content)

    def test_changelog_and_release_docs_are_present(self):
        changelog = text("CHANGELOG.md")
        self.assertIn('## [1.1.0] — Release Candidate', changelog)
        self.assertIn('## [1.0.0]', changelog)
        readme = text("README.md")
        self.assertIn('(CHANGELOG.md)', readme)
        self.assertIn('v1.1.0 Release Candidate', readme)
        release_notes = text("docs/RELEASE.md")
        self.assertIn('FortniteSplashMaker-v1.1.0-win64.zip', release_notes)
        self.assertIn('FortniteSplashMaker-v1.1.0-Setup.exe', release_notes)


if __name__ == "__main__":
    unittest.main()
