# -*- coding: utf-8 -*-
"""
ui/theme.py — Sistema de diseño de la aplicación

Paleta inspirada en documentos corporativos: azul institucional profundo
como base, blanco roto para superficies, verde confirmación, rojo error.
Tipografía sin serifa, tamaños generosos para facilidad de uso.
"""

# ── Colores ───────────────────────────────────────────────────────────────────
PRIMARY       = "#1E3A5F"    # Azul institucional profundo
PRIMARY_LIGHT = "#2563EB"    # Azul acción / botones
PRIMARY_HOVER = "#1D4ED8"    # Hover botón primario
ACCENT        = "#3B82F6"    # Azul claro, selección activa

SUCCESS       = "#059669"    # Verde confirmación
SUCCESS_BG    = "#D1FAE5"    # Fondo verde suave
WARNING       = "#D97706"    # Ámbar advertencia
WARNING_BG    = "#FEF3C7"
ERROR         = "#DC2626"    # Rojo error
ERROR_BG      = "#FEE2E2"

BG            = "#F1F5F9"    # Fondo general (gris azulado muy claro)
SURFACE       = "#FFFFFF"    # Tarjetas / paneles
SURFACE_ALT   = "#F8FAFC"    # Superficies alternas
BORDER        = "#E2E8F0"    # Bordes suaves
BORDER_FOCUS  = "#3B82F6"

TEXT_PRIMARY  = "#0F172A"    # Texto principal
TEXT_SECONDARY= "#475569"    # Texto secundario
TEXT_DISABLED = "#94A3B8"    # Texto deshabilitado
TEXT_ON_DARK  = "#FFFFFF"    # Texto sobre fondos oscuros

# ── Tipografía ────────────────────────────────────────────────────────────────
FONT_FAMILY   = "Segoe UI"   # Windows; fallback: sans-serif

FONT_XS    = (FONT_FAMILY, 9)
FONT_SM    = (FONT_FAMILY, 10)
FONT_BASE  = (FONT_FAMILY, 11)
FONT_MD    = (FONT_FAMILY, 13)
FONT_LG    = (FONT_FAMILY, 15, "bold")
FONT_XL    = (FONT_FAMILY, 20, "bold")
FONT_TITLE = (FONT_FAMILY, 26, "bold")

# ── Dimensiones ───────────────────────────────────────────────────────────────
RADIUS        = 8     # Border radius general (px)
RADIUS_LG     = 12
PAD_SM        = 8
PAD_BASE      = 16
PAD_LG        = 24
PAD_XL        = 32

BTN_HEIGHT    = 44    # Altura estándar de botón
BTN_HEIGHT_LG = 56    # Botón grande (acción principal)
CARD_PAD      = 20
