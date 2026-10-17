"""Uygulama içinde, ekran yerleşimini bozmadan gösterilen bildirimler.

Oluştur ekranında format bilgi alanını geçici olarak kullanır; diğer sekmelerde
alt durum satırının yerini alır. Modal onaylar ve kritik dosya hataları bu
bileşenin kapsamında değildir.
"""

from dataclasses import dataclass
from pathlib import Path
from tkinter import TclError

import customtkinter as ctk

from .components import UI_TEXT, UI_TEXT_SECONDARY


FEEDBACK_STYLES = {
    "success": {"background": "#18372D", "border": "#34785A", "title": "#B4F1D0"},
    "warning": {"background": "#3A3021", "border": "#9C7337", "title": "#FFE0A4"},
    "error": {"background": "#3D242D", "border": "#A65065", "title": "#FFD4DE"},
    "info": {"background": "#1E3451", "border": "#477BAF", "title": "#CFDEFF"},
}

DEFAULT_DURATIONS = {
    "success": 3500,
    "info": 5000,
    "warning": 6500,
    "error": None,  # Kullanıcı kapatana kadar kalır.
}

SUPPORTED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp"})


def shorten(value, limit=140):
    """Uzun dosya adları ve teknik hata metinleri alandan taşmasın."""
    value = " ".join(str(value).split())
    if len(value) <= limit:
        return value
    return value[:max(0, limit - 1)].rstrip() + "…"


@dataclass(frozen=True)
class FeedbackMessage:
    level: str
    title: str
    message: str
    details: str = ""

    @classmethod
    def from_values(cls, level, title, message, details=None):
        if level not in FEEDBACK_STYLES:
            raise ValueError(f"Bilinmeyen bildirim türü: {level}")
        return cls(
            level,
            shorten(title, 48),
            shorten(message, 145),
            shorten(details, 87) if details else "",
        )


def describe_image_error(error, path):
    """Pillow'un teknik hatasını anlaşılır bir kullanıcı mesajına çevirir."""
    filename = Path(path).name if path else ""
    if Path(filename).suffix.casefold() not in SUPPORTED_IMAGE_SUFFIXES:
        return FeedbackMessage.from_values(
            "error", "Desteklenmeyen dosya",
            "Lütfen PNG, JPG, WEBP veya BMP biçiminde bir görsel seçin.", filename,
        )
    if isinstance(error, FileNotFoundError):
        return FeedbackMessage.from_values(
            "error", "Dosya bulunamadı",
            "Seçtiğin dosya taşınmış veya silinmiş olabilir.", filename,
        )
    if isinstance(error, PermissionError):
        return FeedbackMessage.from_values(
            "error", "Dosya okunamıyor",
            "Bu görsel için okuma izni yok. Dosya izinlerini kontrol et.", filename,
        )
    return FeedbackMessage.from_values(
        "error", "Görsel açılamadı",
        "Dosya bozuk veya geçerli bir görsel değil. Başka bir görsel dene.", filename,
    )


class FeedbackOverlay:
    """Sayfa içindeki ayrılmış alana, örtüşmeyen tek bildirim yerleştirir.

    Oluştur: önizleme kartındaki format bilgi satırı (480×66, x20/y420).
    Kütüphane/Ayarlar: pencerenin alt durum çubuğu (1100×44, x40/y708).
    """

    CREATOR_LEFT = 20
    CREATOR_TOP = 420
    CREATOR_WIDTH = 480
    CREATOR_HEIGHT = 66
    FOOTER_LEFT = 40
    FOOTER_TOP = 708
    FOOTER_WIDTH = 1100
    FOOTER_HEIGHT = 44

    def __init__(self, root):
        self.root = root
        self.frame = None
        self.dismiss_after_id = None
        self.sequence = 0
        self.current = None
        self.active_slot = None
        self.creator_master = None
        self.creator_hint = None

    def register_creator_slot(self, master, default_hint):
        """Oluştur kartındaki statik bilgi kutusunu geri çağrılabilir tutar."""
        self.creator_master = master
        self.creator_hint = default_hint

    def _current_page(self):
        page_mode = getattr(self.root, "page_mode", None)
        return page_mode.get() if page_mode is not None else None

    def _select_slot(self):
        if self._current_page() == "Oluştur" and self.creator_master is not None:
            return (
                "creator", self.creator_master,
                self.CREATOR_LEFT, self.CREATOR_TOP,
                self.CREATOR_WIDTH, self.CREATOR_HEIGHT,
            )
        return (
            "footer", self.root,
            self.FOOTER_LEFT, self.FOOTER_TOP,
            self.FOOTER_WIDTH, self.FOOTER_HEIGHT,
        )

    def dismiss(self):
        self.sequence += 1
        if self.dismiss_after_id is not None:
            try:
                self.root.after_cancel(self.dismiss_after_id)
            except (ValueError, RuntimeError, TclError):
                pass
            self.dismiss_after_id = None
        if self.frame is not None:
            try:
                self.frame.destroy()
            except (RuntimeError, TclError):
                pass
            self.frame = None

        if self.active_slot == "creator" and self.creator_hint is not None:
            self.creator_hint.place(x=self.CREATOR_LEFT, y=self.CREATOR_TOP)
        if self.active_slot == "footer":
            status_label = getattr(self.root, "status_label", None)
            if status_label is not None:
                status_label.place(x=40, y=724)

        self.active_slot = None
        self.current = None

    def show(self, level, title, message, *, details=None, duration=None):
        info = FeedbackMessage.from_values(level, title, message, details)
        self.dismiss()
        self.current = info
        style = FEEDBACK_STYLES[info.level]
        slot, master, left, top, width, height = self._select_slot()
        self.active_slot = slot

        if slot == "creator" and self.creator_hint is not None:
            self.creator_hint.place_forget()
        elif slot == "footer":
            status_label = getattr(self.root, "status_label", None)
            if status_label is not None:
                status_label.place_forget()

        frame = ctk.CTkFrame(
            master,
            width=width,
            height=height,
            corner_radius=10 if slot == "creator" else 9,
            border_width=1,
            border_color=style["border"],
            fg_color=style["background"],
        )
        frame.place(x=left, y=top)
        frame.pack_propagate(False)
        frame.grid_propagate(False)
        self.frame = frame

        if slot == "creator":
            # 66 piksellik ayrılmış bölge içinde tek satırlık açıklama ve dosya.
            ctk.CTkLabel(
                frame, text=shorten(info.title, 43),
                width=411, height=17, anchor="w",
                text_color=style["title"],
                font=ctk.CTkFont(size=12, weight="bold"),
            ).place(x=14, y=5)
            ctk.CTkLabel(
                frame, text=shorten(info.message, 74),
                width=446, height=17, anchor="w",
                text_color=UI_TEXT, font=ctk.CTkFont(size=11),
            ).place(x=14, y=24)
            if info.details:
                ctk.CTkLabel(
                    frame, text=shorten(info.details, 67),
                    width=446, height=15, anchor="w",
                    text_color=UI_TEXT_SECONDARY,
                    font=ctk.CTkFont(size=10),
                ).place(x=14, y=45)
            close_x, close_y, close_size = 442, 4, 28
        else:
            # Diğer sekmelerin içerik kartlarının altında, mevcut durum çubuğu.
            ctk.CTkLabel(
                frame, text=shorten(info.title, 32),
                width=200, height=30, anchor="w",
                text_color=style["title"],
                font=ctk.CTkFont(size=12, weight="bold"),
            ).place(x=14, y=7)
            ctk.CTkLabel(
                frame, text=shorten(info.message, 104),
                width=660, height=30, anchor="w",
                text_color=UI_TEXT, font=ctk.CTkFont(size=11),
            ).place(x=210, y=7)
            if info.details:
                ctk.CTkLabel(
                    frame, text=shorten(info.details, 32),
                    width=175, height=30, anchor="e",
                    text_color=UI_TEXT_SECONDARY,
                    font=ctk.CTkFont(size=10),
                ).place(x=875, y=7)
            close_x, close_y, close_size = 1060, 7, 30

        ctk.CTkButton(
            frame, width=close_size, height=28,
            text="×", corner_radius=7,
            fg_color="transparent", hover_color=style["border"],
            text_color=style["title"],
            font=ctk.CTkFont(size=17), command=self.dismiss,
        ).place(x=close_x, y=close_y)
        frame.lift()

        timeout = DEFAULT_DURATIONS[level] if duration is None else duration
        if timeout is not None and timeout > 0:
            token = self.sequence
            self.dismiss_after_id = self.root.after(
                timeout, lambda: self._dismiss_if_current(token)
            )
        return info

    def _dismiss_if_current(self, token):
        if token == self.sequence:
            self.dismiss()
