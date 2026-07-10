# -*- coding: utf-8 -*-
"""
ui/app.py — Ventana principal y orquestador de pantallas

Funciona como un simple "router": cambia entre pantallas destruyendo
la actual y creando la nueva, manteniendo el estado mínimo necesario
(tipo de documento seleccionado, rutas de PDF).
"""

import tkinter as tk
from pathlib import Path
from typing import Optional

from processors.engine import ProcessResult
from ui import theme as T

# Soporte de arrastrar-y-soltar archivos (opcional). Si tkinterdnd2 no está
# instalado, la app funciona igual pero sin drag-and-drop.
try:
    from tkinterdnd2 import TkinterDnD
    _BaseTk = TkinterDnD.Tk
    DND_DISPONIBLE = True
except Exception:       # pragma: no cover - depende del entorno
    _BaseTk = tk.Tk
    DND_DISPONIBLE = False


class App(_BaseTk):
    """Ventana raíz de la aplicación."""

    # Tamaño fijo de la ventana — grande para facilidad de uso
    WIN_W = 1024
    WIN_H = 768

    def __init__(self):
        super().__init__()
        self.title("PDF → Excel  |  EGEHID")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.minsize(1024, 768)
        self.configure(bg=T.BG)
        self.resizable(True, True)

        # Intentar aplicar ícono si existe
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - self.WIN_W) // 2
        y = (self.winfo_screenheight() - self.WIN_H) // 2
        self.geometry(f"{self.WIN_W}x{self.WIN_H}+{x}+{y}")

        # Estado de la sesión
        self._type_id:   Optional[str]       = None
        self._pdf_paths: list[str]            = []
        self._output_dir: Optional[str]       = None
        self._current_screen: Optional[tk.Frame] = None

        # Arrancar en la pantalla de selección de tipo
        self.show_select_type()

    # ── Navegación ────────────────────────────────────────────────────────────

    def _swap(self, new_frame: tk.Frame):
        """Reemplaza la pantalla actual por una nueva."""
        if self._current_screen:
            self._current_screen.destroy()
        self._current_screen = new_frame
        new_frame.pack(fill="both", expand=True)

    def show_select_type(self):
        from ui.screen_select_type import ScreenSelectType
        self._swap(ScreenSelectType(
            self,
            on_select   = self._on_type_selected,
            selected_id = self._type_id,   # recordar selección al volver
        ))

    def show_select_files(self):
        from ui.screen_select_files import ScreenSelectFiles
        self._swap(ScreenSelectFiles(
            self,
            type_id       = self._type_id,
            on_back       = self.show_select_type,
            on_process    = self._on_files_confirmed,
            initial_paths = self._pdf_paths,          # recordar archivos al volver
            on_change     = self._on_paths_changed,   # persistir en vivo
        ))

    def show_processing(self):
        from ui.screen_processing import ScreenProcessing
        self._swap(ScreenProcessing(
            self,
            type_id    = self._type_id,
            pdf_paths  = self._pdf_paths,
            output_dir = self._output_dir,
            on_done    = self._on_processing_done,
            on_cancel  = self.show_select_files,
        ))

    def show_result(self, result: "ProcessResult"):
        from ui.screen_result import ScreenResult
        self._swap(ScreenResult(
            self,
            result = result,
            on_new = self.show_select_type,
        ))

    # ── Callbacks entre pantallas ─────────────────────────────────────────────

    def _on_type_selected(self, type_id: str):
        # Si cambia el tipo, la selección de archivos previa sigue siendo válida
        # (son PDFs); solo se reprocesarán con la nueva plantilla.
        self._type_id = type_id
        self.show_select_files()

    def _on_paths_changed(self, pdf_paths: list[str]):
        """La pantalla de archivos avisa cada cambio para no perder la
        selección al ir atrás/adelante entre pantallas."""
        self._pdf_paths = list(pdf_paths)

    def _on_files_confirmed(self, pdf_paths: list[str]):
        self._pdf_paths = list(pdf_paths)
        self.show_processing()

    def _on_processing_done(self, result: "ProcessResult"):
        self.show_result(result)
