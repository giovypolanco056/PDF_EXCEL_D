# -*- coding: utf-8 -*-
"""
ui/screen_select_files.py — Paso 2: Selección de archivos PDF
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Callable

from templates.registry import get_type
from ui import theme as T
from ui.widgets import (
    Card, PrimaryButton, SecondaryButton, GhostButton,
    FileListBox, Divider, StatusBadge,
)


class ScreenSelectFiles(tk.Frame):
    """
    Pantalla para seleccionar archivos PDF o una carpeta completa.
    Muestra una lista previa de los archivos que se procesarán.
    """

    def __init__(
        self,
        parent,
        type_id: str,
        on_back: Callable,
        on_process: Callable[[list[str]], None],
        **kw,
    ):
        kw.setdefault("bg", T.BG)
        super().__init__(parent, **kw)
        self._type_id = type_id
        self._on_back = on_back
        self._on_process = on_process
        self._pdf_paths: list[str] = []
        self._build()

    def _build(self):
        doc_type = get_type(self._type_id)
        color = doc_type.color if doc_type else T.PRIMARY_LIGHT

        # ── Cabecera ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=T.PRIMARY, pady=8)
        header.pack(fill="x")

        nav = tk.Frame(header, bg=T.PRIMARY)
        nav.pack(fill="x", padx=10)

        GhostButton(
            nav,
            text="← Volver",
            bg=T.PRIMARY,
            fg="#93C5FD",
            activebackground=T.PRIMARY,
            activeforeground=T.TEXT_ON_DARK,
            command=self._on_back,
        ).pack(side="left")

        icon = doc_type.icon if doc_type else "📄"
        label = doc_type.label if doc_type else self._type_id

        tk.Label(
            header,
            text=f"{icon}  {label}",
            font=T.FONT_XL,
            bg=T.PRIMARY,
            fg=T.TEXT_ON_DARK,
        ).pack(pady=(T.PAD_SM, 0))

        tk.Label(
            header,
            text="Paso 2 de 3 — Selecciona los archivos a procesar",
            font=T.FONT_SM,
            bg=T.PRIMARY,
            fg="#93C5FD",
        ).pack()

        # ── Cuerpo ────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=T.BG, padx=10, pady=8)
        body.pack(fill="both", expand=True, padx=T.PAD_BASE, pady=T.PAD_BASE)

        # Botones de selección
        selection_row = tk.Frame(body, bg=T.BG)
        selection_row.pack(fill="x", pady=(0, 5))

        SecondaryButton(
            selection_row,
            text="📄  Seleccionar archivos PDF",
            command=self._pick_files,
        ).pack(side="left", padx=(0, T.PAD_SM))

        SecondaryButton(
            selection_row,
            text="📁  Seleccionar carpeta",
            command=self._pick_folder,
        ).pack(side="left")

        GhostButton(
            selection_row,
            text="✕  Limpiar selección",
            command=self._clear,
            bg=T.BG,
        ).pack(side="right")

        # Área de lista
        list_frame = tk.Frame(body, bg=T.SURFACE, pady=0)
        list_frame.pack(fill="both", expand=True)

        list_header = tk.Frame(list_frame, bg=T.SURFACE, padx=T.PAD_BASE, pady=T.PAD_SM)
        list_header.pack(fill="x")

        tk.Label(
            list_header,
            text="Archivos seleccionados",
            font=(T.FONT_FAMILY, 10, "bold"),
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        ).pack(side="left")

        self._badge_count = StatusBadge(list_header, text="0 archivos", style="neutral")
        self._badge_count.pack(side="right")

        Divider(list_frame).pack(fill="x")

        self._file_list = FileListBox(list_frame)
        self._file_list.pack(fill="both", expand=True, padx=T.PAD_SM, pady=T.PAD_SM)

        self._lbl_empty = tk.Label(
            list_frame,
            text="Ningún archivo seleccionado.\nUsa los botones de arriba para agregar PDFs.",
            font=T.FONT_BASE,
            bg=T.SURFACE,
            fg=T.TEXT_DISABLED,
            justify="center",
        )
        self._lbl_empty.place(relx=0.5, rely=0.5, anchor="center")

        # ── Pie ───────────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=T.BG, padx=10, pady=5)
        footer.pack(fill="x")

        Divider(footer).pack(fill="x", pady=(0, T.PAD_BASE))

        self._btn_process = PrimaryButton(
            footer,
            text="⚙️  Procesar archivos",
            state="disabled",
            command=self._start_process,
        )
        self._btn_process.pack(side="right")

        self._lbl_hint = tk.Label(
            footer,
            text="Selecciona al menos un PDF para continuar",
            font=T.FONT_SM,
            bg=T.BG,
            fg=T.TEXT_DISABLED,
        )
        self._lbl_hint.pack(side="left")

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("Archivos PDF", "*.pdf *.PDF"), ("Todos", "*.*")],
        )
        if paths:
            self._add_paths(list(paths))

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self._add_paths([folder])

    def _add_paths(self, new_paths: list[str]):
        existing = set(self._pdf_paths)
        for p in new_paths:
            if p not in existing:
                self._pdf_paths.append(p)
                existing.add(p)
        self._refresh_list()

    def _clear(self):
        self._pdf_paths = []
        self._refresh_list()

    def _refresh_list(self):
        from utils.files import collect_pdfs
        pdfs = collect_pdfs(self._pdf_paths)
        names = [p.name for p in pdfs]

        if names:
            self._lbl_empty.place_forget()
            self._file_list.set_items(names)
            n = len(names)
            self._badge_count.set(f"{n} archivo{'s' if n != 1 else ''}", "info")
            self._btn_process.config(state="normal")
            self._lbl_hint.config(
                text=f"{n} PDF{'s' if n != 1 else ''} listo{'s' if n != 1 else ''} para procesar",
                fg=T.SUCCESS,
            )
        else:
            self._file_list.clear()
            self._lbl_empty.place(relx=0.5, rely=0.5, anchor="center")
            self._badge_count.set("0 archivos", "neutral")
            self._btn_process.config(state="disabled")
            self._lbl_hint.config(
                text="Selecciona al menos un PDF para continuar",
                fg=T.TEXT_DISABLED,
            )

    def _start_process(self):
        self._on_process(self._pdf_paths)
