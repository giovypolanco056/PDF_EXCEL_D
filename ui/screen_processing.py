# -*- coding: utf-8 -*-
"""
ui/screen_processing.py — Paso 3: Procesamiento con barra de progreso
"""

import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

from templates.registry import get_type
from processors.engine import run_batch, ProcessResult
from ui import theme as T
from ui.widgets import ProgressBar, StatusBadge, Divider, GhostButton


class ScreenProcessing(tk.Frame):
    """
    Pantalla de procesamiento.
    Lanza el motor en un hilo de fondo y actualiza la UI
    mediante after() para mantener la responsividad.
    """

    def __init__(
        self,
        parent,
        type_id: str,
        pdf_paths: list[str],
        output_dir: Optional[str],
        on_done: Callable[["ProcessResult"], None],
        on_cancel: Callable,
        **kw,
    ):
        kw.setdefault("bg", T.BG)
        super().__init__(parent, **kw)
        self._type_id   = type_id
        self._pdf_paths = pdf_paths
        self._output_dir = output_dir
        self._on_done   = on_done
        self._on_cancel = on_cancel
        self._duplicate_queue: list[tuple] = []   # (event, answer_var, args)
        self._build()
        self.after(200, self._start)

    def _build(self):
        doc_type = get_type(self._type_id)
        icon  = doc_type.icon  if doc_type else "⚙️"
        label = doc_type.label if doc_type else self._type_id

        # ── Cabecera ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=T.PRIMARY, pady=T.PAD_XL)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"{icon}  Procesando {label}",
            font=T.FONT_XL,
            bg=T.PRIMARY,
            fg=T.TEXT_ON_DARK,
        ).pack()

        tk.Label(
            header,
            text="Por favor espera mientras se procesan los documentos…",
            font=T.FONT_SM,
            bg=T.PRIMARY,
            fg="#93C5FD",
        ).pack(pady=(4, 0))

        # ── Cuerpo ────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=T.BG)
        body.pack(fill="both", expand=True, padx=T.PAD_XL, pady=T.PAD_XL)

        # Progreso
        prog_card = tk.Frame(body, bg=T.SURFACE, padx=T.CARD_PAD, pady=T.CARD_PAD)
        prog_card.pack(fill="x", pady=(0, T.PAD_BASE))

        prog_header = tk.Frame(prog_card, bg=T.SURFACE)
        prog_header.pack(fill="x", pady=(0, T.PAD_SM))

        tk.Label(
            prog_header,
            text="Progreso",
            font=(T.FONT_FAMILY, 10, "bold"),
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        ).pack(side="left")

        self._lbl_counter = tk.Label(
            prog_header,
            text="0 / ?",
            font=T.FONT_SM,
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        )
        self._lbl_counter.pack(side="right")

        self._progress = ProgressBar(prog_card)
        self._progress.pack(fill="x", pady=(0, T.PAD_SM))

        self._lbl_status = tk.Label(
            prog_card,
            text="Iniciando…",
            font=T.FONT_SM,
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
            anchor="w",
        )
        self._lbl_status.pack(fill="x")

        # Log en tiempo real
        log_card = tk.Frame(body, bg=T.SURFACE, padx=T.CARD_PAD, pady=T.CARD_PAD)
        log_card.pack(fill="both", expand=True)

        tk.Label(
            log_card,
            text="Detalle del proceso",
            font=(T.FONT_FAMILY, 10, "bold"),
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, T.PAD_SM))

        Divider(log_card).pack(fill="x", pady=(0, T.PAD_SM))

        self._log_text = tk.Text(
            log_card,
            font=T.FONT_XS,
            bg=T.SURFACE_ALT,
            fg=T.TEXT_PRIMARY,
            relief="flat",
            bd=0,
            state="disabled",
            wrap="word",
            height=10,
        )
        scroll = tk.Scrollbar(log_card, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._log_text.pack(fill="both", expand=True)

    def _log(self, msg: str, tag: str = ""):
        self._log_text.config(state="normal")
        self._log_text.insert("end", msg + "\n", tag)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _start(self):
        self._log("▶ Iniciando procesamiento…")
        run_batch(
            type_id     = self._type_id,
            pdf_paths   = self._pdf_paths,
            output_dir  = self._output_dir,
            on_progress = self._on_progress,
            on_duplicate= self._on_duplicate,
            on_done     = self._on_batch_done,
            on_error    = self._on_batch_error,
        )

    # ── Callbacks desde el hilo de fondo (thread-safe via after) ─────────────

    def _on_progress(self, current: int, total: int, msg: str):
        self.after(0, lambda: self._update_progress(current, total, msg))

    def _update_progress(self, current: int, total: int, msg: str):
        frac = (current / total) if total > 0 else 0
        self._progress.set(frac)
        self._lbl_counter.config(text=f"{current} / {total}")
        self._lbl_status.config(text=msg)
        self._log(f"  {msg}")

    def _on_duplicate(self, nombre: str, numero: str, fecha: str) -> bool:
        """
        Llamado desde el hilo de fondo.
        Muestra un diálogo modal en el hilo principal y espera respuesta.
        """
        import threading
        result_var = [None]
        event = threading.Event()

        self.after(0, lambda: self._show_duplicate_dialog(
            nombre, numero, fecha, result_var, event
        ))
        event.wait()  # Bloquea el hilo de fondo hasta que el usuario responda
        return result_var[0] is True

    def _show_duplicate_dialog(
        self,
        nombre: str,
        numero: str,
        fecha: str,
        result_var: list,
        event,
    ):
        dialog = tk.Toplevel(self)
        dialog.title("Documento duplicado")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg=T.BG)

        # Centrar
        dialog.update_idletasks()
        w, h = 440, 260
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(
            dialog,
            text="⚠️  Documento duplicado",
            font=T.FONT_LG,
            bg=T.BG,
            fg=T.WARNING,
        ).pack(pady=(T.PAD_LG, T.PAD_SM))

        msg = (
            f"El documento ya existe en el Excel:\n\n"
            f"  Archivo : {nombre}\n"
            f"  Número  : {numero}\n"
            f"  Fecha   : {fecha}\n\n"
            f"¿Deseas sobreescribirlo?"
        )
        tk.Label(
            dialog,
            text=msg,
            font=T.FONT_SM,
            bg=T.BG,
            fg=T.TEXT_PRIMARY,
            justify="left",
            padx=T.PAD_LG,
        ).pack()

        btn_row = tk.Frame(dialog, bg=T.BG, pady=T.PAD_LG)
        btn_row.pack()

        def _yes():
            result_var[0] = True
            dialog.destroy()
            event.set()

        def _no():
            result_var[0] = False
            dialog.destroy()
            event.set()

        from ui.widgets import PrimaryButton, SecondaryButton
        SecondaryButton(btn_row, text="No, omitir", command=_no).pack(side="left", padx=T.PAD_SM)
        PrimaryButton(btn_row, text="Sí, sobreescribir", command=_yes).pack(side="left")

        dialog.protocol("WM_DELETE_WINDOW", _no)

    def _on_batch_done(self, result: "ProcessResult"):
        self.after(0, lambda: self._finish(result))

    def _finish(self, result: "ProcessResult"):
        self._progress.set(1.0)
        self._log(
            f"\n✅ Completado — "
            f"{result.exitosos} procesados, "
            f"{result.omitidos} omitidos, "
            f"{result.fallidos} errores"
        )
        for w in result.advertencias:
            self._log(f"  ⚠ {w}")
        for e in result.errores:
            self._log(f"  ✗ {e}")
        self._on_done(result)

    def _on_batch_error(self, msg: str):
        self.after(0, lambda: self._show_fatal(msg))

    def _show_fatal(self, msg: str):
        self._progress.set(0)
        self._lbl_status.config(text=f"Error: {msg}", fg=T.ERROR)
        self._log(f"\n✗ Error fatal: {msg}")
