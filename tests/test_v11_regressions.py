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


class V11LibraryLayout(unittest.TestCase):
    """Kütüphane v1.1 arama ve seçim durumunu GUI açmadan doğrular."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.custom_dir = self.folder / "library"
        self.custom_dir.mkdir()
        self.season = self.folder / "current_season_splash.png"
        self.season.write_bytes(png_bytes())
        (self.custom_dir / "Minecraft Me.png").write_bytes(png_bytes())
        (self.custom_dir / "Fortnite Me.png").write_bytes(png_bytes())

    def test_library_search_filters_names_and_pinned_season(self):
        with (
            patch.object(main, "LIBRARY_DIR", self.custom_dir),
            patch.object(main, "CURRENT_SEASON_SPLASH_PATH", self.season),
        ):
            items = main.FortniteSplashMaker.get_library_items()
            self.assertEqual([k for _, k in items], ["season", "custom", "custom"])
            found = main.FortniteSplashMaker.get_library_items("   FORTNITE  ")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0][0].stem, "Fortnite Me")
            self.assertEqual(found[0][1], "custom")
            season = main.FortniteSplashMaker.get_library_items("paketle gelen sezon")
            self.assertEqual(len(season), 1)
            self.assertEqual(season[0][1], "season")
            self.assertEqual(main.FortniteSplashMaker.get_library_items("yok"), [])

    def test_library_highlight_selects_exact_card(self):
        a = self.custom_dir / "Fortnite Me.png"
        b = self.custom_dir / "Minecraft Me.png"
        first, second = FakeLabel(), FakeLabel()
        obj = types.SimpleNamespace(
            library_selected_path=a,
            library_selected_kind="custom",
            library_card_frames={(str(a), "custom"): first, (str(b), "custom"): second},
        )
        main.FortniteSplashMaker.update_library_selection_highlight(obj)
        self.assertEqual(first.options["border_color"], main.UI_ACCENT)
        self.assertEqual(first.options["border_width"], 2)
        self.assertEqual(second.options["border_color"], main.UI_BORDER)
        self.assertEqual(second.options["border_width"], 1)

    def test_selecting_bundled_season_disables_delete(self):
        class FakeImage:
            def __init__(self, **kwargs):
                self.options = kwargs

        statuses = []
        obj = types.SimpleNamespace(
            library_preview_image=None,
            library_preview_label=FakeLabel(),
            library_selected_path=None,
            library_selected_kind=None,
            image_reference_pool=deque(maxlen=256),
            library_name_label=FakeLabel(),
            library_info_label=FakeLabel(),
            library_apply_button=FakeLabel(),
            library_delete_button=FakeLabel(),
            load_rgba_image=lambda path: Image.open(path).convert("RGBA"),
            update_library_selection_highlight=lambda: None,
            set_status=statuses.append,
        )
        with patch.object(main.ctk, "CTkImage", FakeImage, create=True):
            main.FortniteSplashMaker.select_library_item(obj, self.season, "season")
        self.assertEqual(obj.library_apply_button.options["state"], "normal")
        self.assertEqual(obj.library_delete_button.options["state"], "disabled")
        self.assertIn("Paket", obj.library_name_label.options["text"])
        self.assertIsNotNone(obj.library_preview_image)


class V11LibraryPanelGeometry(unittest.TestCase):
    """Kütüphane panel çakışmasını gerçek pencere açmadan regresyonla kontrol et."""

    def test_library_gallery_and_preview_do_not_overlap(self):
        created = []

        class Widget:
            def __init__(self, master=None, **options):
                self.master = master
                self.options = dict(options)
                self.placement = {}
                created.append(self)

            def place(self, **options):
                self.placement = dict(options)

            def grid_propagate(self, _value):
                pass

            def pack_propagate(self, _value):
                pass

            def destroy(self):
                pass

        class Variable:
            def __init__(self, value=""):
                self.value = value

            def trace_add(self, _event, _callback):
                pass

            def get(self):
                return self.value

        obj = main.FortniteSplashMaker.__new__(main.FortniteSplashMaker)
        obj.main_container = object()
        obj.library_preview_label = None

        with (
            patch.object(main.ctk, "CTkFrame", Widget, create=True),
            patch.object(main.ctk, "CTkScrollableFrame", Widget, create=True),
            patch.object(main.ctk, "CTkLabel", Widget, create=True),
            patch.object(main.ctk, "CTkButton", Widget, create=True),
            patch.object(main.ctk, "CTkEntry", Widget, create=True),
            patch.object(main.ctk, "CTkFont", lambda **_kwargs: None, create=True),
            patch.object(main.ctk, "StringVar", Variable, create=True),
        ):
            obj.create_library_page()

        gallery = obj.library_gallery_panel
        preview = obj.library_preview_panel
        scroll = obj.library_scroll
        self.assertIs(scroll.master, gallery)
        self.assertEqual(gallery.placement["y"], preview.placement["y"])
        self.assertEqual(gallery.options["height"], preview.options["height"])

        gallery_right = gallery.placement["x"] + gallery.options["width"]
        preview_left = preview.placement["x"]
        self.assertGreaterEqual(preview_left - gallery_right, 18)
        self.assertLessEqual(preview_left + preview.options["width"], main.MAIN_WIDTH)
        self.assertLessEqual(preview.placement["y"] + preview.options["height"], main.MAIN_HEIGHT)

        # CustomTkinter ScrollableFrame, canvas + scrollbar için belirtilen
        # genişliğin dışına taşabilir. Bu fazlalığa 34px genişlik ve 20px
        # yükseklik toleransı ayır; buna rağmen dış panelin içinde kalmalı.
        self.assertLessEqual(
            scroll.placement["x"] + scroll.options["width"] + 34,
            gallery.options["width"],
        )
        self.assertLessEqual(
            scroll.placement["y"] + scroll.options["height"] + 20,
            gallery.options["height"],
        )
        self.assertGreaterEqual(
            scroll.options["width"], 2 * (main.CARD_W + 16)
        )

        # Kütüphane araç çubuğundaki kontroller de birbirinin üzerine binmemeli.
        toolbar_controls = [
            w for w in created
            if w.master is obj.library_page and
            ("command" in w.options or "textvariable" in w.options)
        ]
        toolbar_controls.sort(key=lambda widget: widget.placement["x"])
        self.assertEqual(len(toolbar_controls), 4)
        for left, right in zip(toolbar_controls, toolbar_controls[1:]):
            self.assertLessEqual(
                left.placement["x"] + left.options["width"] + 8,
                right.placement["x"],
            )

        self.assertEqual(obj.library_apply_button.options["command"].__name__, "apply_library_item")
        self.assertEqual(obj.library_delete_button.options["command"].__name__, "delete_library_item")
        self.assertEqual(obj.library_apply_button.options["state"], "disabled")


class V11LibraryCardSafety(unittest.TestCase):
    """Kart düzenlemesinin sınıf metotlarını ve resim yerleşimini bozmamasını sağlar."""

    def test_all_ui_callbacks_still_belong_to_app_class(self):
        required = {
            "create_library_card", "update_library_selection_highlight",
            "create_empty_library_preview", "clear_library_selection",
            "select_library_item", "apply_library_item", "delete_library_item",
            "open_library_folder", "detect_fortnite", "select_fortnite_folder",
            "apply_to_fortnite", "restore_previous", "apply_bundled_season",
            "create_statusbar", "set_status",
        }
        for name in sorted(required):
            with self.subTest(method=name):
                self.assertTrue(
                    callable(getattr(main.FortniteSplashMaker, name, None)),
                    f"{name} girinti hatası nedeniyle sınıf dışında kalmış",
                )

    def test_library_card_image_fits_frame_and_is_clickable(self):
        created = []

        class Widget:
            def __init__(self, master=None, **options):
                self.master = master
                self.options = options
                self.placement = {}
                self.events = {}
                created.append(self)

            def place(self, **options):
                self.placement = options

            def bind(self, event, callback):
                self.events[event] = callback

            def grid_propagate(self, _value):
                pass

            def pack_propagate(self, _value):
                pass

        class ImageWidget:
            def __init__(self, **kwargs):
                self.options = kwargs

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.png"
            path.write_bytes(png_bytes())
            selected = []
            app = types.SimpleNamespace(
                library_scroll=object(),
                library_selected_path=None,
                library_selected_kind=None,
                library_card_frames={},
                library_card_images=[],
                image_reference_pool=deque(maxlen=256),
                load_rgba_image=lambda p: Image.open(p).convert("RGBA"),
                select_library_item=lambda p, k: selected.append((p, k)),
            )
            with (
                patch.object(main.ctk, "CTkFrame", Widget, create=True),
                patch.object(main.ctk, "CTkLabel", Widget, create=True),
                patch.object(main.ctk, "CTkImage", ImageWidget, create=True),
                patch.object(main.ctk, "CTkFont", lambda **kwargs: None, create=True),
            ):
                card = main.FortniteSplashMaker.create_library_card(
                    app, path, "custom"
                )

            thumbnails = [w for w in created if w.master is card and w.options.get("width") == main.CARD_THUMB_W]
            self.assertEqual(len(thumbnails), 2)  # Küçük çerçeve + dosya adı
            frame = next(w for w in thumbnails if w.options.get("height") == main.CARD_THUMB_H)
            image_label = next(w for w in created if w.master is frame and "image" in w.options)
            self.assertEqual(frame.placement, {"x": 15, "y": 10})
            self.assertEqual(image_label.placement, {"x": 1, "y": 1})
            self.assertEqual(image_label.options["width"], main.CARD_THUMB_W - 2)
            self.assertEqual(image_label.options["height"], main.CARD_THUMB_H - 2)
            self.assertIn("<Button-1>", image_label.events)
            image_label.events["<Button-1>"](None)
            self.assertEqual(selected, [(path, "custom")])



class V11SettingsLayout(unittest.TestCase):
    """Ayarlar kartlarını ve işlev bağlantılarını GUI açmadan kontrol eder."""

    def test_settings_cards_fit_without_overlap(self):
        created = []

        class Widget:
            def __init__(self, master=None, **options):
                self.master = master
                self.options = options
                self.placement = {}
                created.append(self)

            def place(self, **kwargs):
                self.placement = kwargs

            def grid_propagate(self, _value):
                pass

            def pack_propagate(self, _value):
                pass

        app = main.FortniteSplashMaker.__new__(main.FortniteSplashMaker)
        app.main_container = object()
        with (
            patch.object(main.ctk, "CTkFrame", Widget, create=True),
            patch.object(main.ctk, "CTkLabel", Widget, create=True),
            patch.object(main.ctk, "CTkButton", Widget, create=True),
            patch.object(main.ctk, "CTkFont", lambda **_kwargs: None, create=True),
        ):
            app.create_settings_page()

        cards = [
            app.settings_install_card,
            app.settings_backup_card,
            app.settings_splash_card,
            app.settings_app_card,
        ]
        self.assertEqual(len(cards), 4)
        for card in cards:
            x, y = card.placement["x"], card.placement["y"]
            w, h = card.options["width"], card.options["height"]
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + w, main.MAIN_WIDTH)
            self.assertLessEqual(y + h, main.MAIN_HEIGHT)
            # Her bileşen kendi kartına sığmalı; taşan buton kalmamalı.
            for child in created:
                if child.master is not card or not child.placement:
                    continue
                if "width" in child.options and "height" in child.options:
                    self.assertLessEqual(child.placement["x"] + child.options["width"], w)
                    self.assertLessEqual(child.placement["y"] + child.options["height"], h)

        for i, left in enumerate(cards):
            ax, ay = left.placement["x"], left.placement["y"]
            aw, ah = left.options["width"], left.options["height"]
            for right in cards[i + 1:]:
                bx, by = right.placement["x"], right.placement["y"]
                bw, bh = right.options["width"], right.options["height"]
                overlap = ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
                self.assertFalse(overlap, "Ayarlar kartları üst üste gelmemeli")

        buttons = [w for w in created if "command" in w.options]
        actions = {w.options["command"].__name__ for w in buttons}
        self.assertEqual(actions, {
            "select_fortnite_folder", "reset_saved_fortnite_path",
            "open_backup_folder", "refresh_settings_page",
        })
        self.assertEqual(app.settings_open_backup_button.options["state"], "disabled")
        self.assertIn("1.0.0", " ".join(str(w.options.get("text", "")) for w in created))

    def test_backup_status_handles_missing_valid_and_corrupt_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "game" / "SplashScreen.png"
            target.parent.mkdir()
            target.write_bytes(png_bytes())
            backup_root = root / "backups"
            backup_root.mkdir()
            backup = backup_path_for(target, backup_root)
            app = types.SimpleNamespace(
                splash_path=target,
                settings_backup_badge=FakeLabel(),
                settings_backup_info_label=FakeLabel(),
                settings_open_backup_button=FakeLabel(),
            )
            with patch.object(main, "BACKUP_DIR", backup_root):
                main.FortniteSplashMaker.refresh_backup_status(app)
                self.assertIn("henüz yok", app.settings_backup_badge.options["text"])
                self.assertEqual(app.settings_open_backup_button.options["state"], "normal")

                backup.parent.mkdir(parents=True)
                backup.write_bytes(png_bytes())
                main.FortniteSplashMaker.refresh_backup_status(app)
                self.assertIn("mevcut", app.settings_backup_badge.options["text"])

                backup.write_bytes(b"not a valid png")
                main.FortniteSplashMaker.refresh_backup_status(app)
                self.assertIn("okunamıyor", app.settings_backup_badge.options["text"])
                self.assertIn("silme", app.settings_backup_info_label.options["text"])

                app.splash_path = None
                main.FortniteSplashMaker.refresh_backup_status(app)
                self.assertIn("Fortnite bulunamadı", app.settings_backup_badge.options["text"])

    def test_open_backup_folder_only_if_present(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            candidate = root / "backups"
            with (
                patch.object(main, "BACKUP_DIR", candidate),
                patch.object(main.os, "startfile", create=True) as start,
                patch.object(main.messagebox, "showwarning") as warning,
            ):
                main.FortniteSplashMaker.open_backup_folder(object())
                start.assert_not_called()
                warning.assert_called_once()
                candidate.mkdir()
                main.FortniteSplashMaker.open_backup_folder(object())
                start.assert_called_once_with(str(candidate))

    def test_active_status_badge_reacts_to_valid_splash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "SplashScreen.png"
            season = root / "season.png"
            img = png_bytes()
            target.write_bytes(img)
            season.write_bytes(img)
            app = types.SimpleNamespace(
                splash_path=target,
                current_splash_state="unknown",
                splash_state_badge=FakeLabel(),
                settings_splash_status_label=FakeLabel(),
                settings_active_badge=FakeLabel(),
            )
            app.file_sha256 = lambda path: main.FortniteSplashMaker.file_sha256(app, path)
            with patch.object(main, "CURRENT_SEASON_SPLASH_PATH", season):
                main.FortniteSplashMaker.update_active_splash_status(app)
                self.assertEqual(app.current_splash_state, "season")
                self.assertIn("Paket", app.settings_active_badge.options["text"])
                target.write_bytes(png_bytes((32, 67, 105, 255)))
                main.FortniteSplashMaker.update_active_splash_status(app)
                self.assertEqual(app.current_splash_state, "custom")
                self.assertIn("Özel", app.settings_active_badge.options["text"])


if __name__ == "__main__":
    unittest.main()
