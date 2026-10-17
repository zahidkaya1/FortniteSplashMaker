"""Fortnite Splash Maker için tek tip, modal CustomTkinter pencereleri.

Dosya sistemi işlemleri burada yapılmaz; pencereler yalnızca kullanıcı kararını
veya kütüphanede kullanılacak görünen adı döndürür.
"""

import customtkinter as ctk

from .components import (
    UI_ACCENT,
    UI_BG,
    UI_BORDER,
    UI_SURFACE,
    UI_SURFACE_DARK,
    UI_TEXT,
    UI_TEXT_MUTED,
    UI_TEXT_SECONDARY,
    create_action_button,
)


DIALOG_BORDER = UI_BORDER
DANGER_COLOR = "#B74C5C"
DANGER_HOVER = "#983E4D"


def normalize_library_name(value, default_name):
    """Boş girişte otomatik ad kullan; 60 karakter sınırını uygula."""
    name = " ".join(str(value).strip().split())
    if not name:
        name = default_name
    if len(name) > 60:
        raise ValueError("Ad en fazla 60 karakter olabilir.")
    return name


def _make_dialog(parent, title, width, height):
    """Pencereyi ebeveynin ortasına yerleştirip aynı tema kartını oluştur."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(f"{width}x{height}")
    dialog.resizable(False, False)
    dialog.configure(fg_color=UI_BG)
    dialog.transient(parent)

    parent.update_idletasks()
    parent_width = max(parent.winfo_width(), width)
    parent_height = max(parent.winfo_height(), height)
    x = parent.winfo_rootx() + (parent_width - width) // 2
    y = parent.winfo_rooty() + (parent_height - height) // 2
    # Küçük ekranlarda diyalog penceresi görüntü alanının dışına taşmasın.
    x = max(0, min(x, parent.winfo_screenwidth() - width))
    y = max(0, min(y, parent.winfo_screenheight() - height))
    dialog.geometry(f"{width}x{height}+{x}+{y}")

    card = ctk.CTkFrame(
        dialog,
        width=width - 32,
        height=height - 32,
        corner_radius=14,
        fg_color=UI_SURFACE,
        border_width=1,
        border_color=DIALOG_BORDER,
    )
    card.place(x=16, y=16)
    card.pack_propagate(False)
    card.grid_propagate(False)
    return dialog, card


def _finish_modal(parent, dialog, focus_widget=None):
    """Pencere kapanana kadar sadece modal pencerenin kullanılmasını sağla."""
    dialog.update_idletasks()
    dialog.grab_set()
    if focus_widget is None:
        dialog.focus_force()
    else:
        focus_widget.focus_set()
    parent.wait_window(dialog)


def show_confirm_dialog(
    parent,
    title,
    message,
    confirm_text="Evet",
    cancel_text="Hayır",
):
    """İptal/ESC/pencere kapatma False; onay True döndürür."""
    dialog, card = _make_dialog(parent, title, 480, 254)
    result = {"confirmed": False}

    ctk.CTkLabel(
        card,
        text=title,
        width=405,
        height=32,
        anchor="w",
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=UI_TEXT,
    ).place(x=22, y=18)

    ctk.CTkLabel(
        card,
        text=message,
        width=402,
        height=96,
        anchor="w",
        justify="left",
        wraplength=398,
        font=ctk.CTkFont(size=13),
        text_color=UI_TEXT_SECONDARY,
    ).place(x=22, y=56)

    ctk.CTkFrame(
        card, width=400, height=1, fg_color=UI_BORDER,
    ).place(x=22, y=160)

    def cancel(_event=None):
        dialog.destroy()

    def confirm(_event=None):
        result["confirmed"] = True
        dialog.destroy()

    cancel_button = create_action_button(
        card,
        variant="outline",
        text=cancel_text,
        width=129,
        height=37,
        command=cancel,
    )
    cancel_button.place(x=150, y=172)

    destructive = confirm_text.casefold() in {"sil", "kaldır", "sıfırla"}
    confirm_button = create_action_button(
        card,
        variant="primary",
        text=confirm_text,
        width=130,
        height=37,
        fg_color=DANGER_COLOR if destructive else UI_ACCENT,
        hover_color=DANGER_HOVER if destructive else "#1C64B3",
        command=confirm,
    )
    confirm_button.place(x=292, y=172)

    dialog.bind("<Escape>", cancel)
    dialog.bind("<Return>", confirm)
    dialog.protocol("WM_DELETE_WINDOW", cancel)
    _finish_modal(parent, dialog, cancel_button)
    return result["confirmed"]


def show_library_name_dialog(parent, default_name):
    """Kütüphane adını sorar; İptal/ESC durumunda None döndürür."""
    dialog, card = _make_dialog(parent, "Kütüphaneye Ekle", 500, 300)
    result = {"value": None}

    ctk.CTkLabel(
        card,
        text="Kütüphaneye Ekle",
        width=424,
        height=34,
        anchor="w",
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=UI_TEXT,
    ).place(x=22, y=16)

    ctk.CTkLabel(
        card,
        text=(
            "Görsele özel bir ad verebilirsin. Boş bırakırsan "
            f"otomatik olarak {default_name} kullanılır."
        ),
        width=424,
        height=43,
        wraplength=421,
        anchor="w",
        justify="left",
        text_color=UI_TEXT_SECONDARY,
        font=ctk.CTkFont(size=12),
    ).place(x=22, y=55)

    ctk.CTkLabel(
        card,
        text="GÖRSEL ADI",
        width=424,
        height=18,
        anchor="w",
        text_color=UI_TEXT_MUTED,
        font=ctk.CTkFont(size=11, weight="bold"),
    ).place(x=22, y=107)

    entry = ctk.CTkEntry(
        card,
        width=424,
        height=41,
        corner_radius=9,
        fg_color=UI_SURFACE_DARK,
        border_color=UI_BORDER,
        text_color=UI_TEXT,
        placeholder_text=default_name,
    )
    entry.place(x=22, y=128)

    error_label = ctk.CTkLabel(
        card,
        text="",
        width=424,
        height=21,
        anchor="w",
        text_color="#F2A3B0",
        font=ctk.CTkFont(size=11),
    )
    error_label.place(x=22, y=174)

    def cancel(_event=None):
        dialog.destroy()

    def confirm(_event=None):
        try:
            value = normalize_library_name(entry.get(), default_name)
        except ValueError as error:
            error_label.configure(text=str(error))
            return
        result["value"] = value
        dialog.destroy()

    cancel_button = create_action_button(
        card,
        variant="outline",
        text="İptal",
        width=129,
        height=37,
        command=cancel,
    )
    cancel_button.place(x=162, y=210)
    create_action_button(
        card,
        variant="primary",
        text="Kütüphaneye Ekle",
        width=143,
        height=37,
        command=confirm,
    ).place(x=303, y=210)

    entry.bind("<Return>", confirm)
    dialog.bind("<Escape>", cancel)
    dialog.protocol("WM_DELETE_WINDOW", cancel)
    _finish_modal(parent, dialog, entry)
    return result["value"]
