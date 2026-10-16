"""Fortnite Splash Maker v1.1.0 ilk hata düzeltme paketi regresyon testleri.

Calistirma (proje kokunde):
    python -m unittest discover -s tests -p 'test_v11_regressions.py' -v
"""

import hashlib
import io
import sys
import tempfile
import types
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Bu testler UI penceresi açmadan iş mantığını kontrol eder. CTk henüz
# yüklenmemiş test ortamında sadece sınıfı import etmek için bir taklit kullan.
try:
    import customtkinter  # noqa: F401
except ImportError:
    ctk_stub = types.ModuleType("customtkinter")
    ctk_stub.CTk = type("CTk", (), {})
    sys.modules["customtkinter"] = ctk_stub

import main
from splash_files import apply_splash, backup_path_for, restore_previous_splash


class FakeLabel:
    def __init__(self, *_args, **kwargs):
        self.options = dict(kwargs)
        self._splash_image_ref = None
        self.destroyed = False
        self.placement = None

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def destroy(self):
        self.destroyed = True

    def place(self, **kwargs):
        self.placement = dict(kwargs)

    def update_idletasks(self):
        pass


def png_bytes(color=(10, 20, 30, 255)):
    with io.BytesIO() as output:
        Image.new("RGBA", (800, 450), color).save(output, format="PNG")
        return output.getvalue()


class V11Regressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def status_object(self, target):
        obj = types.SimpleNamespace(
            splash_path=target,
            current_splash_state="unknown",
            splash_state_badge=FakeLabel(),
            settings_splash_status_label=FakeLabel(),
        )
        obj.file_sha256 = lambda path: main.FortniteSplashMaker.file_sha256(obj, path)
        return obj

    def test_unknown_when_target_png_broken(self):
        target = self.root / "SplashScreen.png"
        season = self.root / "season.png"
        target.write_bytes(b"damaged")
        season.write_bytes(png_bytes())
        obj = self.status_object(target)
        with patch.object(main, "CURRENT_SEASON_SPLASH_PATH", season):
            main.FortniteSplashMaker.update_active_splash_status(obj)
        self.assertEqual(obj.current_splash_state, "unknown")
        self.assertIn("geçersiz", obj.settings_splash_status_label.options["text"])

    def test_unknown_when_bundled_season_missing(self):
        target = self.root / "SplashScreen.png"
        target.write_bytes(png_bytes())
        obj = self.status_object(target)
        with patch.object(main, "CURRENT_SEASON_SPLASH_PATH", self.root / "missing.png"):
            main.FortniteSplashMaker.update_active_splash_status(obj)
        self.assertEqual(obj.current_splash_state, "unknown")

    def test_equal_season_is_season(self):
        target = self.root / "SplashScreen.png"
        season = self.root / "season.png"
        data = png_bytes()
        target.write_bytes(data)
        season.write_bytes(data)
        obj = self.status_object(target)
        with patch.object(main, "CURRENT_SEASON_SPLASH_PATH", season):
            main.FortniteSplashMaker.update_active_splash_status(obj)
        self.assertEqual(obj.current_splash_state, "season")

    def test_different_season_is_custom(self):
        target = self.root / "SplashScreen.png"
        season = self.root / "season.png"
        target.write_bytes(png_bytes((1, 2, 3, 255)))
        season.write_bytes(png_bytes((2, 3, 4, 255)))
        obj = self.status_object(target)
        with patch.object(main, "CURRENT_SEASON_SPLASH_PATH", season):
            main.FortniteSplashMaker.update_active_splash_status(obj)
        self.assertEqual(obj.current_splash_state, "custom")

    def test_missing_target_is_not_ready(self):
        parent = self.root / "EasyAntiCheat"
        parent.mkdir()
        obj = types.SimpleNamespace(splash_path=parent / "SplashScreen.png")
        with patch.object(main.messagebox, "showerror") as showerror:
            result = main.FortniteSplashMaker.fortnite_target_is_ready(obj)
        self.assertFalse(result)
        showerror.assert_called_once()

    def test_missing_install_clears_stale_path(self):
        obj = types.SimpleNamespace(
            splash_path=self.root / "gone.png",
            fortnite_install_path=self.root / "Fortnite",
            fortnite_badge=FakeLabel(),
            path_label=FakeLabel(),
            splash_state_badge=FakeLabel(),
            settings_splash_status_label=FakeLabel(),
            set_status=lambda _value: None,
        )
        main.FortniteSplashMaker.set_fortnite_not_found(obj)
        self.assertIsNone(obj.splash_path)
        self.assertIsNone(obj.fortnite_install_path)

    def test_direct_splash_folder_is_not_falsely_invalid(self):
        direct = self.root / "EasyAntiCheat"
        direct.mkdir()
        target = direct / "SplashScreen.png"
        target.write_bytes(png_bytes())
        obj = types.SimpleNamespace(
            splash_path=target,
            fortnite_install_path=None,
            settings={"fortnite_path": str(direct), "fortnite_path_is_direct_splash_folder": True},
            settings_path_label=FakeLabel(),
            update_active_splash_status=lambda: None,
        )
        main.FortniteSplashMaker.refresh_settings_page(obj)
        self.assertIn("Aktif ve kayıtlı yol", obj.settings_path_label.options["text"])

    def test_failed_image_load_clears_previous_preview(self):
        old_image_ref = object()
        preview = FakeLabel()
        info = FakeLabel()
        status = []
        obj = types.SimpleNamespace(
            input_path=None,
            original_image=None,
            processed_image=None,
            preview_ctk_image=old_image_ref,
            image_reference_pool=deque(maxlen=256),
            preview_label=preview,
            preview_box=object(),
            file_info=info,
            load_rgba_image=lambda _path: (_ for _ in ()).throw(ValueError("invalid")),
            set_status=status.append,
        )
        obj.create_empty_creator_preview = lambda: main.FortniteSplashMaker.create_empty_creator_preview(obj)
        obj.clear_creator_preview = lambda: main.FortniteSplashMaker.clear_creator_preview(obj)
        with (
            patch.object(main.messagebox, "showerror") as showerror,
            patch.object(main.ctk, "CTkLabel", FakeLabel, create=True),
            patch.object(main.ctk, "CTkFont", lambda **_kwargs: None, create=True),
        ):
            main.FortniteSplashMaker.load_input_image(obj, self.root / "bad.png")
        self.assertIsNone(obj.processed_image)
        self.assertIsNone(obj.preview_ctk_image)
        self.assertTrue(preview.destroyed, "Eski görüntülü widget yok edilmelidir")
        self.assertIsNot(obj.preview_label, preview)
        self.assertIn("Bir görsel seçerek başla", obj.preview_label.options["text"])
        self.assertNotIn("image", obj.preview_label.options)
        self.assertEqual(info.options["text"], "Henüz görsel seçilmedi")
        self.assertEqual(len(obj.image_reference_pool), 1)
        showerror.assert_called_once()

    def test_clearing_library_selection(self):
        old = object()
        original_preview = FakeLabel(image=old)
        obj = types.SimpleNamespace(
            library_preview_image=old,
            library_selected_path=self.root / "old.png",
            library_selected_kind="custom",
            library_preview_label=original_preview,
            library_preview_panel=object(),
            library_name_label=FakeLabel(),
            image_reference_pool=deque(maxlen=256),
        )
        obj.create_empty_library_preview = lambda: main.FortniteSplashMaker.create_empty_library_preview(obj)
        with patch.object(main.ctk, "CTkLabel", FakeLabel, create=True):
            main.FortniteSplashMaker.clear_library_selection(obj)
        self.assertIsNone(obj.library_selected_path)
        self.assertIsNone(obj.library_preview_image)
        self.assertTrue(original_preview.destroyed)
        self.assertIsNot(obj.library_preview_label, original_preview)
        self.assertEqual(obj.library_preview_label.options["text"], "Bir görsel seç")
        self.assertNotIn("image", obj.library_preview_label.options)
        self.assertEqual(obj.library_name_label.options["text"], "-")
        self.assertEqual(len(obj.image_reference_pool), 1)

    def test_repeated_invalid_input_keeps_preview_blank(self):
        old_preview = FakeLabel(image=object())
        info = FakeLabel()
        statuses = []
        obj = types.SimpleNamespace(
            input_path=None,
            original_image=None,
            processed_image=None,
            preview_ctk_image=object(),
            image_reference_pool=deque(maxlen=256),
            preview_label=old_preview,
            preview_box=object(),
            file_info=info,
            load_rgba_image=lambda _path: (_ for _ in ()).throw(ValueError("invalid")),
            set_status=statuses.append,
        )
        obj.create_empty_creator_preview = lambda: main.FortniteSplashMaker.create_empty_creator_preview(obj)
        obj.clear_creator_preview = lambda: main.FortniteSplashMaker.clear_creator_preview(obj)
        with (
            patch.object(main.messagebox, "showerror") as showerror,
            patch.object(main.ctk, "CTkLabel", FakeLabel, create=True),
            patch.object(main.ctk, "CTkFont", lambda **_kwargs: None, create=True),
        ):
            main.FortniteSplashMaker.load_input_image(obj, self.root / "bad.png")
            first_empty = obj.preview_label
            main.FortniteSplashMaker.load_input_image(obj, self.root / "bad_again.png")
        self.assertTrue(old_preview.destroyed)
        self.assertTrue(first_empty.destroyed)
        self.assertIsNot(obj.preview_label, first_empty)
        self.assertNotIn("image", obj.preview_label.options)
        self.assertEqual(obj.preview_label.options["text"], "Bir görsel seçerek başla\n\nPNG • JPG • WEBP • BMP")
        self.assertEqual(len(obj.image_reference_pool), 1)
        self.assertEqual(showerror.call_count, 2)

    def test_previous_splash_restored_byte_for_byte(self):
        target = self.root / "SplashScreen.png"
        backup_dir = self.root / "backups"
        original = png_bytes((12, 33, 44, 255))
        target.write_bytes(original)
        apply_splash(Image.new("RGBA", (1200, 800), (88, 77, 66, 255)), target, backup_dir)
        self.assertNotEqual(target.read_bytes(), original)
        self.assertEqual(backup_path_for(target, backup_dir).read_bytes(), original)
        restore_previous_splash(target, backup_dir)
        self.assertEqual(target.read_bytes(), original)

    def test_broken_backup_prevents_any_change(self):
        target = self.root / "SplashScreen.png"
        backup_dir = self.root / "backups"
        original = png_bytes()
        target.write_bytes(original)
        backup = backup_path_for(target, backup_dir)
        backup.parent.mkdir(parents=True)
        backup.write_bytes(b"broken")
        with self.assertRaises(Exception):
            apply_splash(Image.new("RGBA", (800, 450), "red"), target, backup_dir)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(backup.read_bytes(), b"broken")


if __name__ == "__main__":
    unittest.main()


class V11CreatorLayout(unittest.TestCase):
    """Widget'ları oluşturmadan çağrıları taklit ederek yerleşim taşmasını yakala."""

    def test_creator_controls_fit_and_keep_original_actions(self):
        created = []

        class Widget:
            def __init__(self, master, **options):
                self.master = master
                self.options = options
                self.placement = {}
                created.append(self)

            def place(self, **options):
                self.placement = options

            def grid_propagate(self, _value):
                pass

            def pack_propagate(self, _value):
                pass

            def destroy(self):
                pass

        obj = main.FortniteSplashMaker.__new__(main.FortniteSplashMaker)
        obj.main_container = object()
        obj.preview_label = None

        with (
            patch.object(main.ctk, "CTkFrame", Widget, create=True),
            patch.object(main.ctk, "CTkLabel", Widget, create=True),
            patch.object(main.ctk, "CTkButton", Widget, create=True),
            patch.object(main.ctk, "CTkFont", lambda **_kwargs: None, create=True),
        ):
            obj.create_creator_page()

        # Bütün açık koordinatlı bileşenler parent kartının içine sığmalı.
        for widget in created:
            parent = widget.master
            if not hasattr(parent, "options"):
                continue
            for dimension, coordinate in (("width", "x"), ("height", "y")):
                length = widget.options.get(dimension)
                available = parent.options.get(dimension)
                origin = widget.placement.get(coordinate)
                if isinstance(length, int) and isinstance(available, int) and isinstance(origin, int):
                    self.assertLessEqual(origin + length, available, widget.options.get("text"))

        expected_actions = {
            "Görsel Seç": "select_image",
            "Fortnite Klasörünü Değiştir": "select_fortnite_folder",
            "Fortnite'a Uygula": "apply_to_fortnite",
            "Kütüphaneye Ekle": "add_current_to_library",
            "PNG Olarak Kaydet": "save_as",
            "Yedekten Geri Yükle": "restore_previous",
            "Paket Sezon Görselini Uygula": "apply_bundled_season",
        }
        actual_actions = {
            widget.options["text"]: widget.options["command"].__name__
            for widget in created
            if "command" in widget.options
        }
        self.assertEqual(actual_actions, expected_actions)
