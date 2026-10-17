import hashlib
import json
import os
import subprocess
import sys
from collections import deque
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps, UnidentifiedImageError

from .splash_files import (
    apply_splash, backup_path_for, read_png, restore_previous_splash,
)
from .ui.components import (
    UI_BG, UI_SURFACE, UI_SURFACE_RAISED, UI_SURFACE_DARK,
    UI_BORDER, UI_ACCENT, UI_ACCENT_HOVER, UI_TEXT,
    UI_TEXT_SECONDARY, UI_TEXT_MUTED,
    create_section_card, create_action_button, create_status_badge,
)
from .ui.feedback import FeedbackOverlay, describe_image_error
from .ui.dialogs import show_confirm_dialog, show_library_name_dialog


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "Fortnite Splash Maker"
APP_VERSION = "1.0.0"

WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760

TARGET_SIZE = (800, 450)

SPLASH_FILENAME = "SplashScreen.png"

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(
        getattr(
            sys,
            "_MEIPASS",
            APP_DIR
        )
    )
else:
    # Kaynak kod src/ altindadir; veri ve assets konumu proje kokunde kalir.
    APP_DIR = Path(__file__).resolve().parents[2]
    RESOURCE_DIR = APP_DIR

LIBRARY_DIR = APP_DIR / "library"
ASSETS_DIR = RESOURCE_DIR / "assets"
CURRENT_SEASON_SPLASH_PATH = ASSETS_DIR / "current_season_splash.png"
APP_ICON_PATH = ASSETS_DIR / "app_icon.ico"
SETTINGS_PATH = APP_DIR / "settings.json"
# Kurulum/portable klasöründen bağımsız: yeniden kurulum yedekleri silmez.
BACKUP_DIR = (
    Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    / "FortniteSplashMaker" / "backups"
)

SUPPORTED_FILES = "*.png *.jpg *.jpeg *.webp *.bmp"

# ============================================================
# FIXED UI SIZES
# ============================================================

MAIN_X = 35
MAIN_Y = 175
MAIN_WIDTH = 1110
MAIN_HEIGHT = 535

CREATOR_LEFT_X = 15
CREATOR_LEFT_Y = 15
CREATOR_LEFT_W = 520
CREATOR_LEFT_H = 505

CREATOR_RIGHT_X = 555
CREATOR_RIGHT_Y = 15
CREATOR_RIGHT_W = 540
CREATOR_RIGHT_H = 505

LIB_GALLERY_X = 15
# CTkScrollableFrame boyutuna scrollbar/kenar bosluklarini da ekliyor.
# Sabit dis panelleri kullanarak galerinin onizleme alanina tasmamasini sagla.
LIB_GALLERY_Y = 68
LIB_GALLERY_W = 625
LIB_GALLERY_H = 455
LIB_SCROLL_W = 574
LIB_SCROLL_H = 414

LIB_PREVIEW_X = 660
LIB_PREVIEW_Y = 68
LIB_PREVIEW_W = 435
LIB_PREVIEW_H = 455

CARD_W = 270
CARD_H = 190
CARD_THUMB_W = 240
CARD_THUMB_H = 135

PREVIEW_W = 460
PREVIEW_H = 259

LIB_PREVIEW_IMAGE_W = 372
LIB_PREVIEW_IMAGE_H = 209


# ============================================================
# APP
# ============================================================

class FortniteSplashMaker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ----------------------------------------------------
        # Window
        # ----------------------------------------------------
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)

        if APP_ICON_PATH.exists():
            try:
                self.iconbitmap(
                    str(APP_ICON_PATH)
                )
            except Exception:
                pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=UI_BG)

        self.update_idletasks()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = max((screen_width - WINDOW_WIDTH) // 2, 0)
        y = max((screen_height - WINDOW_HEIGHT) // 2, 0)

        self.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}"
        )

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------
        self.input_path = None
        self.original_image = None
        self.processed_image = None
        self.preview_ctk_image = None

        self.fortnite_install_path = None
        self.splash_path = None
        self.current_splash_state = "unknown"

        self.settings = self.load_settings()

        self.page_mode = ctk.StringVar(value="Oluştur")

        self.library_selected_path = None
        self.library_selected_kind = None
        self.library_preview_image = None
        self.library_card_images = []
        self.library_card_frames = {}
        self._library_search_after = None

        # Gecikmeli Tk yeniden çizimleri için son görsellerin referanslarını
        # tutuyoruz. Havuz sınırlı olduğu için uzun kullanımda büyümez.
        # Görüntülenen kartlar ayrıca library_card_images içinde saklanır.
        self.image_reference_pool = deque(maxlen=256)

        self.feedback_overlay = FeedbackOverlay(self)

        # ----------------------------------------------------
        # Persistent folders
        # ----------------------------------------------------
        LIBRARY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        ASSETS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------
        self.create_header()
        self.create_navigation()
        self.create_main_container()
        self.create_creator_page()
        self.create_library_page()
        self.create_settings_page()
        self.create_statusbar()

        self.show_page("Oluştur")

        # ----------------------------------------------------
        # Startup
        # ----------------------------------------------------
        self.after(250, self.detect_fortnite)
        self.after(400, self.refresh_library)

    # ========================================================
    # SETTINGS STORAGE
    # ========================================================

    def load_settings(self):
        if not SETTINGS_PATH.exists():
            return {}

        try:
            with open(
                SETTINGS_PATH,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if isinstance(data, dict):
                return data

        except (
            OSError,
            json.JSONDecodeError
        ):
            pass

        return {}

    def save_settings(self):
        try:
            with open(
                SETTINGS_PATH,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    self.settings,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

        except OSError as error:
            messagebox.showerror(
                "Ayarlar kaydedilemedi",
                str(error)
            )

    def save_fortnite_path_setting(self):
        if self.fortnite_install_path is not None:
            self.settings["fortnite_path"] = str(
                self.fortnite_install_path
            )

            self.settings.pop(
                "fortnite_path_is_direct_splash_folder",
                None
            )

            self.save_settings()

    def clear_fortnite_path_setting(self):
        self.settings.pop(
            "fortnite_path",
            None
        )

        self.settings.pop(
            "fortnite_path_is_direct_splash_folder",
            None
        )

        self.save_settings()

    def create_header(self):
        # Global başlık ve durum kartları; bütün sayfalarda görünür.
        ctk.CTkLabel(
            self,
            text="Fortnite Splash Maker",
            font=ctk.CTkFont(size=29, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=40, y=27)

        ctk.CTkLabel(
            self,
            text="Fortnite başlangıç ekranlarını hazırla, sakla ve güvenle uygula",
            font=ctk.CTkFont(size=14),
            text_color=UI_TEXT_SECONDARY,
        ).place(x=40, y=72)

        self.fortnite_badge = create_status_badge(
            self,
            text="Fortnite aranıyor...",
            width=186,
            height=29,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.fortnite_badge.place(x=950, y=42)

        self.splash_state_badge = create_status_badge(
            self,
            text="Splash durumu bilinmiyor",
            width=186,
            height=27,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        )
        self.splash_state_badge.place(x=950, y=77)

    # ========================================================
    # NAVIGATION
    # ========================================================

    def create_navigation(self):
        self.nav = ctk.CTkSegmentedButton(
            self,
            values=["Oluştur", "Kütüphane", "Ayarlar"],
            variable=self.page_mode,
            width=350,
            height=36,
            corner_radius=9,
            fg_color=UI_SURFACE,
            selected_color=UI_ACCENT,
            selected_hover_color=UI_ACCENT_HOVER,
            unselected_color=UI_SURFACE,
            unselected_hover_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT,
            command=self.show_page,
        )
        self.nav.place(x=(WINDOW_WIDTH - 350) // 2, y=125)

    def show_page(self, page):
        # Önceki ekrana ait hata/bilgi kutusu diğer sayfalara taşınmasın.
        self.feedback_overlay.dismiss()
        self.page_mode.set(page)

        self.creator_page.place_forget()
        self.library_page.place_forget()
        self.settings_page.place_forget()

        if page == "Oluştur":
            self.creator_page.place(
                x=0,
                y=0
            )

        elif page == "Kütüphane":
            self.library_page.place(
                x=0,
                y=0
            )
            self.refresh_library()

        else:
            self.settings_page.place(
                x=0,
                y=0
            )
            self.refresh_settings_page()

    def create_main_container(self):
        self.main_container = ctk.CTkFrame(
            self,
            width=MAIN_WIDTH,
            height=MAIN_HEIGHT,
            corner_radius=13,
            fg_color=UI_BG,
        )
        self.main_container.place(x=MAIN_X, y=MAIN_Y)
        self.main_container.grid_propagate(False)
        self.main_container.pack_propagate(False)

    # ========================================================
    # CREATOR PAGE
    # ========================================================

    def create_creator_page(self):
        self.creator_page = ctk.CTkFrame(
            self.main_container,
            width=MAIN_WIDTH,
            height=MAIN_HEIGHT,
            fg_color="transparent"
        )

        self.creator_page.grid_propagate(False)
        self.creator_page.pack_propagate(False)

        self.create_creator_left_panel()
        self.create_creator_right_panel()

    # ========================================================
    # CREATOR LEFT
    # ========================================================

    def create_creator_left_panel(self):
        panel = create_section_card(
            self.creator_page,
            width=CREATOR_LEFT_W,
            height=CREATOR_LEFT_H,
            corner_radius=16,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
        )
        panel.place(x=CREATOR_LEFT_X, y=CREATOR_LEFT_Y)
        panel.grid_propagate(False)
        panel.pack_propagate(False)

        ctk.CTkLabel(
            panel,
            text="Görsel Önizleme",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=20, y=20)

        # Statik format etiketi: görselin işleneceği gerçek çıkış biçimi.
        ctk.CTkLabel(
            panel,
            width=152,
            height=26,
            corner_radius=8,
            fg_color=UI_SURFACE_RAISED,
            text="16:9  •  800×450",
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        ).place(x=345, y=19)

        # Tam 16:9'luk 480x270 önizleme alanı.
        self.preview_box = ctk.CTkFrame(
            panel,
            width=480,
            height=270,
            corner_radius=12,
            fg_color=UI_SURFACE_DARK,
            border_width=1,
            border_color=UI_BORDER,
        )
        self.preview_box.place(x=20, y=66)
        self.preview_box.grid_propagate(False)
        self.preview_box.pack_propagate(False)
        self.create_empty_creator_preview()

        ctk.CTkLabel(
            panel,
            text="SEÇİLİ DOSYA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=UI_TEXT_MUTED,
        ).place(x=20, y=354)

        self.file_info = ctk.CTkLabel(
            panel,
            width=480,
            height=28,
            text="Henüz görsel seçilmedi",
            font=ctk.CTkFont(size=13),
            anchor="w",
            text_color=UI_TEXT_SECONDARY,
        )
        self.file_info.place(x=20, y=377)

        # Kullanıcıya işlemin dosya formatını değiştirdiğini net gösterir.
        format_frame = ctk.CTkFrame(
            panel,
            width=480,
            height=66,
            corner_radius=10,
            fg_color=UI_SURFACE_DARK,
        )
        format_frame.place(x=20, y=420)
        format_frame.grid_propagate(False)
        format_frame.pack_propagate(False)
        # Bildirim gelirse bu bilgi kutusu geçici olarak gizlenir.
        # Bildirim kapatılınca normal format açıklaması geri gösterilir.
        self.feedback_overlay.register_creator_slot(panel, format_frame)

        ctk.CTkLabel(
            format_frame,
            text="FORTNITE İÇİN HAZIRLANIR",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8FC3F9",
        ).place(x=14, y=9)

        self.output_info = ctk.CTkLabel(
            format_frame,
            width=450,
            height=23,
            text="Merkezden kırpma   •   800×450   •   PNG / RGBA",
            anchor="w",
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        )
        self.output_info.place(x=14, y=33)

    # ========================================================
    # CREATOR RIGHT
    # ========================================================

    def create_creator_right_panel(self):
        panel = create_section_card(
            self.creator_page,
            width=CREATOR_RIGHT_W,
            height=CREATOR_RIGHT_H,
            corner_radius=16,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
        )
        panel.place(x=CREATOR_RIGHT_X, y=CREATOR_RIGHT_Y)
        panel.grid_propagate(False)
        panel.pack_propagate(False)

        def section_heading(text, y):
            ctk.CTkLabel(
                panel,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=UI_TEXT,
            ).place(x=20, y=y)

        section_heading("01   Görsel seçimi", 15)
        create_action_button(
            panel,
            variant="secondary",
            text="Görsel Seç",
            width=500,
            height=42,
            corner_radius=10,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            border_width=1,
            border_color=UI_BORDER,
            text_color=UI_TEXT,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.select_image,
        ).place(x=20, y=46)

        ctk.CTkLabel(
            panel,
            text="PNG, JPG, WEBP, BMP  •  Otomatik 16:9 kırpma",
            width=500,
            height=27,
            anchor="w",
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        ).place(x=20, y=95)

        ctk.CTkFrame(
            panel, width=500, height=1, fg_color=UI_BORDER,
        ).place(x=20, y=137)

        section_heading("02   Fortnite kurulumu", 144)
        self.path_label = ctk.CTkLabel(
            panel,
            text="Fortnite aranıyor...",
            width=500,
            height=25,
            anchor="w",
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        )
        self.path_label.place(x=20, y=171)

        ctk.CTkButton(
            panel,
            text="Fortnite Klasörünü Değiştir",
            width=500,
            height=33,
            corner_radius=9,
            fg_color="transparent",
            hover_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT,
            border_width=1,
            border_color=UI_BORDER,
            command=self.select_fortnite_folder,
        ).place(x=20, y=198)

        ctk.CTkFrame(
            panel, width=500, height=1, fg_color=UI_BORDER,
        ).place(x=20, y=241)

        section_heading("03   İşlemler", 248)

        # Ekrandaki tek birincil eylem.
        create_action_button(
            panel,
            variant="primary",
            text="Fortnite'a Uygula",
            width=500,
            height=43,
            corner_radius=10,
            fg_color=UI_ACCENT,
            hover_color=UI_ACCENT_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.apply_to_fortnite,
        ).place(x=20, y=278)

        ctk.CTkButton(
            panel,
            text="Kütüphaneye Ekle",
            width=243,
            height=36,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            text_color=UI_TEXT,
            command=self.add_current_to_library,
        ).place(x=20, y=329)

        ctk.CTkButton(
            panel,
            text="PNG Olarak Kaydet",
            width=243,
            height=36,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            text_color=UI_TEXT,
            command=self.save_as,
        ).place(x=277, y=329)

        # Yedek ve paket sezon görseli bilerek ayrı eylemler olarak kalır.
        recovery_panel = ctk.CTkFrame(
            panel,
            width=500,
            height=113,
            corner_radius=11,
            fg_color=UI_SURFACE_DARK,
        )
        recovery_panel.place(x=20, y=378)
        recovery_panel.grid_propagate(False)
        recovery_panel.pack_propagate(False)

        ctk.CTkLabel(
            recovery_panel,
            text="04   Geri yükleme",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=12, y=7)

        ctk.CTkLabel(
            recovery_panel,
            text="İlk değişiklik öncesi yedek veya uygulamayla gelen sezon görseli",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
            width=475,
            anchor="w",
        ).place(x=12, y=33)

        ctk.CTkButton(
            recovery_panel,
            text="Yedekten Geri Yükle",
            width=232,
            height=37,
            corner_radius=8,
            fg_color="transparent",
            hover_color=UI_SURFACE_RAISED,
            border_width=1,
            border_color=UI_BORDER,
            text_color=UI_TEXT,
            command=self.restore_previous,
        ).place(x=12, y=66)

        ctk.CTkButton(
            recovery_panel,
            text="Paket Sezon Görselini Uygula",
            width=232,
            height=37,
            corner_radius=8,
            fg_color="transparent",
            hover_color=UI_SURFACE_RAISED,
            border_width=1,
            border_color=UI_BORDER,
            text_color=UI_TEXT,
            command=self.apply_bundled_season,
        ).place(x=256, y=66)

    # ========================================================
    # LIBRARY PAGE
    # ========================================================

    def create_library_page(self):
        """Kütüphane: sabit ve çakışmayan galeri + önizleme yerleşimi."""
        self.library_page = ctk.CTkFrame(
            self.main_container,
            width=MAIN_WIDTH,
            height=MAIN_HEIGHT,
            fg_color="transparent",
        )
        self.library_page.grid_propagate(False)
        self.library_page.pack_propagate(False)

        # Üst satır: başlık ve sayaç solda, arama ve işlemler aynı hizada.
        ctk.CTkLabel(
            self.library_page,
            text="Splash Kütüphanesi",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=UI_TEXT,
            anchor="w",
            width=300,
            height=27,
        ).place(x=15, y=2)

        self.library_count_label = ctk.CTkLabel(
            self.library_page,
            text="Görseller yükleniyor...",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
            anchor="w",
            width=300,
            height=20,
        )
        self.library_count_label.place(x=15, y=33)

        self.library_search_var = ctk.StringVar(value="")
        self.library_search_entry = ctk.CTkEntry(
            self.library_page,
            textvariable=self.library_search_var,
            width=307,
            height=36,
            placeholder_text="Görsel adıyla ara...",
            placeholder_text_color=UI_TEXT_SECONDARY,
            fg_color=UI_SURFACE,
            border_color=UI_BORDER,
            text_color=UI_TEXT,
            corner_radius=9,
        )
        self.library_search_entry.place(x=334, y=9)
        self.library_search_var.trace_add(
            "write", self.on_library_search_change
        )

        ctk.CTkButton(
            self.library_page,
            text="Klasörü Aç",
            width=133,
            height=36,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            text_color=UI_TEXT,
            command=self.open_library_folder,
        ).place(x=659, y=9)

        ctk.CTkButton(
            self.library_page,
            text="Görsel Ekle",
            width=135,
            height=36,
            corner_radius=9,
            fg_color=UI_ACCENT,
            hover_color=UI_ACCENT_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.add_external_to_library,
        ).place(x=802, y=9)

        ctk.CTkButton(
            self.library_page,
            text="Yenile",
            width=147,
            height=36,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            text_color=UI_TEXT,
            command=self.refresh_library,
        ).place(x=947, y=9)

        # ScrollableFrame doğrudan ana sayfaya konursa scrollbar ve widget
        # boşluklarıyla beklenenden geniş olabiliyor. Dış çerçeve panelin
        # gerçek sınırını belirler; kaydırma alanını panelin içinde tutarız.
        self.library_gallery_panel = create_section_card(
            self.library_page,
            width=LIB_GALLERY_W,
            height=LIB_GALLERY_H,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
            corner_radius=15,
        )
        self.library_gallery_panel.place(x=LIB_GALLERY_X, y=LIB_GALLERY_Y)
        self.library_gallery_panel.grid_propagate(False)
        self.library_gallery_panel.pack_propagate(False)

        self.library_scroll = ctk.CTkScrollableFrame(
            self.library_gallery_panel,
            width=LIB_SCROLL_W,
            height=LIB_SCROLL_H,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=UI_SURFACE_RAISED,
            scrollbar_button_hover_color=UI_ACCENT,
        )
        self.library_scroll.place(x=10, y=10)

        preview_panel = create_section_card(
            self.library_page,
            width=LIB_PREVIEW_W,
            height=LIB_PREVIEW_H,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
            corner_radius=15,
        )
        preview_panel.place(x=LIB_PREVIEW_X, y=LIB_PREVIEW_Y)
        preview_panel.grid_propagate(False)
        preview_panel.pack_propagate(False)

        ctk.CTkLabel(
            preview_panel,
            text="Seçili Splash",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=UI_TEXT,
            anchor="w",
            width=260,
            height=28,
        ).place(x=21, y=15)

        self.library_preview_background = ctk.CTkFrame(
            preview_panel,
            width=395,
            height=231,
            fg_color=UI_SURFACE_DARK,
            border_color=UI_BORDER,
            border_width=1,
            corner_radius=12,
        )
        self.library_preview_background.place(x=20, y=51)
        self.library_preview_background.grid_propagate(False)
        self.library_preview_background.pack_propagate(False)

        self.library_preview_panel = preview_panel
        self.create_empty_library_preview()

        self.library_name_label = ctk.CTkLabel(
            preview_panel,
            width=395,
            height=27,
            text="-",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=UI_TEXT,
        )
        self.library_name_label.place(x=20, y=289)

        self.library_info_label = ctk.CTkLabel(
            preview_panel,
            width=395,
            height=23,
            text="Önizlemek için soldan bir görsel seçin.",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_SECONDARY,
        )
        self.library_info_label.place(x=20, y=315)

        self.library_apply_button = create_action_button(
            preview_panel,
            text="Fortnite'a Uygula",
            width=395,
            height=42,
            corner_radius=10,
            fg_color=UI_ACCENT,
            hover_color=UI_ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.apply_library_item,
            state="disabled",
        )
        self.library_apply_button.place(x=20, y=355)

        self.library_delete_button = ctk.CTkButton(
            preview_panel,
            text="Kütüphaneden Sil",
            width=395,
            height=35,
            corner_radius=9,
            fg_color="transparent",
            hover_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT_SECONDARY,
            border_color=UI_BORDER,
            border_width=1,
            command=self.delete_library_item,
            state="disabled",
        )
        self.library_delete_button.place(x=20, y=407)

    def on_library_search_change(self, *_args):
        """Aramada her tuş vuruşunda tüm küçük görselleri tekrar yükleme."""
        if self._library_search_after is not None:
            self.after_cancel(self._library_search_after)
        self._library_search_after = self.after(180, self.refresh_library)

    @staticmethod
    def get_library_items(search_text=""):
        """Paket sezon görseli ve kullanıcı PNG'lerini süzerek listeler."""
        items = []
        if CURRENT_SEASON_SPLASH_PATH.is_file():
            items.append((CURRENT_SEASON_SPLASH_PATH, "season"))
        items.extend(
            (item, "custom")
            for item in sorted(
                LIBRARY_DIR.glob("*.png"),
                key=lambda path: path.name.casefold(),
            )
        )
        query = " ".join(search_text.casefold().split())
        if not query:
            return items
        return [
            (path, kind)
            for path, kind in items
            if query in (
                "paketle gelen sezon " + path.stem.casefold()
                if kind == "season" else path.stem.casefold()
            )
        ]

    # ========================================================
    # SAFETY / VALIDATION HELPERS
    # ========================================================

    def load_rgba_image(self, path):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Görsel dosyası bulunamadı:\n{path}"
            )

        try:
            with Image.open(path) as source:
                source.load()
                return source.convert("RGBA")

        except UnidentifiedImageError as error:
            raise ValueError(
                f"Geçerli bir görsel dosyası değil:\n{path}"
            ) from error

        except OSError as error:
            raise OSError(
                f"Görsel okunamadı:\n{path}\n\n{error}"
            ) from error

    def fortnite_target_is_ready(self):
        if self.splash_path is None:
            self.show_feedback(
                "warning", "Fortnite bulunamadı",
                "Devam etmek için önce Fortnite kurulum klasörünü seç.",
            )
            return False

        splash_parent = Path(
            self.splash_path
        ).parent

        if not splash_parent.is_dir():
            messagebox.showerror(
                "Fortnite yolu geçersiz",
                (
                    "Easy Anti-Cheat klasörü artık bulunamıyor.\n\n"
                    "Fortnite güncellenmiş veya taşınmış olabilir. "
                    "Fortnite klasörünü yeniden seç."
                )
            )
            return False

        target = Path(self.splash_path)
        if target.is_symlink():
            messagebox.showerror(
                "Geçersiz splash dosyası",
                "SplashScreen.png bir sembolik bağlantı. Gerçek Fortnite klasörünü seç."
            )
            return False

        if not target.is_file():
            messagebox.showerror(
                "Splash dosyası bulunamadı",
                (
                    "Fortnite klasörü mevcut ancak SplashScreen.png dosyası "
                    "bulunamadı.\n\nFortnite kurulumunu kontrol et veya "
                    "klasörü yeniden seç."
                )
            )
            return False

        return True

    def save_rgba_png(self, image, destination):
        destination = Path(destination)

        prepared = ImageOps.fit(
            image.convert("RGBA"),
            TARGET_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        ).convert("RGBA")

        prepared.save(
            destination,
            format="PNG"
        )

    # ========================================================
    # SETTINGS PAGE
    # ========================================================

    def create_settings_page(self):
        """v1.1 Ayarlar: Fortnite, yedek ve uygulama bilgileri ayrı kartlar."""
        self.settings_page = ctk.CTkFrame(
            self.main_container,
            width=MAIN_WIDTH,
            height=MAIN_HEIGHT,
            fg_color="transparent",
        )
        self.settings_page.grid_propagate(False)
        self.settings_page.pack_propagate(False)

        ctk.CTkLabel(
            self.settings_page,
            text="Ayarlar",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=UI_TEXT,
            anchor="w",
            width=340,
            height=28,
        ).place(x=15, y=2)
        ctk.CTkLabel(
            self.settings_page,
            text="Fortnite kurulumu, splash yedekleri ve uygulama bilgileri",
            font=ctk.CTkFont(size=12),
            text_color=UI_TEXT_MUTED,
            anchor="w",
            width=630,
            height=23,
        ).place(x=15, y=32)

        # Sol üst: Fortnite dosyasının bağlı olduğu klasör.
        install_card = create_section_card(
            self.settings_page,
            width=640,
            height=225,
            corner_radius=15,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
        )
        install_card.place(x=15, y=68)
        install_card.grid_propagate(False)
        install_card.pack_propagate(False)
        self.settings_install_card = install_card

        ctk.CTkLabel(
            install_card,
            text="Fortnite Kurulumu",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=20, y=16)
        self.settings_install_badge = create_status_badge(
            install_card,
            text="Kontrol ediliyor",
            width=148,
            height=26,
            corner_radius=8,
            fg_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
        )
        self.settings_install_badge.place(x=468, y=16)

        ctk.CTkLabel(
            install_card,
            text="KURULUM DİZİNİ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=UI_TEXT_MUTED,
        ).place(x=20, y=54)

        path_box = ctk.CTkFrame(
            install_card,
            width=600,
            height=63,
            corner_radius=9,
            fg_color=UI_SURFACE_DARK,
        )
        path_box.place(x=20, y=77)
        path_box.grid_propagate(False)
        path_box.pack_propagate(False)
        self.settings_path_label = ctk.CTkLabel(
            path_box,
            width=566,
            height=55,
            text="Fortnite yolu kontrol ediliyor...",
            anchor="w",
            justify="left",
            wraplength=560,
            font=ctk.CTkFont(size=12),
            text_color=UI_TEXT_SECONDARY,
        )
        self.settings_path_label.place(x=13, y=4)

        ctk.CTkButton(
            install_card,
            text="Fortnite Klasörünü Değiştir",
            width=291,
            height=40,
            corner_radius=9,
            fg_color=UI_ACCENT,
            hover_color=UI_ACCENT_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_fortnite_folder,
        ).place(x=20, y=161)
        ctk.CTkButton(
            install_card,
            text="Kayıtlı Yolu Sıfırla",
            width=291,
            height=40,
            corner_radius=9,
            fg_color="transparent",
            hover_color=UI_SURFACE_RAISED,
            border_width=1,
            border_color=UI_BORDER,
            text_color=UI_TEXT_SECONDARY,
            command=self.reset_saved_fortnite_path,
        ).place(x=329, y=161)

        # Sol alt: Kurulumdan bağımsız saklanan ilk splash yedeği.
        backup_card = create_section_card(
            self.settings_page,
            width=640,
            height=214,
            corner_radius=15,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
        )
        backup_card.place(x=15, y=307)
        backup_card.grid_propagate(False)
        backup_card.pack_propagate(False)
        self.settings_backup_card = backup_card

        ctk.CTkLabel(
            backup_card,
            text="Splash Yedekleme",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=20, y=17)
        self.settings_backup_badge = create_status_badge(
            backup_card,
            text="Yedek kontrol ediliyor",
            width=175,
            height=26,
            corner_radius=8,
            fg_color=UI_SURFACE_RAISED,
            text_color=UI_TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
        )
        self.settings_backup_badge.place(x=441, y=17)

        self.settings_backup_info_label = ctk.CTkLabel(
            backup_card,
            width=599,
            height=45,
            text="Yedek durumu kontrol ediliyor...",
            anchor="w",
            justify="left",
            wraplength=584,
            font=ctk.CTkFont(size=12),
            text_color=UI_TEXT_SECONDARY,
        )
        self.settings_backup_info_label.place(x=20, y=53)

        ctk.CTkLabel(
            backup_card,
            text=f"Konum: {BACKUP_DIR}",
            width=599,
            height=24,
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
        ).place(x=20, y=108)

        self.settings_open_backup_button = create_action_button(
            backup_card,
            text="Yedek Klasörünü Aç",
            width=292,
            height=38,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            text_color=UI_TEXT,
            command=self.open_backup_folder,
            state="disabled",
        )
        self.settings_open_backup_button.place(x=20, y=153)
        ctk.CTkLabel(
            backup_card,
            text="Yedek, ilk değiştirme öncesinde saklanır.\nSezon görselinden farklı olabilir.",
            width=281,
            height=40,
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
        ).place(x=330, y=151)

        # Sağ üst: dosya bütünlüğünden hesaplanan splash durumu.
        splash_card = create_section_card(
            self.settings_page,
            width=420,
            height=262,
            corner_radius=15,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
        )
        splash_card.place(x=675, y=68)
        splash_card.grid_propagate(False)
        splash_card.pack_propagate(False)
        self.settings_splash_card = splash_card

        ctk.CTkLabel(
            splash_card,
            text="Aktif Splash",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=20, y=16)
        self.settings_active_badge = create_status_badge(
            splash_card,
            width=380,
            height=42,
            text="Kontrol ediliyor...",
            corner_radius=10,
            fg_color=UI_SURFACE_RAISED,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=UI_TEXT_SECONDARY,
        )
        self.settings_active_badge.place(x=20, y=57)

        self.settings_splash_status_label = ctk.CTkLabel(
            splash_card,
            width=378,
            height=55,
            text="Aktif splash durumu kontrol ediliyor...",
            anchor="w",
            justify="left",
            wraplength=375,
            font=ctk.CTkFont(size=12),
            text_color=UI_TEXT_SECONDARY,
        )
        self.settings_splash_status_label.place(x=20, y=107)

        ctk.CTkLabel(
            splash_card,
            text="Durum, Fortnite splash dosyasının\niçeriği doğrulanarak belirlenir.",
            width=380,
            height=39,
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
        ).place(x=20, y=159)

        ctk.CTkButton(
            splash_card,
            text="Durumu Yenile",
            width=380,
            height=36,
            corner_radius=9,
            fg_color=UI_SURFACE_RAISED,
            hover_color="#304560",
            text_color=UI_TEXT,
            command=self.refresh_settings_page,
        ).place(x=20, y=209)

        # Sağ alt: sürüm ve uygulamaya ait veri dosyaları.
        app_card = create_section_card(
            self.settings_page,
            width=420,
            height=177,
            corner_radius=15,
            fg_color=UI_SURFACE,
            border_width=1,
            border_color=UI_BORDER,
        )
        app_card.place(x=675, y=344)
        app_card.grid_propagate(False)
        app_card.pack_propagate(False)
        self.settings_app_card = app_card

        ctk.CTkLabel(
            app_card,
            text="Uygulama",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=UI_TEXT,
        ).place(x=20, y=15)
        ctk.CTkLabel(
            app_card,
            text=f"Fortnite Splash Maker  •  v{APP_VERSION}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=UI_TEXT_SECONDARY,
            anchor="w",
            width=375,
        ).place(x=20, y=56)
        ctk.CTkLabel(
            app_card,
            text="Windows masaüstü uygulaması  •  Python / CustomTkinter",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
            anchor="w",
            width=380,
        ).place(x=20, y=89)
        ctk.CTkLabel(
            app_card,
            text="Kullanıcı görselleri library/ altında; manuel\nFortnite yolu settings.json dosyasında saklanır.",
            width=380,
            height=41,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=UI_TEXT_MUTED,
        ).place(x=20, y=119)

    def refresh_settings_page(self):
        """Ayarlar görünümündeki tüm durumları dosyaları değiştirmeden yenile."""
        if not hasattr(self, "settings_path_label"):
            return

        saved_path = self.settings.get("fortnite_path")
        active = self.splash_path is not None and Path(self.splash_path).is_file()
        if active:
            active_path = (
                self.fortnite_install_path
                if self.fortnite_install_path is not None
                else Path(self.splash_path).parent
            )
            label = (
                "Aktif ve kayıtlı yol:"
                if saved_path and Path(saved_path) == Path(active_path)
                else "Aktif Fortnite yolu:"
            )
            text = f"{label}\n{active_path}"
        elif saved_path:
            text = f"Kaydedilen Fortnite yolu şu anda kullanılamıyor:\n{saved_path}"
        else:
            text = "Henüz bir Fortnite yolu algılanmadı veya kaydedilmedi."
        self.settings_path_label.configure(text=text)

        if hasattr(self, "settings_install_badge"):
            self.settings_install_badge.configure(
                text="Fortnite bulundu ✓" if active else "Fortnite bulunamadı",
                fg_color="#1B3A35" if active else UI_SURFACE_RAISED,
                text_color="#9CE0C3" if active else UI_TEXT_SECONDARY,
            )
        if hasattr(self, "settings_backup_badge"):
            self.refresh_backup_status()
        self.update_active_splash_status()

    def refresh_backup_status(self):
        """İlk değişiklik yedeğinin gerçekten okunabilir olduğunu göster."""
        target = self.splash_path
        if target is None:
            status = "Fortnite bulunamadı"
            message = "Yedeği kontrol etmek için önce bir Fortnite kurulumu seç."
            color = UI_TEXT_SECONDARY
            bg = UI_SURFACE_RAISED
        else:
            try:
                backup = backup_path_for(target, BACKUP_DIR)
                if backup.is_file():
                    read_png(backup)
                    status = "Yedek mevcut ✓"
                    message = "Bu kurulum için ilk değişiklik öncesindeki splash güvenle saklanıyor."
                    color, bg = "#9CE0C3", "#1B3A35"
                else:
                    status = "Yedek henüz yok"
                    message = "Bu kurulum için yedek bulunamadı. İlk splash değişiminde oluşturulur."
                    color, bg = UI_TEXT_SECONDARY, UI_SURFACE_RAISED
            except (OSError, ValueError, RuntimeError):
                status = "Yedek okunamıyor"
                message = "Yedek doğrulanamadı. Dosyayı kontrol et; mevcut yedeği silme."
                color, bg = "#F2B5AA", "#49302F"

        self.settings_backup_badge.configure(
            text=status,
            fg_color=bg,
            text_color=color,
        )
        self.settings_backup_info_label.configure(text=message)
        self.settings_open_backup_button.configure(
            state="normal" if BACKUP_DIR.is_dir() else "disabled"
        )

    def open_backup_folder(self):
        """Uygulama dışındaki kalıcı yedekleri silmeden klasörünü göster."""
        if not BACKUP_DIR.is_dir():
            self.show_feedback(
                "warning", "Yedek klasörü bulunamadı",
                "Henüz yedek oluşturulmadı. İlk splash değişiminde yedek alınır.",
            )
            return
        try:
            os.startfile(str(BACKUP_DIR))
        except OSError as error:
            messagebox.showerror("Yedek klasörü açılamadı", str(error))

    def reset_saved_fortnite_path(self):
        saved_path = self.settings.get(
            "fortnite_path"
        )

        if not saved_path:
            self.show_toast(
                "Kayıtlı Fortnite yolu zaten boş."
            )
            self.refresh_settings_page()
            return

        answer = self.ask_confirm(
            "Kayıtlı Yolu Sıfırla",
            (
                "Kaydedilmiş Fortnite klasörü ayarlardan "
                "kaldırılsın mı?\n\n"
                "Uygulama tekrar otomatik algılama yapacak."
            ),
            confirm_text="Sıfırla",
            cancel_text="Vazgeç"
        )

        if not answer:
            return

        self.clear_fortnite_path_setting()

        self.fortnite_install_path = None
        self.splash_path = None

        self.set_fortnite_not_found()
        self.refresh_settings_page()

        self.after(
            100,
            self.detect_fortnite
        )

        self.show_toast(
            "Kayıtlı Fortnite yolu sıfırlandı."
        )

    # ========================================================
    # IMAGE SELECTION
    # ========================================================

    def select_image(self):
        filename = filedialog.askopenfilename(
            title="Splash görselini seç",
            filetypes=[
                ("Görseller", SUPPORTED_FILES),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WEBP", "*.webp"),
                ("BMP", "*.bmp"),
                ("Tüm Dosyalar", "*.*")
            ]
        )

        if not filename:
            return

        self.load_input_image(
            Path(filename)
        )

    def load_input_image(self, path):
        try:
            self.input_path = Path(path)

            self.original_image = self.load_rgba_image(
                self.input_path
            )

            width, height = (
                self.original_image.size
            )

            display_name = self.input_path.name

            if len(display_name) > 46:
                display_name = (
                    display_name[:43]
                    + "..."
                )

            self.file_info.configure(
                text=(
                    f"{display_name}"
                    f"  •  "
                    f"{width}×{height}"
                )
            )

            self.process_image()
            # Önceki geçersiz seçimden kalan hata kartını kaldır.
            self.feedback_overlay.dismiss()

            self.set_status(
                "Görsel hazır."
            )

        except Exception as error:
            self.input_path = None
            self.original_image = None
            self.processed_image = None
            self.clear_creator_preview()
            self.set_status("Görsel yüklenemedi.")

            info = describe_image_error(error, path)
            self.show_feedback(
                info.level, info.title, info.message, details=info.details,
            )

    def create_empty_creator_preview(self):
        """Tamamen boş bir önizleme widget'ı oluşturur.

        CTkLabel üzerinde image=None bazen Tk'nin eski görüntüyü ekranda
        bırakmasına neden olabildiğinden widget'ı yeniden oluşturuyoruz.
        """
        previous = getattr(self, "preview_label", None)
        if previous is not None:
            previous.destroy()

        self.preview_label = ctk.CTkLabel(
            self.preview_box,
            width=460,
            height=259,
            text="Bir görsel seçerek başla\n\nPNG • JPG • WEBP • BMP",
            text_color=UI_TEXT_MUTED,
            font=ctk.CTkFont(size=16)
        )
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")

    def clear_creator_preview(self):
        """Geçersiz seçimde görsel verisini ve görüntü widget'ını sıfırlar."""
        if self.preview_ctk_image is not None:
            self.image_reference_pool.append(self.preview_ctk_image)
        self.preview_ctk_image = None
        self.create_empty_creator_preview()
        self.file_info.configure(text="Henüz görsel seçilmedi")
        self.preview_label.update_idletasks()

    def process_image(self):
        if self.original_image is None:
            return

        self.processed_image = ImageOps.fit(
            self.original_image,
            TARGET_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        ).convert("RGBA")

        self.update_preview()

    # ========================================================
    # PREVIEW
    # ========================================================

    def update_preview(self):
        if self.processed_image is None:
            return

        preview = self.processed_image.resize(
            (
                PREVIEW_W,
                PREVIEW_H
            ),
            Image.Resampling.LANCZOS
        )

        if self.preview_ctk_image is not None:
            self.image_reference_pool.append(self.preview_ctk_image)

        self.preview_ctk_image = ctk.CTkImage(
            light_image=preview,
            dark_image=preview,
            size=(
                PREVIEW_W,
                PREVIEW_H
            )
        )

        self.preview_label.configure(
            image=self.preview_ctk_image,
            text=""
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save_processed(self, path):
        if self.processed_image is None:
            raise ValueError(
                "Önce bir görsel seç."
            )

        self.save_rgba_png(
            self.processed_image,
            path
        )

    def save_as(self):
        if self.processed_image is None:
            self.show_feedback(
                "warning", "Görsel seçilmedi",
                "Kaydetmek için önce bir görsel seç.",
            )
            return

        filename = filedialog.asksaveasfilename(
            title="SplashScreen.png kaydet",
            initialfile=SPLASH_FILENAME,
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png")
            ]
        )

        if not filename:
            return

        try:
            self.save_processed(
                filename
            )

            self.set_status(
                "SplashScreen.png kaydedildi."
            )

            self.show_toast(
                "PNG başarıyla kaydedildi."
            )

        except Exception as error:
            messagebox.showerror(
                "Hata",
                str(error)
            )

    # ========================================================
    # MODERN CONFIRM DIALOG
    # ========================================================

    def ask_confirm(
        self,
        title,
        message,
        confirm_text="Evet",
        cancel_text="Hayır",
    ):
        """Bütün silme, sıfırlama ve geri yükleme onayları ortak pencereyi kullanır."""
        return show_confirm_dialog(
            self,
            title,
            message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
        )

    # ========================================================
    # CUSTOM LIBRARY NAME DIALOG
    # ========================================================

    def get_next_library_default_name(self):
        existing_stems = {
            path.stem.casefold()
            for path in LIBRARY_DIR.glob("*.png")
        }

        index = 1
        while True:
            candidate = f"Splash {index:02d}"
            if candidate.casefold() not in existing_stems:
                return candidate
            index += 1

    def ask_library_name(self):
        """Kütüphaneye ekleme penceresinde ortak lacivert tasarımı kullan."""
        return show_library_name_dialog(
            self, self.get_next_library_default_name()
        )

    # ========================================================
    # LIBRARY ADD
    # ========================================================

    def add_current_to_library(self):
        if self.processed_image is None:
            self.show_feedback(
                "warning", "Görsel seçilmedi",
                "Kütüphaneye eklemek için önce bir görsel seç.",
            )
            return

        library_name = self.ask_library_name()

        if library_name is None:
            return

        filename = self.make_unique_library_name(
            library_name
        )

        destination = (
            LIBRARY_DIR
            / filename
        )

        try:
            self.save_processed(
                destination
            )

            self.refresh_library()

            self.set_status(
                f"Kütüphaneye eklendi: {destination.stem}"
            )

            self.show_toast(
                f"✓ {destination.stem} kütüphaneye eklendi."
            )

        except Exception as error:
            messagebox.showerror(
                "Hata",
                str(error)
            )

    def add_external_to_library(self):
        filename = filedialog.askopenfilename(
            title="Kütüphaneye görsel ekle",
            filetypes=[
                ("Görseller", SUPPORTED_FILES)
            ]
        )

        if not filename:
            return

        library_name = self.ask_library_name()

        if library_name is None:
            return

        try:
            image = self.load_rgba_image(
                filename
            )

            destination = (
                LIBRARY_DIR
                / self.make_unique_library_name(
                    library_name
                )
            )

            self.save_rgba_png(
                image,
                destination
            )

            self.refresh_library()

            self.set_status(
                f"Kütüphaneye eklendi: {destination.stem}"
            )

            self.show_toast(
                f"✓ {destination.stem} kütüphaneye eklendi."
            )

        except Exception as error:
            info = describe_image_error(error, filename)
            self.show_feedback(
                info.level, info.title, info.message, details=info.details,
            )

    def make_unique_library_name(self, stem):
        safe = "".join(
            char
            if (
                char.isalnum()
                or char in "-_ "
            )
            else " "
            for char in stem
        )

        safe = " ".join(
            safe.strip().split()
        )

        if not safe:
            safe = "Splash"

        filename = f"{safe}.png"
        path = LIBRARY_DIR / filename

        counter = 2

        while path.exists():
            filename = (
                f"{safe} ({counter}).png"
            )
            path = LIBRARY_DIR / filename
            counter += 1

        return filename

    # ========================================================
    # TOAST
    # ========================================================

    def show_feedback(self, level, title, message, *, details=None, duration=None):
        """Uygun sayfadaki bilgi alanını kullan; alt durum metnini tekrarlama."""
        return self.feedback_overlay.show(
            level, title, message, details=details, duration=duration,
        )

    def show_toast(self, message, duration=3500):
        """Eski başarı çağrıları yeni ortak bildirim alanını kullanır."""
        self.show_feedback(
            "success", "İşlem tamamlandı", message, duration=duration,
        )

    # ========================================================
    # LIBRARY REFRESH
    # ========================================================

    def refresh_library(self):
        if not hasattr(self, "library_scroll"):
            return
        self._library_search_after = None

        # Silinmiş seçimi temizle ve gecikmeli Tk redraw referanslarını koru.
        self.image_reference_pool.extend(self.library_card_images)
        if (
            self.library_selected_path is not None
            and not Path(self.library_selected_path).is_file()
        ):
            self.clear_library_selection()

        for child in self.library_scroll.winfo_children():
            child.destroy()
        self.library_scroll.update_idletasks()
        self.library_card_images = []
        self.library_card_frames = {}

        all_items = self.get_library_items()
        query = self.library_search_var.get().strip()
        items = self.get_library_items(query)
        custom_count = sum(kind == "custom" for _, kind in all_items)
        self.library_count_label.configure(
            text=(
                f"{custom_count} özel görsel  •  {len(items)} gösteriliyor"
                if query else
                f"{custom_count} özel görsel  •  {len(all_items)} toplam görsel"
            )
        )

        if not items:
            empty_text = (
                "Aramanızla eşleşen görsel bulunamadı."
                if query else
                "Henüz bir splash görseli eklenmedi."
            )
            ctk.CTkLabel(
                self.library_scroll,
                text=empty_text,
                font=ctk.CTkFont(size=13),
                text_color=UI_TEXT_SECONDARY,
                width=575,
                height=100,
            ).grid(row=0, column=0, columnspan=2, pady=70)
            return

        self.library_scroll.grid_columnconfigure(0, minsize=286)
        self.library_scroll.grid_columnconfigure(1, minsize=286)

        for index, (item_path, kind) in enumerate(items):
            card = self.create_library_card(item_path, kind)
            card.grid(
                row=index // 2,
                column=index % 2,
                padx=8,
                pady=8,
            )
        self.update_library_selection_highlight()

    def create_library_card(self, path, kind):
        """Resmi iç boşluk ekleyen bir buton yerine sabit görsel yüzeyine yerleştir."""
        is_selected = (
            self.library_selected_path is not None
            and Path(self.library_selected_path) == Path(path)
            and self.library_selected_kind == kind
        )
        card = ctk.CTkFrame(
            self.library_scroll,
            width=CARD_W,
            height=CARD_H,
            corner_radius=12,
            fg_color=UI_SURFACE_RAISED if is_selected else UI_SURFACE_DARK,
            border_width=2 if is_selected else 1,
            border_color=UI_ACCENT if is_selected else UI_BORDER,
        )
        card.grid_propagate(False)
        card.pack_propagate(False)
        self.library_card_frames[(str(path), kind)] = card

        thumbnail_frame = ctk.CTkFrame(
            card,
            width=CARD_THUMB_W,
            height=CARD_THUMB_H,
            corner_radius=8,
            fg_color=UI_SURFACE_DARK,
            border_width=1,
            border_color=UI_BORDER,
        )
        thumbnail_frame.place(x=15, y=10)
        thumbnail_frame.grid_propagate(False)
        thumbnail_frame.pack_propagate(False)

        # Kart ve görsel ayrı bileşenlerdir: üstte görünmez bir buton
        # olmadığı için resmin üstüne dolgu/renk katmanı binmez.
        def choose(_event=None):
            self.select_library_item(path, kind)

        card.bind("<Button-1>", choose)
        thumbnail_frame.bind("<Button-1>", choose)

        try:
            # Çerçevenin 1px kenarlığı dışında 16:9 görsel alanını doldur.
            image = self.load_rgba_image(path)
            thumb_size = (CARD_THUMB_W - 2, CARD_THUMB_H - 2)
            thumbnail = ImageOps.fit(
                image,
                thumb_size,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            ctk_image = ctk.CTkImage(
                light_image=thumbnail,
                dark_image=thumbnail,
                size=thumb_size,
            )
            self.library_card_images.append(ctk_image)
            self.image_reference_pool.append(ctk_image)

            image_label = ctk.CTkLabel(
                thumbnail_frame,
                text="",
                image=ctk_image,
                width=thumb_size[0],
                height=thumb_size[1],
                fg_color="transparent",
            )
            image_label._splash_image_ref = ctk_image
            image_label.place(x=1, y=1)
            image_label.bind("<Button-1>", choose)
        except Exception:
            placeholder = ctk.CTkLabel(
                thumbnail_frame,
                width=CARD_THUMB_W - 2,
                height=CARD_THUMB_H - 2,
                text="Görsel okunamadı",
                text_color=UI_TEXT_MUTED,
                fg_color="transparent",
            )
            placeholder.place(x=1, y=1)
            placeholder.bind("<Button-1>", choose)

        display_name = (
            "★ Paketle Gelen Sezon" if kind == "season" else path.stem
        )
        if len(display_name) > 29:
            display_name = display_name[:26] + "..."
        name_label = ctk.CTkLabel(
            card,
            width=CARD_THUMB_W,
            height=25,
            text=display_name,
            anchor="center",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=UI_TEXT,
        )
        name_label.place(x=15, y=152)
        name_label.bind("<Button-1>", choose)
        return card

    def update_library_selection_highlight(self):
        """Kartları yeniden oluşturmadan mavi seçim çerçevesini güncelle."""
        for (path, kind), card in self.library_card_frames.items():
            selected = (
                self.library_selected_path is not None
                and str(self.library_selected_path) == path
                and self.library_selected_kind == kind
            )
            card.configure(
                border_width=2 if selected else 1,
                border_color=UI_ACCENT if selected else UI_BORDER,
                fg_color=UI_SURFACE_RAISED if selected else UI_SURFACE_DARK,
            )

    def create_empty_library_preview(self):
        """Eski görüntülü label'ı kaldırıp temiz bir önizleme oluştur."""
        previous = getattr(self, "library_preview_label", None)
        if previous is not None:
            previous.destroy()

        self.library_preview_label = ctk.CTkLabel(
            self.library_preview_panel,
            width=LIB_PREVIEW_IMAGE_W,
            height=LIB_PREVIEW_IMAGE_H,
            text="Bir görsel seç",
            text_color=UI_TEXT_MUTED,
            fg_color="transparent",
        )
        self.library_preview_label.place(x=31, y=62)

    def clear_library_selection(self):
        """Silinmiş veya seçimi kaldırılmış görselin izini tamamen temizle."""
        if self.library_preview_image is not None:
            self.image_reference_pool.append(self.library_preview_image)

        self.library_selected_path = None
        self.library_selected_kind = None
        self.library_preview_image = None
        self.create_empty_library_preview()
        self.library_name_label.configure(text="-")
        if hasattr(self, "library_info_label"):
            self.library_info_label.configure(
                text="Önizlemek için soldan bir görsel seçin."
            )
        if hasattr(self, "library_apply_button"):
            self.library_apply_button.configure(state="disabled")
        if hasattr(self, "library_delete_button"):
            self.library_delete_button.configure(state="disabled")
        if hasattr(self, "library_card_frames"):
            self.update_library_selection_highlight()
        self.library_preview_label.update_idletasks()

    def select_library_item(self, path, kind):
        path = Path(path)
        if not path.is_file():
            self.refresh_library()
            self.show_feedback(
                "warning", "Görsel bulunamadı",
                "Seçilen görsel silinmiş veya taşınmış. Kütüphane yenilendi.",
            )
            return

        try:
            image = self.load_rgba_image(path)
            original_size = image.size
            thumbnail = ImageOps.fit(
                image,
                (LIB_PREVIEW_IMAGE_W, LIB_PREVIEW_IMAGE_H),
                method=Image.Resampling.LANCZOS,
            )
            new_preview_image = ctk.CTkImage(
                light_image=thumbnail,
                dark_image=thumbnail,
                size=(LIB_PREVIEW_IMAGE_W, LIB_PREVIEW_IMAGE_H),
            )
            if self.library_preview_image is not None:
                self.image_reference_pool.append(self.library_preview_image)
            self.image_reference_pool.append(new_preview_image)

            self.library_preview_label.configure(
                image=new_preview_image,
                text="",
            )
            self.library_preview_label._splash_image_ref = new_preview_image
            self.library_preview_image = new_preview_image
            self.library_preview_label.update_idletasks()

            self.library_selected_path = path
            self.library_selected_kind = kind
            display_name = (
                "Paketle Gelen Sezon Görseli" if kind == "season" else path.stem
            )
            if len(display_name) > 48:
                display_name = display_name[:45] + "..."
            self.library_name_label.configure(text=display_name)
            self.library_info_label.configure(
                text=(
                    f"{original_size[0]}×{original_size[1]}  •  "
                    f"{'Paket görseli' if kind == 'season' else 'Kütüphane görseli'}"
                )
            )
            self.library_apply_button.configure(state="normal")
            self.library_delete_button.configure(
                state="disabled" if kind == "season" else "normal"
            )
            self.update_library_selection_highlight()
            self.set_status(f"Seçildi: {display_name}")

        except Exception as error:
            info = describe_image_error(error, path)
            self.show_feedback(
                info.level, info.title, info.message, details=info.details,
            )

    def apply_library_item(self):
        if self.library_selected_path is None:
            self.show_feedback(
                "warning", "Görsel seçilmedi",
                "Fortnite'a uygulamak için kütüphaneden bir görsel seç.",
            )
            return

        if not self.fortnite_target_is_ready():
            return

        selected_path = Path(
            self.library_selected_path
        )

        if not selected_path.exists():
            self.clear_library_selection()
            self.refresh_library()

            self.show_feedback(
                "warning", "Görsel bulunamadı",
                "Seçilen kütüphane görseli artık mevcut değil. Liste yenilendi.",
            )
            return

        try:
            image = self.load_rgba_image(
                selected_path
            )

            apply_splash(
                image,
                self.splash_path,
                BACKUP_DIR
            )

            self.set_status(
                "Kütüphane splash'i Fortnite'a uygulandı."
            )

            self.show_toast(
                "✓ Seçili splash Fortnite'a uygulandı."
            )

            self.update_active_splash_status()

        except PermissionError:
            messagebox.showerror(
                "Dosya erişim izni gerekli",
                (
                    "Fortnite dosyasına veya yedek klasörüne erişilemedi.\n\n"
                    "Klasör izinlerini ve dosyanın başka bir programda "
                    "kullanılıp kullanılmadığını kontrol et."
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Splash uygulanamadı",
                str(error)
            )

    def delete_library_item(self):
        if self.library_selected_path is None:
            self.show_feedback(
                "warning", "Görsel seçilmedi",
                "Silmek için önce kütüphaneden bir görsel seç.",
            )
            return

        if self.library_selected_kind == "season":
            self.show_feedback(
                "info", "Paket sezon görseli",
                "Uygulamayla gelen sezon görseli kütüphaneden silinemez.",
            )
            return

        selected_path = Path(
            self.library_selected_path
        )

        answer = self.ask_confirm(
            "Kütüphaneden Sil",
            (
                f"“{selected_path.stem}” kütüphaneden silinsin mi?\n\n"
                "Bu işlem geri alınamaz."
            ),
            confirm_text="Sil",
            cancel_text="Vazgeç"
        )

        if not answer:
            return

        try:
            if selected_path.exists():
                selected_path.unlink()

            self.clear_library_selection()
            self.refresh_library()

            self.set_status(
                "Görsel kütüphaneden silindi."
            )

            self.show_toast(
                "Görsel kütüphaneden silindi."
            )

        except PermissionError:
            messagebox.showerror(
                "Silinemedi",
                (
                    "Dosya silinemedi. Başka bir program "
                    "tarafından kullanılıyor olabilir."
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Silinemedi",
                str(error)
            )

    def open_library_folder(self):
        LIBRARY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        try:
            os.startfile(
                LIBRARY_DIR
            )

        except AttributeError:
            subprocess.Popen(
                [
                    "explorer",
                    str(LIBRARY_DIR)
                ]
            )

    # ========================================================
    # ACTIVE SPLASH STATUS
    # ========================================================

    def file_sha256(self, path):
        """Yalnızca okunabilen/geçerli PNG görsellerine durum kimliği ver."""
        try:
            return hashlib.sha256(read_png(path)).hexdigest()
        except (OSError, ValueError):
            return None

    def update_active_splash_status(self):
        """Doğrulanamayan bir dosyayı yanlışlıkla 'özel' diye işaretleme."""
        target = Path(self.splash_path) if self.splash_path else None

        if target is None or not target.is_file() or target.is_symlink():
            state = "unknown"
            badge_text = "Splash durumu bilinmiyor"
            settings_text = "Aktif splash durumu: Fortnite splash dosyası bulunamadı."
        else:
            current_hash = self.file_sha256(target)
            season_hash = (
                self.file_sha256(CURRENT_SEASON_SPLASH_PATH)
                if CURRENT_SEASON_SPLASH_PATH.is_file() else None
            )

            if current_hash is None:
                state = "unknown"
                badge_text = "Splash durumu bilinmiyor"
                settings_text = "Aktif splash durumu: Fortnite splash dosyası okunamadı veya geçersiz."
            elif season_hash is None:
                state = "unknown"
                badge_text = "Splash durumu bilinmiyor"
                settings_text = "Aktif splash durumu: Paketle gelen sezon görseli doğrulanamadı."
            elif current_hash == season_hash:
                state = "season"
                badge_text = "Paket Görseli Aktif ✓"
                settings_text = "Aktif splash durumu: Paketle gelen sezon görseli kullanılıyor."
            else:
                state = "custom"
                badge_text = "Özel Splash Aktif"
                settings_text = "Aktif splash durumu: Paket görselinden farklı bir splash kullanılıyor."

        self.current_splash_state = state
        if hasattr(self, "splash_state_badge"):
            self.splash_state_badge.configure(text=badge_text)
        if hasattr(self, "settings_splash_status_label"):
            self.settings_splash_status_label.configure(text=settings_text)
        if hasattr(self, "settings_active_badge"):
            theme = {
                "season": ("#1B3A35", "#9CE0C3"),
                "custom": ("#203D5C", "#A8D2FF"),
                "unknown": (UI_SURFACE_RAISED, UI_TEXT_SECONDARY),
            }
            background, foreground = theme[state]
            self.settings_active_badge.configure(
                text=badge_text,
                fg_color=background,
                text_color=foreground,
            )

    # ========================================================
    # FORTNITE DETECTION
    # ========================================================

    def detect_fortnite(self):
        saved_path = self.settings.get(
            "fortnite_path"
        )

        is_direct_folder = self.settings.get(
            "fortnite_path_is_direct_splash_folder",
            False
        )

        if saved_path:
            saved_path_obj = Path(
                saved_path
            )

            if saved_path_obj.exists():
                if is_direct_folder:
                    direct_splash = (
                        saved_path_obj
                        / SPLASH_FILENAME
                    )

                    if direct_splash.exists():
                        self.fortnite_install_path = None
                        self.splash_path = direct_splash
                        self.set_fortnite_found()
                        return

                else:
                    if self.configure_fortnite_path(
                        saved_path_obj,
                        save_setting=False
                    ):
                        return

        install_path = (
            self.find_fortnite_from_epic()
        )

        if install_path:
            if self.configure_fortnite_path(
                install_path,
                save_setting=False
            ):
                return

        self.set_fortnite_not_found()

    def find_fortnite_from_epic(self):
        manifests = Path(
            r"C:\ProgramData\Epic"
            r"\EpicGamesLauncher"
            r"\Data\Manifests"
        )

        if not manifests.exists():
            return None

        try:
            for file in manifests.glob(
                "*.item"
            ):
                try:
                    with open(
                        file,
                        "r",
                        encoding="utf-8"
                    ) as f:
                        data = json.load(f)

                    display_name = (
                        data.get(
                            "DisplayName",
                            ""
                        )
                    ).lower()

                    app_name = (
                        data.get(
                            "AppName",
                            ""
                        )
                    ).lower()

                    if (
                        "fortnite"
                        not in display_name
                        and
                        "fortnite"
                        not in app_name
                    ):
                        continue

                    location = data.get(
                        "InstallLocation"
                    )

                    if location:
                        path = Path(location)

                        if path.exists():
                            return path

                except (
                    json.JSONDecodeError,
                    OSError
                ):
                    continue

        except OSError:
            pass

        return None

    def configure_fortnite_path(
        self,
        install_path,
        save_setting=False
    ):
        install_path = Path(
            install_path
        )

        expected_folder = (
            install_path
            / "FortniteGame"
            / "Binaries"
            / "Win64"
            / "EasyAntiCheat"
        )

        expected_splash = (
            expected_folder
            / SPLASH_FILENAME
        )

        if expected_splash.exists():
            self.fortnite_install_path = (
                install_path
            )

            self.splash_path = (
                expected_splash
            )

            if save_setting:
                self.save_fortnite_path_setting()

            self.set_fortnite_found()
            return True

        win64 = (
            install_path
            / "FortniteGame"
            / "Binaries"
            / "Win64"
        )

        if win64.exists():
            try:
                for candidate in win64.rglob(
                    SPLASH_FILENAME
                ):
                    if (
                        "easyanticheat"
                        in str(
                            candidate.parent
                        ).lower()
                    ):
                        self.fortnite_install_path = (
                            install_path
                        )

                        self.splash_path = candidate

                        if save_setting:
                            self.save_fortnite_path_setting()

                        self.set_fortnite_found()
                        return True

            except OSError:
                pass

        return False

    def set_fortnite_found(self):
        self.fortnite_badge.configure(
            text="Fortnite bulundu ✓"
        )

        if self.fortnite_install_path:
            display_path = str(
                self.fortnite_install_path
            )

        elif self.splash_path:
            display_path = str(
                self.splash_path.parent
            )

        else:
            display_path = "Fortnite bulundu"

        if len(display_path) > 60:
            display_path = (
                display_path[:57]
                + "..."
            )

        self.path_label.configure(
            text=display_path
        )

        self.refresh_library()
        self.refresh_settings_page()
        self.update_active_splash_status()

        self.set_status(
            "Fortnite kurulumu hazır."
        )

    def set_fortnite_not_found(self):
        # Eski/geçersiz yolun yanlışlıkla sonraki işlemlerde kullanılmasını engelle.
        self.fortnite_install_path = None
        self.splash_path = None
        self.fortnite_badge.configure(
            text="Fortnite bulunamadı"
        )

        self.path_label.configure(
            text=(
                "Fortnite otomatik olarak "
                "bulunamadı."
            )
        )

        self.current_splash_state = "unknown"

        if hasattr(
            self,
            "splash_state_badge"
        ):
            self.splash_state_badge.configure(
                text="Splash durumu bilinmiyor"
            )

        if hasattr(
            self,
            "settings_splash_status_label"
        ):
            self.settings_splash_status_label.configure(
                text=(
                    "Aktif splash durumu: "
                    "Fortnite bulunamadı."
                )
            )
        if hasattr(self, "settings_active_badge"):
            self.settings_active_badge.configure(
                text="Splash durumu bilinmiyor",
                fg_color=UI_SURFACE_RAISED,
                text_color=UI_TEXT_SECONDARY,
            )
        if hasattr(self, "settings_install_badge"):
            self.settings_install_badge.configure(
                text="Fortnite bulunamadı",
                fg_color=UI_SURFACE_RAISED,
                text_color=UI_TEXT_SECONDARY,
            )
        if hasattr(self, "settings_backup_badge"):
            self.refresh_backup_status()

        self.set_status(
            "Fortnite klasörünü manuel seçebilirsin."
        )

    def select_fortnite_folder(self):
        folder = filedialog.askdirectory(
            title="Fortnite klasörünü seç"
        )

        if not folder:
            return

        path = Path(folder)

        if self.configure_fortnite_path(
            path,
            save_setting=True
        ):
            self.show_toast(
                "✓ Fortnite yolu kaydedildi."
            )
            return

        direct_splash = (
            path
            / SPLASH_FILENAME
        )

        if direct_splash.exists():
            self.splash_path = direct_splash
            self.fortnite_install_path = None

            # Kullanıcı doğrudan EasyAntiCheat klasörünü seçtiyse
            # bu özel konumu settings.json içinde ayrıca sakla.
            self.settings["fortnite_path"] = str(
                path
            )
            self.settings[
                "fortnite_path_is_direct_splash_folder"
            ] = True
            self.save_settings()

            self.set_fortnite_found()
            self.show_toast(
                "✓ Fortnite splash klasörü kaydedildi."
            )
            return

        messagebox.showerror(
            "Geçersiz klasör",
            (
                "Seçilen klasörde Fortnite kurulumu veya "
                "SplashScreen.png bulunamadı."
            )
        )

    def apply_to_fortnite(self):
        if self.processed_image is None:
            self.show_feedback(
                "warning", "Görsel seçilmedi",
                "Fortnite'a uygulamak için önce bir görsel seç.",
            )
            return

        if not self.fortnite_target_is_ready():
            return

        try:
            apply_splash(
                self.processed_image,
                self.splash_path,
                BACKUP_DIR
            )

            self.set_status(
                "Yeni splash Fortnite'a uygulandı."
            )

            self.show_toast(
                "✓ Splash Fortnite'a uygulandı."
            )

            self.update_active_splash_status()

        except PermissionError:
            messagebox.showerror(
                "Dosya erişim izni gerekli",
                (
                    "Fortnite dosyasına veya yedek klasörüne erişilemedi.\n\n"
                    "Klasör izinlerini ve dosyanın başka bir programda "
                    "kullanılıp kullanılmadığını kontrol et."
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Splash uygulanamadı",
                str(error)
            )

    def restore_previous(self):
        if not self.fortnite_target_is_ready():
            return

        if not self.ask_confirm(
            "Yedeklenen Splash",
            "Bu kurulumda ilk değişiklikten önce saklanan splash geri yüklensin mi?\n\n"
            "Bu yedek, daha önce özelleştirilmiş bir görsel de olabilir.",
            confirm_text="Geri Yükle",
            cancel_text="Vazgeç"
        ):
            return

        try:
            restore_previous_splash(self.splash_path, BACKUP_DIR)
            self.set_status("Yedeklenen splash geri yüklendi.")
            self.show_toast("✓ Yedeklenen splash geri yüklendi.")
            self.update_active_splash_status()
        except Exception as error:
            messagebox.showerror("Geri yüklenemedi", str(error))

    def apply_bundled_season(self):
        if not self.fortnite_target_is_ready():
            return

        if not CURRENT_SEASON_SPLASH_PATH.exists():
            messagebox.showerror(
                "Paketle gelen sezon görseli bulunamadı",
                (
                    "assets/current_season_splash.png bulunamadı.\n\n"
                    "main.py ile birlikte assets klasörünü de "
                    "uygulama klasöründe tut."
                )
            )
            return

        answer = self.ask_confirm(
            "Paketle Gelen Sezon Görseli",
            (
                "Uygulamayla gelen sezon görseli uygulansın mı?\n\n"
                "Bu görsel, Fortnite'ın güncel sezonuyla aynı olmayabilir."
            ),
            confirm_text="Uygula",
            cancel_text="Vazgeç"
        )

        if not answer:
            return

        try:
            image = self.load_rgba_image(
                CURRENT_SEASON_SPLASH_PATH
            )

            apply_splash(
                image,
                self.splash_path,
                BACKUP_DIR
            )

            self.set_status(
                "Paketle gelen sezon görseli uygulandı."
            )

            self.show_toast(
                "✓ Paketle gelen sezon görseli uygulandı."
            )

            self.update_active_splash_status()

        except PermissionError:
            messagebox.showerror(
                "Dosya erişim izni gerekli",
                (
                    "Fortnite dosyasına veya yedek klasörüne erişilemedi.\n\n"
                    "Klasör izinlerini ve dosyanın başka bir programda "
                    "kullanılıp kullanılmadığını kontrol et."
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Geri yüklenemedi",
                str(error)
            )

    def create_statusbar(self):
        self.status_label = ctk.CTkLabel(
            self,
            width=1100,
            height=24,
            text="Hazır",
            anchor="w",
            text_color=UI_TEXT_SECONDARY
        )

        self.status_label.place(
            x=40,
            y=724
        )

    def set_status(self, text):
        self.status_label.configure(
            text=text
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app = FortniteSplashMaker()
    app.mainloop()
