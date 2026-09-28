import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps, UnidentifiedImageError


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
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR

LIBRARY_DIR = APP_DIR / "library"
ASSETS_DIR = RESOURCE_DIR / "assets"
CURRENT_SEASON_SPLASH_PATH = ASSETS_DIR / "current_season_splash.png"
APP_ICON_PATH = ASSETS_DIR / "app_icon.ico"
SETTINGS_PATH = APP_DIR / "settings.json"

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
LIB_GALLERY_Y = 65
LIB_GALLERY_W = 620
LIB_GALLERY_H = 450

LIB_PREVIEW_X = 655
LIB_PREVIEW_Y = 65
LIB_PREVIEW_W = 440
LIB_PREVIEW_H = 450

CARD_W = 270
CARD_H = 190
CARD_THUMB_W = 240
CARD_THUMB_H = 135

PREVIEW_W = 460
PREVIEW_H = 259

LIB_PREVIEW_IMAGE_W = 390
LIB_PREVIEW_IMAGE_H = 219


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

        # Tk/CustomTkinter resimleri bazen widget yeniden çizilirken
        # gecikmeli olarak kullanılabiliyor. Eski CTkImage nesnelerini
        # uygulama kapanana kadar canlı tutarak "pyimageX doesn't exist"
        # hatasını tamamen engelliyoruz.
        self.image_reference_pool = []

        self.toast_frame = None

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
        ctk.CTkLabel(
            self,
            text="Fortnite Splash Maker",
            font=ctk.CTkFont(
                size=29,
                weight="bold"
            )
        ).place(
            x=40,
            y=28
        )

        ctk.CTkLabel(
            self,
            text=(
                "Fortnite başlangıç ekranlarını "
                "hazırla, sakla ve tek tıkla uygula"
            ),
            text_color="gray70",
            font=ctk.CTkFont(size=14)
        ).place(
            x=40,
            y=72
        )

        self.fortnite_badge = ctk.CTkLabel(
            self,
            text="Fortnite aranıyor...",
            width=150,
            height=30,
            corner_radius=8,
            fg_color=("gray85", "gray25")
        )

        self.fortnite_badge.place(
            x=990,
            y=45
        )

        self.splash_state_badge = ctk.CTkLabel(
            self,
            text="Splash durumu bilinmiyor",
            width=180,
            height=26,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            text_color="gray70"
        )

        self.splash_state_badge.place(
            x=960,
            y=82
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def create_navigation(self):
        self.nav = ctk.CTkSegmentedButton(
            self,
            values=[
                "Oluştur",
                "Kütüphane",
                "Ayarlar"
            ],
            variable=self.page_mode,
            width=290,
            height=30,
            command=self.show_page
        )

        self.nav.place(
            x=(WINDOW_WIDTH - 290) // 2,
            y=130
        )

    def show_page(self, page):
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
            height=MAIN_HEIGHT
        )

        self.main_container.place(
            x=MAIN_X,
            y=MAIN_Y
        )

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
        panel = ctk.CTkFrame(
            self.creator_page,
            width=CREATOR_LEFT_W,
            height=CREATOR_LEFT_H
        )

        panel.place(
            x=CREATOR_LEFT_X,
            y=CREATOR_LEFT_Y
        )

        panel.grid_propagate(False)
        panel.pack_propagate(False)

        ctk.CTkLabel(
            panel,
            text="Önizleme",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        ).place(
            x=20,
            y=16
        )

        self.preview_box = ctk.CTkFrame(
            panel,
            width=480,
            height=320,
            fg_color="#151515"
        )

        self.preview_box.place(
            x=20,
            y=52
        )

        self.preview_box.grid_propagate(False)
        self.preview_box.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            self.preview_box,
            width=460,
            height=300,
            text=(
                "Bir görsel seçerek başla\n\n"
                "PNG • JPG • WEBP • BMP"
            ),
            text_color="gray60",
            font=ctk.CTkFont(size=16)
        )

        self.preview_label.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.file_info = ctk.CTkLabel(
            panel,
            width=480,
            height=28,
            text="Henüz görsel seçilmedi",
            anchor="w",
            text_color="gray65"
        )

        self.file_info.place(
            x=20,
            y=390
        )

        self.output_info = ctk.CTkLabel(
            panel,
            width=480,
            height=24,
            text=(
                "Otomatik yerleşim • "
                "800×450 • PNG • RGBA"
            ),
            anchor="w",
            text_color="gray55"
        )

        self.output_info.place(
            x=20,
            y=424
        )

    # ========================================================
    # CREATOR RIGHT
    # ========================================================

    def create_creator_right_panel(self):
        panel = ctk.CTkFrame(
            self.creator_page,
            width=CREATOR_RIGHT_W,
            height=CREATOR_RIGHT_H
        )

        panel.place(
            x=CREATOR_RIGHT_X,
            y=CREATOR_RIGHT_Y
        )

        panel.grid_propagate(False)
        panel.pack_propagate(False)

        # Görsel
        ctk.CTkLabel(
            panel,
            text="Görsel",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        ).place(
            x=20,
            y=18
        )

        ctk.CTkButton(
            panel,
            text="Görsel Seç",
            width=500,
            height=40,
            command=self.select_image
        ).place(
            x=20,
            y=52
        )

        ctk.CTkLabel(
            panel,
            width=500,
            height=38,
            text=(
                "Görsel otomatik olarak 16:9 oranında "
                "merkezden kırpılır ve Fortnite için hazırlanır."
            ),
            anchor="w",
            justify="left",
            wraplength=495,
            text_color="gray65"
        ).place(
            x=20,
            y=102
        )

        # Fortnite
        ctk.CTkLabel(
            panel,
            text="Fortnite",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        ).place(
            x=20,
            y=164
        )

        self.path_label = ctk.CTkLabel(
            panel,
            width=500,
            height=30,
            text="Fortnite aranıyor...",
            anchor="w",
            text_color="gray65"
        )

        self.path_label.place(
            x=20,
            y=197
        )

        ctk.CTkButton(
            panel,
            text="Fortnite Klasörünü Seç",
            width=500,
            height=34,
            fg_color="transparent",
            border_width=1,
            command=self.select_fortnite_folder
        ).place(
            x=20,
            y=232
        )

        # İşlemler
        ctk.CTkLabel(
            panel,
            text="İşlemler",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        ).place(
            x=20,
            y=286
        )

        ctk.CTkButton(
            panel,
            text="Fortnite'a Uygula",
            width=500,
            height=43,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            command=self.apply_to_fortnite
        ).place(
            x=20,
            y=321
        )

        ctk.CTkButton(
            panel,
            text="Kütüphaneye Ekle",
            width=500,
            height=38,
            command=self.add_current_to_library
        ).place(
            x=20,
            y=374
        )

        ctk.CTkButton(
            panel,
            text="Orijinal Fortnite Splash'ini Geri Yükle",
            width=500,
            height=36,
            fg_color="transparent",
            border_width=1,
            command=self.restore_original
        ).place(
            x=20,
            y=422
        )

        ctk.CTkButton(
            panel,
            text="PNG Olarak Kaydet",
            width=500,
            height=32,
            fg_color="transparent",
            border_width=1,
            command=self.save_as
        ).place(
            x=20,
            y=466
        )

    # ========================================================
    # LIBRARY PAGE
    # ========================================================

    def create_library_page(self):
        self.library_page = ctk.CTkFrame(
            self.main_container,
            width=MAIN_WIDTH,
            height=MAIN_HEIGHT,
            fg_color="transparent"
        )

        self.library_page.grid_propagate(False)
        self.library_page.pack_propagate(False)

        ctk.CTkLabel(
            self.library_page,
            text="Splash Kütüphanesi",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).place(
            x=15,
            y=15
        )

        ctk.CTkButton(
            self.library_page,
            text="Klasörü Aç",
            width=115,
            height=30,
            command=self.open_library_folder
        ).place(
            x=720,
            y=12
        )

        ctk.CTkButton(
            self.library_page,
            text="Görsel Ekle",
            width=115,
            height=30,
            command=self.add_external_to_library
        ).place(
            x=843,
            y=12
        )

        ctk.CTkButton(
            self.library_page,
            text="Yenile",
            width=100,
            height=30,
            command=self.refresh_library
        ).place(
            x=966,
            y=12
        )

        self.library_scroll = ctk.CTkScrollableFrame(
            self.library_page,
            width=LIB_GALLERY_W,
            height=LIB_GALLERY_H,
            label_text="Kütüphane"
        )

        self.library_scroll.place(
            x=LIB_GALLERY_X,
            y=LIB_GALLERY_Y
        )

        preview_panel = ctk.CTkFrame(
            self.library_page,
            width=LIB_PREVIEW_W,
            height=LIB_PREVIEW_H
        )

        preview_panel.place(
            x=LIB_PREVIEW_X,
            y=LIB_PREVIEW_Y
        )

        preview_panel.grid_propagate(False)
        preview_panel.pack_propagate(False)

        ctk.CTkLabel(
            preview_panel,
            text="Seçili Splash",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        ).place(
            x=20,
            y=18
        )

        self.library_preview_label = ctk.CTkLabel(
            preview_panel,
            width=LIB_PREVIEW_IMAGE_W,
            height=LIB_PREVIEW_IMAGE_H,
            text="Bir görsel seç",
            text_color="gray60"
        )

        self.library_preview_label.place(
            x=25,
            y=66
        )

        self.library_name_label = ctk.CTkLabel(
            preview_panel,
            width=400,
            height=28,
            text="-",
            text_color="gray70"
        )

        self.library_name_label.place(
            x=20,
            y=300
        )

        ctk.CTkButton(
            preview_panel,
            text="Fortnite'a Uygula",
            width=400,
            height=40,
            command=self.apply_library_item
        ).place(
            x=20,
            y=345
        )

        ctk.CTkButton(
            preview_panel,
            text="Kütüphaneden Sil",
            width=400,
            height=34,
            fg_color="transparent",
            border_width=1,
            command=self.delete_library_item
        ).place(
            x=20,
            y=393
        )

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
            messagebox.showwarning(
                "Fortnite bulunamadı",
                "Önce Fortnite klasörünü seç."
            )
            return False

        splash_parent = Path(
            self.splash_path
        ).parent

        if not splash_parent.exists():
            messagebox.showerror(
                "Fortnite yolu geçersiz",
                (
                    "Easy Anti-Cheat klasörü artık bulunamıyor.\n\n"
                    "Fortnite güncellenmiş veya taşınmış olabilir. "
                    "Fortnite klasörünü yeniden seç."
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
        self.settings_page = ctk.CTkFrame(
            self.main_container,
            width=MAIN_WIDTH,
            height=MAIN_HEIGHT,
            fg_color="transparent"
        )

        self.settings_page.grid_propagate(False)
        self.settings_page.pack_propagate(False)

        panel = ctk.CTkFrame(
            self.settings_page,
            width=760,
            height=400
        )

        panel.place(
            x=(MAIN_WIDTH - 760) // 2,
            y=55
        )

        panel.grid_propagate(False)
        panel.pack_propagate(False)

        ctk.CTkLabel(
            panel,
            text="Ayarlar",
            font=ctk.CTkFont(
                size=23,
                weight="bold"
            )
        ).place(
            x=28,
            y=24
        )

        ctk.CTkLabel(
            panel,
            text="Fortnite Klasörü",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).place(
            x=28,
            y=82
        )

        self.settings_path_label = ctk.CTkLabel(
            panel,
            width=704,
            height=58,
            text="Henüz bir Fortnite yolu kaydedilmedi.",
            anchor="w",
            justify="left",
            wraplength=690,
            text_color="gray65"
        )

        self.settings_path_label.place(
            x=28,
            y=112
        )

        ctk.CTkButton(
            panel,
            text="Fortnite Klasörünü Değiştir",
            width=340,
            height=38,
            command=self.select_fortnite_folder
        ).place(
            x=28,
            y=180
        )

        ctk.CTkButton(
            panel,
            text="Kayıtlı Yolu Sıfırla",
            width=340,
            height=38,
            fg_color="transparent",
            border_width=1,
            command=self.reset_saved_fortnite_path
        ).place(
            x=392,
            y=180
        )

        ctk.CTkFrame(
            panel,
            width=704,
            height=1,
            fg_color=("gray75", "gray30")
        ).place(
            x=28,
            y=244
        )

        ctk.CTkLabel(
            panel,
            text="Uygulama",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).place(
            x=28,
            y=274
        )

        ctk.CTkLabel(
            panel,
            text=f"Fortnite Splash Maker  •  v{APP_VERSION}",
            text_color="gray65"
        ).place(
            x=28,
            y=310
        )

        self.settings_splash_status_label = ctk.CTkLabel(
            panel,
            width=704,
            height=24,
            text="Aktif splash durumu: kontrol ediliyor...",
            anchor="w",
            text_color="gray65"
        )

        self.settings_splash_status_label.place(
            x=28,
            y=336
        )

        ctk.CTkLabel(
            panel,
            width=704,
            height=38,
            text=(
                "Manuel seçilen Fortnite yolu settings.json "
                "dosyasında saklanır ve sonraki açılışta otomatik kullanılır."
            ),
            anchor="w",
            justify="left",
            wraplength=690,
            text_color="gray55"
        ).place(
            x=28,
            y=364
        )

    def refresh_settings_page(self):
        if not hasattr(
            self,
            "settings_path_label"
        ):
            return

        saved_path = self.settings.get(
            "fortnite_path"
        )

        if (
            self.fortnite_install_path is not None
            and Path(
                self.fortnite_install_path
            ).exists()
        ):
            text = (
                "Aktif ve kayıtlı yol:\n"
                f"{self.fortnite_install_path}"
            )

        elif saved_path:
            text = (
                "Kayıtlı yol şu anda geçerli değil:\n"
                f"{saved_path}"
            )

        else:
            text = (
                "Henüz manuel olarak kaydedilmiş "
                "bir Fortnite yolu yok."
            )

        self.settings_path_label.configure(
            text=text
        )

        self.update_active_splash_status()

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

            self.set_status(
                "Görsel hazır."
            )

        except Exception as error:
            self.input_path = None
            self.original_image = None
            self.processed_image = None

            messagebox.showerror(
                "Görsel açılamadı",
                str(error)
            )

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
            messagebox.showwarning(
                "Görsel seçilmedi",
                "Önce bir görsel seç."
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
        cancel_text="Hayır"
    ):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("430x210")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        self.update_idletasks()

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()

        x = parent_x + (WINDOW_WIDTH - 430) // 2
        y = parent_y + (WINDOW_HEIGHT - 210) // 2

        dialog.geometry(
            f"430x210+{x}+{y}"
        )

        result = {
            "confirmed": False
        }

        ctk.CTkLabel(
            dialog,
            text=title,
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).place(
            x=24,
            y=22
        )

        ctk.CTkLabel(
            dialog,
            width=382,
            height=78,
            text=message,
            wraplength=380,
            justify="left",
            anchor="w",
            text_color="gray70"
        ).place(
            x=24,
            y=62
        )

        def confirm():
            result["confirmed"] = True
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text=cancel_text,
            width=120,
            height=36,
            fg_color="transparent",
            border_width=1,
            command=cancel
        ).place(
            x=166,
            y=154
        )

        ctk.CTkButton(
            dialog,
            text=confirm_text,
            width=120,
            height=36,
            command=confirm
        ).place(
            x=286,
            y=154
        )

        dialog.bind(
            "<Return>",
            lambda _event: confirm()
        )

        dialog.bind(
            "<Escape>",
            lambda _event: cancel()
        )

        dialog.protocol(
            "WM_DELETE_WINDOW",
            cancel
        )

        self.wait_window(dialog)

        return result["confirmed"]

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
        default_name = self.get_next_library_default_name()

        dialog = ctk.CTkToplevel(self)
        dialog.title("Kütüphaneye Ekle")
        dialog.geometry("460x235")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        self.update_idletasks()

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()

        x = parent_x + (WINDOW_WIDTH - 460) // 2
        y = parent_y + (WINDOW_HEIGHT - 235) // 2

        dialog.geometry(
            f"460x235+{x}+{y}"
        )

        result = {
            "confirmed": False,
            "value": None
        }

        ctk.CTkLabel(
            dialog,
            text="Kütüphaneye Ekle",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).place(
            x=24,
            y=20
        )

        ctk.CTkLabel(
            dialog,
            width=412,
            height=42,
            text=(
                "İstersen bir ad yaz. Boş bırakırsan "
                f"otomatik olarak “{default_name}” kullanılacak."
            ),
            wraplength=410,
            justify="left",
            anchor="w",
            text_color="gray65"
        ).place(
            x=24,
            y=58
        )

        entry = ctk.CTkEntry(
            dialog,
            width=412,
            height=38,
            placeholder_text=default_name
        )

        entry.place(
            x=24,
            y=112
        )

        error_label = ctk.CTkLabel(
            dialog,
            width=412,
            height=22,
            text="",
            anchor="w",
            text_color="#d66"
        )

        error_label.place(
            x=24,
            y=152
        )

        def confirm():
            value = " ".join(
                entry.get().strip().split()
            )

            if not value:
                value = default_name

            if len(value) > 60:
                error_label.configure(
                    text=(
                        "Ad en fazla 60 karakter olabilir."
                    )
                )
                return

            result["confirmed"] = True
            result["value"] = value
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="İptal",
            width=120,
            height=34,
            fg_color="transparent",
            border_width=1,
            command=cancel
        ).place(
            x=196,
            y=184
        )

        ctk.CTkButton(
            dialog,
            text="Kütüphaneye Ekle",
            width=120,
            height=34,
            command=confirm
        ).place(
            x=316,
            y=184
        )

        entry.bind(
            "<Return>",
            lambda _event: confirm()
        )

        dialog.bind(
            "<Escape>",
            lambda _event: cancel()
        )

        dialog.protocol(
            "WM_DELETE_WINDOW",
            cancel
        )

        entry.focus_set()

        self.wait_window(dialog)

        if result["confirmed"]:
            return result["value"]

        return None

    # ========================================================
    # LIBRARY ADD
    # ========================================================

    def add_current_to_library(self):
        if self.processed_image is None:
            messagebox.showwarning(
                "Görsel seçilmedi",
                "Önce bir görsel seç."
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
            messagebox.showerror(
                "Görsel eklenemedi",
                str(error)
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

    def show_toast(
        self,
        message,
        duration=2500
    ):
        if self.toast_frame is not None:
            try:
                self.toast_frame.destroy()
            except Exception:
                pass

        self.toast_frame = ctk.CTkFrame(
            self,
            width=360,
            height=48,
            corner_radius=10
        )

        self.toast_frame.place(
            x=WINDOW_WIDTH - 385,
            y=690
        )

        self.toast_frame.grid_propagate(False)
        self.toast_frame.pack_propagate(False)

        ctk.CTkLabel(
            self.toast_frame,
            width=330,
            height=48,
            text=message,
            anchor="w",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        ).place(
            x=16,
            y=0
        )

        frame = self.toast_frame

        def close_toast():
            if self.toast_frame is frame:
                try:
                    frame.destroy()
                except Exception:
                    pass
                self.toast_frame = None

        self.after(
            duration,
            close_toast
        )

    # ========================================================
    # LIBRARY REFRESH
    # ========================================================

    def refresh_library(self):
        if not hasattr(
            self,
            "library_scroll"
        ):
            return

        # Önce mevcut kartlardaki resim referanslarını kalıcı havuza al.
        # Widget'lar yok edildikten sonra bile Tk tarafında gecikmeli redraw
        # olabildiği için eski CTkImage nesnelerini GC'ye bırakmıyoruz.
        self.image_reference_pool.extend(
            self.library_card_images
        )

        for child in self.library_scroll.winfo_children():
            child.destroy()

        self.library_scroll.update_idletasks()

        self.library_card_images = []

        items = []

        if CURRENT_SEASON_SPLASH_PATH.exists():
            items.append(
                (
                    CURRENT_SEASON_SPLASH_PATH,
                    "season"
                )
            )

        for path in sorted(
            LIBRARY_DIR.glob("*.png"),
            key=lambda item: item.name.lower()
        ):
            items.append(
                (path, "custom")
            )

        if not items:
            ctk.CTkLabel(
                self.library_scroll,
                text="Kütüphanede henüz görsel yok.",
                text_color="gray60"
            ).grid(
                row=0,
                column=0,
                padx=20,
                pady=30
            )
            return

        self.library_scroll.grid_columnconfigure(
            0,
            minsize=280
        )

        self.library_scroll.grid_columnconfigure(
            1,
            minsize=280
        )

        for index, (item_path, kind) in enumerate(items):
            row = index // 2
            column = index % 2

            card = self.create_library_card(
                item_path,
                kind
            )

            card.grid(
                row=row,
                column=column,
                padx=6,
                pady=6
            )

    def create_library_card(
        self,
        path,
        kind
    ):
        card = ctk.CTkFrame(
            self.library_scroll,
            width=CARD_W,
            height=CARD_H
        )

        card.grid_propagate(False)
        card.pack_propagate(False)

        try:
            image = self.load_rgba_image(
                path
            )

            ctk_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(
                    CARD_THUMB_W,
                    CARD_THUMB_H
                )
            )

            self.library_card_images.append(
                ctk_image
            )
            self.image_reference_pool.append(
                ctk_image
            )

            button = ctk.CTkButton(
                card,
                text="",
                image=ctk_image,
                width=CARD_THUMB_W,
                height=CARD_THUMB_H,
                fg_color="transparent",
                hover_color=("gray80", "gray25"),
                command=lambda p=path, k=kind:
                    self.select_library_item(
                        p,
                        k
                    )
            )

            button._splash_image_ref = ctk_image

            button.place(
                x=15,
                y=10
            )

        except Exception:
            ctk.CTkLabel(
                card,
                width=CARD_THUMB_W,
                height=CARD_THUMB_H,
                text="Önizleme yüklenemedi",
                text_color="gray60"
            ).place(
                x=15,
                y=10
            )

        if kind == "season":
            label_text = "★ Aktif Sezon Splash"
        else:
            name = path.stem

            if len(name) > 27:
                name = name[:24] + "..."

            label_text = name

        ctk.CTkLabel(
            card,
            width=240,
            height=28,
            text=label_text,
            anchor="center",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        ).place(
            x=15,
            y=150
        )

        return card

    def select_library_item(
        self,
        path,
        kind
    ):
        path = Path(path)

        if not path.exists():
            self.refresh_library()

            messagebox.showwarning(
                "Görsel bulunamadı",
                (
                    "Seçilen görsel artık mevcut değil. "
                    "Kütüphane yenilendi."
                )
            )
            return

        try:
            image = self.load_rgba_image(
                path
            )

            new_preview_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(
                    LIB_PREVIEW_IMAGE_W,
                    LIB_PREVIEW_IMAGE_H
                )
            )

            # Hem eski hem yeni preview CTkImage nesnelerini kalıcı havuzda tut.
            if self.library_preview_image is not None:
                self.image_reference_pool.append(
                    self.library_preview_image
                )

            self.image_reference_pool.append(
                new_preview_image
            )

            self.library_preview_label.configure(
                image=new_preview_image,
                text=""
            )

            self.library_preview_label._splash_image_ref = (
                new_preview_image
            )

            self.library_preview_image = (
                new_preview_image
            )

            # Tk'nin redraw kuyruğunu hemen işle.
            self.library_preview_label.update_idletasks()

            self.library_selected_path = path
            self.library_selected_kind = kind

            if kind == "season":
                display_name = "Aktif Sezon Fortnite Splash"
            else:
                display_name = path.stem

            if len(display_name) > 48:
                display_name = (
                    display_name[:45]
                    + "..."
                )

            self.library_name_label.configure(
                text=display_name
            )

            self.set_status(
                f"Seçildi: {display_name}"
            )

        except Exception as error:
            messagebox.showerror(
                "Görsel açılamadı",
                str(error)
            )

    def apply_library_item(self):
        if self.library_selected_path is None:
            messagebox.showwarning(
                "Görsel seçilmedi",
                "Kütüphaneden bir görsel seç."
            )
            return

        if not self.fortnite_target_is_ready():
            return

        selected_path = Path(
            self.library_selected_path
        )

        if not selected_path.exists():
            self.library_selected_path = None
            self.library_selected_kind = None
            self.refresh_library()

            messagebox.showwarning(
                "Görsel bulunamadı",
                (
                    "Seçilen kütüphane görseli artık mevcut değil. "
                    "Kütüphane yenilendi."
                )
            )
            return

        try:
            image = self.load_rgba_image(
                selected_path
            )

            self.save_rgba_png(
                image,
                self.splash_path
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
                "Yönetici izni gerekli",
                (
                    "Fortnite klasörüne yazma izni yok.\n\n"
                    "Uygulamayı yönetici olarak çalıştır."
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Splash uygulanamadı",
                str(error)
            )

    def delete_library_item(self):
        if self.library_selected_path is None:
            messagebox.showwarning(
                "Görsel seçilmedi",
                "Önce bir görsel seç."
            )
            return

        if self.library_selected_kind == "season":
            messagebox.showinfo(
                "Aktif Sezon Splash",
                (
                    "Bu görsel uygulamanın sabit geri yükleme "
                    "splash'idir ve kütüphaneden silinemez."
                )
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

            self.library_selected_path = None
            self.library_selected_kind = None

            # Eski preview resmi Tk redraw tamamlanana kadar değil,
            # uygulama kapanana kadar referans havuzunda tutulur.
            if self.library_preview_image is not None:
                self.image_reference_pool.append(
                    self.library_preview_image
                )

            self.library_preview_label.configure(
                image=None,
                text="Bir görsel seç"
            )

            self.library_preview_label._splash_image_ref = None
            self.library_preview_label.update_idletasks()

            self.library_preview_image = None

            self.library_name_label.configure(
                text="-"
            )

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
        try:
            sha = hashlib.sha256()

            with open(path, "rb") as file:
                while True:
                    chunk = file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    sha.update(chunk)

            return sha.hexdigest()

        except OSError:
            return None

    def update_active_splash_status(self):
        if (
            self.splash_path is None
            or
            not Path(
                self.splash_path
            ).exists()
        ):
            self.current_splash_state = "unknown"

            if hasattr(
                self,
                "splash_state_badge"
            ):
                self.splash_state_badge.configure(
                    text="Splash durumu bilinmiyor",
                    text_color="gray70"
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

            return

        current_hash = self.file_sha256(
            self.splash_path
        )

        season_hash = None

        if CURRENT_SEASON_SPLASH_PATH.exists():
            season_hash = self.file_sha256(
                CURRENT_SEASON_SPLASH_PATH
            )

        if (
            current_hash
            and
            season_hash
            and
            current_hash == season_hash
        ):
            self.current_splash_state = "season"
            badge_text = "Aktif Sezon Splash ✓"
            settings_text = (
                "Aktif splash durumu: "
                "Aktif Sezon Splash kullanılıyor."
            )
        else:
            self.current_splash_state = "custom"
            badge_text = "Özel Splash Aktif"
            settings_text = (
                "Aktif splash durumu: "
                "Özel bir splash kullanılıyor."
            )

        if hasattr(
            self,
            "splash_state_badge"
        ):
            self.splash_state_badge.configure(
                text=badge_text
            )

        if hasattr(
            self,
            "settings_splash_status_label"
        ):
            self.settings_splash_status_label.configure(
                text=settings_text
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
            messagebox.showwarning(
                "Görsel seçilmedi",
                "Önce bir görsel seç."
            )
            return

        if not self.fortnite_target_is_ready():
            return

        try:
            self.save_processed(
                self.splash_path
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
                "Yönetici izni gerekli",
                (
                    "Fortnite klasörüne yazma izni yok.\n\n"
                    "Uygulamayı yönetici olarak çalıştır."
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Splash uygulanamadı",
                str(error)
            )

    def restore_original(self):
        if not self.fortnite_target_is_ready():
            return

        if not CURRENT_SEASON_SPLASH_PATH.exists():
            messagebox.showerror(
                "Aktif sezon splash'i bulunamadı",
                (
                    "assets/current_season_splash.png bulunamadı.\n\n"
                    "main.py ile birlikte assets klasörünü de "
                    "uygulama klasöründe tut."
                )
            )
            return

        answer = self.ask_confirm(
            "Aktif Sezon Splash",
            (
                "Gönderdiğin güncel Fortnite splash'i "
                "geri yüklensin mi?"
            ),
            confirm_text="Geri Yükle",
            cancel_text="Vazgeç"
        )

        if not answer:
            return

        try:
            image = self.load_rgba_image(
                CURRENT_SEASON_SPLASH_PATH
            )

            self.save_rgba_png(
                image,
                self.splash_path
            )

            self.set_status(
                "Aktif sezon Fortnite splash'i geri yüklendi."
            )

            self.show_toast(
                "✓ Aktif sezon splash'i geri yüklendi."
            )

            self.update_active_splash_status()

        except PermissionError:
            messagebox.showerror(
                "Yönetici izni gerekli",
                (
                    "Fortnite klasörüne yazma izni yok.\n\n"
                    "Uygulamayı yönetici olarak çalıştır."
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
            text_color="gray65"
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
