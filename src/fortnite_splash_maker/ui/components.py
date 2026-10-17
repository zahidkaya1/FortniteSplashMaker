"""Fortnite Splash Maker v1.1 arayüzünde tekrar kullanılan görsel stiller.

Bu modül yalnızca görünüm oluşturur; Fortnite dosyalarına erişmez.
"""

import customtkinter as ctk

UI_BG = "#101722"
UI_SURFACE = "#1B2635"
UI_SURFACE_RAISED = "#202F42"
UI_SURFACE_DARK = "#111D2B"
UI_BORDER = "#304158"
UI_ACCENT = "#2877CF"
UI_ACCENT_HOVER = "#1C64B3"
UI_TEXT = "#F0F5FC"
UI_TEXT_SECONDARY = "#A7B6CA"
UI_TEXT_MUTED = "#7F91AA"


def create_section_card(master, **kwargs):
    """Tüm sekmelerin kullandığı tutarlı çerçeve stili."""
    options = {
        "corner_radius": 15,
        "fg_color": UI_SURFACE,
        "border_width": 1,
        "border_color": UI_BORDER,
    }
    options.update(kwargs)
    return ctk.CTkFrame(master, **options)


def create_action_button(master, *, variant="secondary", **kwargs):
    """Birincil, ikincil ve çerçeveli işlem düğmeleri."""
    styles = {
        "primary": {
            "fg_color": UI_ACCENT,
            "hover_color": UI_ACCENT_HOVER,
            "text_color": UI_TEXT,
        },
        "secondary": {
            "fg_color": UI_SURFACE_RAISED,
            "hover_color": "#304560",
            "text_color": UI_TEXT,
        },
        "outline": {
            "fg_color": "transparent",
            "hover_color": UI_SURFACE_RAISED,
            "border_width": 1,
            "border_color": UI_BORDER,
            "text_color": UI_TEXT_SECONDARY,
        },
    }
    if variant not in styles:
        raise ValueError(f"Bilinmeyen buton stili: {variant}")
    options = {"height": 36, "corner_radius": 9, **styles[variant]}
    options.update(kwargs)
    return ctk.CTkButton(master, **options)


def create_status_badge(master, *, tone="neutral", **kwargs):
    """Durum rozetlerini tek bir renk eşlemesiyle oluşturur."""
    tones = {
        "neutral": (UI_SURFACE_RAISED, UI_TEXT_SECONDARY),
        "success": ("#1B3A35", "#9CE0C3"),
        "warning": ("#433724", "#F6D292"),
        "error": ("#49302F", "#F2B5AA"),
        "info": ("#203D5D", "#A8D3FF"),
    }
    if tone not in tones:
        raise ValueError(f"Bilinmeyen rozet tonu: {tone}")
    background, foreground = tones[tone]
    options = {
        "corner_radius": 9,
        "fg_color": background,
        "text_color": foreground,
    }
    options.update(kwargs)
    return ctk.CTkLabel(master, **options)
