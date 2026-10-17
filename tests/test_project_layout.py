"""Yeni src/ yerlesimi ve paket entegrasyonu regresyon testleri."""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import customtkinter  # noqa: F401
except ImportError:
    # Ekran acmadan kaynak modulu import edebilmek icin test taklidi.
    import types
    ctk_stub = types.ModuleType("customtkinter")
    ctk_stub.CTk = type("CTk", (), {})
    sys.modules["customtkinter"] = ctk_stub

from fortnite_splash_maker import main
from fortnite_splash_maker import splash_files
from fortnite_splash_maker.ui import components, dialogs, feedback


class ProjectLayoutTests(unittest.TestCase):
    def test_imported_modules_belong_to_package(self):
        self.assertTrue(main.__name__.startswith("fortnite_splash_maker."))
        self.assertTrue(splash_files.__name__.startswith("fortnite_splash_maker."))
        for mod in (components, dialogs, feedback):
            self.assertTrue(mod.__name__.startswith("fortnite_splash_maker.ui."))

    def test_source_uses_existing_root_data_and_assets(self):
        self.assertEqual(main.APP_DIR, ROOT)
        self.assertEqual(main.LIBRARY_DIR, ROOT / "library")
        self.assertEqual(main.SETTINGS_PATH, ROOT / "settings.json")
        self.assertEqual(main.ASSETS_DIR, ROOT / "assets")
        self.assertIn("FortniteSplashMaker", str(main.BACKUP_DIR))

    def test_build_script_targets_source_runner(self):
        build = (ROOT / "scripts" / "build.ps1").read_text(encoding="utf-8")
        self.assertIn('"--paths", ".\\src"', build)
        self.assertIn('$pyInstallerArgs += ".\\scripts\\run.py"', build)
        self.assertFalse((ROOT / "main.py").exists())

    def test_package_entrypoints_have_correct_imports(self):
        for path in (
            ROOT / "scripts" / "run.py",
            ROOT / "src" / "fortnite_splash_maker" / "__main__.py",
        ):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        from fortnite_splash_maker.__main__ import main as entry
        self.assertTrue(callable(entry))

    def test_install_and_release_paths_unchanged(self):
        installer = (ROOT / "installer" / "installer.iss").read_text(encoding="utf-8-sig")
        self.assertIn("dist\\FortniteSplashMaker", installer)
        self.assertIn("DefaultDirName={localappdata}\\Programs\\FortniteSplashMaker", installer)
        self.assertIn("assets\\app_icon.ico", installer)
        release = (ROOT / "scripts" / "release.ps1").read_text(encoding="utf-8")
        self.assertIn('"settings.json"', release)
        self.assertIn('"library"', release)


if __name__ == "__main__":
    unittest.main()
