# -*- coding: utf-8 -*-
"""
ui/screen_select_type.py — Paso 1: Selección del tipo de documento
"""

import tkinter as tk
from typing import Callable

from templates.registry import all_types, DocumentType
from ui import theme as T
from ui.widgets import Card, PrimaryButton, Divider


class ScreenSelectType(tk.Frame):
    """
    Pantalla inicial donde el usuario elige el tipo de documento.
    Muestra una cuadrícula de tarjetas, una por tipo disponible.
    """

    def __init__(self, parent, on_select: Callable[[str], None], **kw):
        kw.setdefault("bg", T.BG)
        super().__init__(parent, **kw)
        self._on_select = on_select
        self._selected: str | None = None
        self._cards: dict[str, tk.Frame] = {}
        self._build()

    def _build(self):
        # ── Cabecera ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=T.PRIMARY, pady=T.PAD_XL)
        header.pack(fill="x")

        tk.Label(
            header,
            text="PDF  →  Excel",
            font=(T.FONT_FAMILY, 28, "bold"),
            bg=T.PRIMARY,
            fg=T.TEXT_ON_DARK,
        ).pack()
        tk.Label(
            header,
            text="Convierte documentos PDF al formato Excel",
            font=T.FONT_BASE,
            bg=T.PRIMARY,
            fg="#93C5FD",
        ).pack(pady=(4, 0))

        # ── Instrucción ───────────────────────────────────────────────────────
        tk.Label(
            self,
            text="¿Qué tipo de documento vas a procesar?",
            font=T.FONT_LG,
            bg=T.BG,
            fg=T.TEXT_PRIMARY,
        ).pack(pady=(T.PAD_XL, T.PAD_BASE))

        # ── Cuadrícula de tipos ───────────────────────────────────────────────
        grid = tk.Frame(self, bg=T.BG)
        grid.pack(padx=T.PAD_XL, pady=(0, T.PAD_BASE))

        types = all_types()
        cols = 3
        for idx, doc_type in enumerate(types):
            row, col = divmod(idx, cols)
            card = self._make_type_card(grid, doc_type)
            card.grid(row=row, column=col, padx=T.PAD_SM, pady=T.PAD_SM, sticky="nsew")
            grid.columnconfigure(col, weight=1)

        # ── Botón continuar ───────────────────────────────────────────────────
        bottom = tk.Frame(self, bg=T.BG)
        bottom.pack(fill="x", padx=T.PAD_XL, pady=T.PAD_BASE)

        Divider(bottom).pack(fill="x", pady=(0, T.PAD_BASE))

        self._btn_continue = PrimaryButton(
            bottom,
            text="Continuar  →",
            state="disabled",
            command=self._confirm,
        )
        self._btn_continue.pack(side="right")

        self._lbl_hint = tk.Label(
            bottom,
            text="Selecciona un tipo de documento para continuar",
            font=T.FONT_SM,
            bg=T.BG,
            fg=T.TEXT_DISABLED,
        )
        self._lbl_hint.pack(side="left", pady=4)

    def _make_type_card(self, parent: tk.Frame, doc_type: DocumentType) -> tk.Frame:
        """Crea la tarjeta visual de un tipo de documento."""
        card = tk.Frame(
            parent,
            bg=T.SURFACE,
            padx=8,
            pady=8,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground=T.BORDER,
        )

        tk.Label(
            card,
            text=doc_type.icon,
            font=(T.FONT_FAMILY, 20),
            bg=T.SURFACE,
        ).pack()

        tk.Label(
            card,
            text=doc_type.label,
            font=T.FONT_BASE,
            bg=T.SURFACE,
            fg=T.TEXT_PRIMARY,
        ).pack(pady=(4, 2))

        tk.Label(
            card,
            text=doc_type.description,
            font=T.FONT_SM,
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
            wraplength=120,
        ).pack()

        # Color strip inferior
        strip = tk.Frame(card, bg=doc_type.color, height=4)
        strip.pack(fill="x", side="bottom", pady=(T.PAD_SM, 0))

        # Bind clics en todos los hijos
        for widget in (card, *card.winfo_children(), strip):
            widget.bind("<Button-1>", lambda e, tid=doc_type.id: self._select(tid))

        self._cards[doc_type.id] = card
        return card

    def _select(self, type_id: str):
        # Deseleccionar anterior
        if self._selected and self._selected in self._cards:
            self._cards[self._selected].config(
                highlightbackground=T.BORDER,
                bg=T.SURFACE,
            )
            for child in self._cards[self._selected].winfo_children():
                child.config(bg=T.SURFACE)

        self._selected = type_id
        card = self._cards[type_id]
        card.config(highlightbackground=T.PRIMARY_LIGHT, bg="#EFF6FF")
        for child in card.winfo_children():
            child.config(bg="#EFF6FF")

        self._btn_continue.config(state="normal")
        self._lbl_hint.config(
            text=f"Tipo seleccionado: {type_id.replace('_', ' ').title()}",
            fg=T.PRIMARY_LIGHT,
        )

    def _confirm(self):
        if self._selected:
            self._on_select(self._selected)
