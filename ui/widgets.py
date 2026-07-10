# -*- coding: utf-8 -*-
"""
ui/widgets.py — Widgets reutilizables de la aplicación
"""

import tkinter as tk
from tkinter import ttk
from ui import theme as T


class Card(tk.Frame):
    """Panel con fondo blanco, borde suave y radio de esquinas simulado."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.SURFACE)
        kw.setdefault("padx", T.CARD_PAD)
        kw.setdefault("pady", T.CARD_PAD)
        super().__init__(parent, **kw)


class PrimaryButton(tk.Button):
    """Botón azul principal de acción."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.PRIMARY_LIGHT)
        kw.setdefault("fg", T.TEXT_ON_DARK)
        kw.setdefault("activebackground", T.PRIMARY_HOVER)
        kw.setdefault("activeforeground", T.TEXT_ON_DARK)
        kw.setdefault("font", T.FONT_MD)
        kw.setdefault("relief", "flat")
        kw.setdefault("cursor", "hand2")
        kw.setdefault("padx", T.PAD_LG)
        kw.setdefault("pady", 12)
        kw.setdefault("bd", 0)
        super().__init__(parent, **kw)
        self.bind("<Enter>", lambda e: self.config(bg=T.PRIMARY_HOVER))
        self.bind("<Leave>", lambda e: self.config(bg=T.PRIMARY_LIGHT))


class SecondaryButton(tk.Button):
    """Botón secundario con borde."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.SURFACE)
        kw.setdefault("fg", T.PRIMARY_LIGHT)
        kw.setdefault("activebackground", T.BG)
        kw.setdefault("activeforeground", T.PRIMARY_LIGHT)
        kw.setdefault("font", T.FONT_BASE)
        kw.setdefault("relief", "flat")
        kw.setdefault("cursor", "hand2")
        kw.setdefault("padx", T.PAD_BASE)
        kw.setdefault("pady", 10)
        kw.setdefault("bd", 1)
        kw.setdefault("highlightbackground", T.BORDER)
        kw.setdefault("highlightthickness", 1)
        super().__init__(parent, **kw)
        self.bind("<Enter>", lambda e: self.config(bg=T.BG))
        self.bind("<Leave>", lambda e: self.config(bg=T.SURFACE))


class GhostButton(tk.Button):
    """Botón sin fondo, solo texto subrayado."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.BG)
        kw.setdefault("fg", T.TEXT_SECONDARY)
        kw.setdefault("activebackground", T.BG)
        kw.setdefault("activeforeground", T.PRIMARY_LIGHT)
        kw.setdefault("font", T.FONT_SM)
        kw.setdefault("relief", "flat")
        kw.setdefault("cursor", "hand2")
        kw.setdefault("bd", 0)
        super().__init__(parent, **kw)


class StatusBadge(tk.Label):
    """Etiqueta de estado con color de fondo."""
    STYLES = {
        "success": (T.SUCCESS,    T.SUCCESS_BG),
        "warning": (T.WARNING,    T.WARNING_BG),
        "error":   (T.ERROR,      T.ERROR_BG),
        "info":    (T.PRIMARY_LIGHT, "#DBEAFE"),
        "neutral": (T.TEXT_SECONDARY, T.BORDER),
    }

    def __init__(self, parent, text: str = "", style: str = "neutral", **kw):
        fg, bg = self.STYLES.get(style, self.STYLES["neutral"])
        kw.setdefault("font", T.FONT_SM)
        kw.setdefault("padx", 10)
        kw.setdefault("pady", 4)
        super().__init__(parent, text=text, fg=fg, bg=bg, **kw)

    def set(self, text: str, style: str = "neutral"):
        fg, bg = self.STYLES.get(style, self.STYLES["neutral"])
        self.config(text=text, fg=fg, bg=bg)


class ProgressBar(tk.Frame):
    """Barra de progreso personalizada."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.BG)
        super().__init__(parent, height=8, **kw)
        self.pack_propagate(False)

        self._track = tk.Frame(self, bg=T.BORDER, height=8)
        self._track.pack(fill="x")

        self._fill = tk.Frame(self._track, bg=T.PRIMARY_LIGHT, height=8)
        self._fill.place(relx=0, rely=0, relwidth=0, relheight=1)

        self._value = 0.0

    def set(self, fraction: float):
        """fraction entre 0.0 y 1.0"""
        self._value = max(0.0, min(1.0, fraction))
        self._fill.place(relwidth=self._value)

    def reset(self):
        self.set(0.0)


class Divider(tk.Frame):
    """Línea divisoria horizontal."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.BORDER)
        kw.setdefault("height", 1)
        super().__init__(parent, **kw)


class SectionLabel(tk.Label):
    """Etiqueta de sección con texto secundario pequeño."""
    def __init__(self, parent, text: str, **kw):
        kw.setdefault("bg", T.BG)
        kw.setdefault("fg", T.TEXT_SECONDARY)
        kw.setdefault("font", T.FONT_SM)
        super().__init__(parent, text=text.upper(), **kw)


class FileListBox(tk.Frame):
    """Lista scrollable de archivos seleccionados."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", T.SURFACE)
        super().__init__(parent, **kw)

        self._listbox = tk.Listbox(
            self,
            font=T.FONT_SM,
            bg=T.SURFACE,
            fg=T.TEXT_PRIMARY,
            selectbackground=T.ACCENT,
            selectforeground=T.TEXT_ON_DARK,
            activestyle="none",
            selectmode="extended",   # permite elegir uno o varios para quitar
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scrollbar.set)

        self._listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def set_items(self, items: list[str]):
        self._listbox.delete(0, "end")
        for item in items:
            self._listbox.insert("end", f"  📄 {item}")

    def clear(self):
        self._listbox.delete(0, "end")

    def count(self) -> int:
        return self._listbox.size()

    def selected_indices(self) -> list[int]:
        """Índices actualmente seleccionados en la lista."""
        return list(self._listbox.curselection())

    def bind_remove_key(self, callback):
        """Ejecuta callback al pulsar Supr/Delete o Retroceso sobre la lista."""
        self._listbox.bind("<Delete>", lambda e: callback())
        self._listbox.bind("<BackSpace>", lambda e: callback())

    def bind_double_click(self, callback):
        """Ejecuta callback(index) al hacer doble clic en un elemento."""
        def _handler(event):
            idx = self._listbox.nearest(event.y)
            if idx >= 0:
                callback(idx)
        self._listbox.bind("<Double-Button-1>", _handler)
