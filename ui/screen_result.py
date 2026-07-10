# -*- coding: utf-8 -*-
"""
ui/screen_result.py — Paso 4: Resultado y acciones de descarga
"""

import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

from processors.engine import ProcessResult
from processors.extractor_encabezado import NOMBRES_TIPO
from ui import theme as T
from ui.widgets import PrimaryButton, SecondaryButton, GhostButton, Divider, StatusBadge


# Estado del documento → (ícono, etiqueta de color de la etiqueta Text)
_ESTADO_ICONO = {
    "ok":          ("✓", "ok"),
    "advertencia": ("⚠", "warn"),
    "error":       ("✗", "err"),
    "fallido":     ("✗", "err"),
    "omitido":     ("⊘", "muted"),
    "reemplazado": ("↻", "muted"),
}


class ScreenResult(tk.Frame):
    """
    Pantalla final: muestra el resumen del procesamiento,
    la ubicación del Excel y los botones de acción.
    """

    def __init__(
        self,
        parent,
        result: "ProcessResult",
        on_new: Callable,
        **kw,
    ):
        kw.setdefault("bg", T.BG)
        super().__init__(parent, **kw)
        self._result = result
        self._on_new = on_new
        self._build()

    def _build(self):
        r = self._result
        has_excel = r.excel_path and r.excel_path.exists()
        all_ok    = r.fallidos == 0 and r.omitidos == 0
        partial   = r.fallidos > 0 or r.omitidos > 0

        # ── Cabecera de estado ────────────────────────────────────────────────
        hdr_color = T.SUCCESS if all_ok else (T.WARNING if partial else T.ERROR)
        hdr_icon  = "✅" if all_ok else ("⚠️" if partial else "✗")
        hdr_text  = (
            "¡Proceso completado!"
            if all_ok
            else "Proceso completado con advertencias"
            if partial
            else "El proceso encontró errores"
        )

        header = tk.Frame(self, bg=hdr_color, pady=T.PAD_XL)
        header.pack(fill="x")

        tk.Label(
            header,
            text=hdr_icon,
            font=(T.FONT_FAMILY, 40),
            bg=hdr_color,
            fg=T.TEXT_ON_DARK,
        ).pack()

        tk.Label(
            header,
            text=hdr_text,
            font=T.FONT_XL,
            bg=hdr_color,
            fg=T.TEXT_ON_DARK,
        ).pack(pady=(T.PAD_SM, 0))

        # ── Cuerpo ────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=T.BG)
        body.pack(fill="both", expand=True, padx=T.PAD_BASE, pady=T.PAD_BASE)

        # Tarjeta de estadísticas
        stats_card = tk.Frame(body, bg=T.SURFACE, padx=T.CARD_PAD, pady=T.CARD_PAD)
        stats_card.pack(fill="x", pady=(0, T.PAD_BASE))

        tk.Label(
            stats_card,
            text="Resumen del procesamiento",
            font=(T.FONT_FAMILY, 10, "bold"),
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, T.PAD_SM))

        Divider(stats_card).pack(fill="x", pady=(0, T.PAD_BASE))

        stats_row = tk.Frame(stats_card, bg=T.SURFACE)
        stats_row.pack(fill="x")

        self._stat_block(stats_row, str(r.exitosos),  "Procesados",   T.SUCCESS)
        self._stat_block(stats_row, str(r.omitidos),  "Omitidos",     T.WARNING)
        self._stat_block(stats_row, str(r.fallidos),  "Con error",    T.ERROR)
        self._stat_block(stats_row, str(r.total),     "Total PDFs",   T.TEXT_SECONDARY)

        # Tarjeta de ubicación del Excel
        if has_excel:
            loc_card = tk.Frame(body, bg=T.SURFACE, padx=T.CARD_PAD, pady=T.CARD_PAD)
            loc_card.pack(fill="x", pady=(0, T.PAD_BASE))

            tk.Label(
                loc_card,
                text="Archivo generado",
                font=(T.FONT_FAMILY, 10, "bold"),
                bg=T.SURFACE,
                fg=T.TEXT_SECONDARY,
            ).pack(anchor="w", pady=(0, T.PAD_SM))

            Divider(loc_card).pack(fill="x", pady=(0, T.PAD_SM))

            path_str = str(r.excel_path)
            tk.Label(
                loc_card,
                text=path_str,
                font=T.FONT_SM,
                bg=T.SURFACE,
                fg=T.PRIMARY_LIGHT,
                cursor="hand2",
                wraplength=560,
                justify="left",
                anchor="w",
            ).pack(fill="x")

            # Botones de acción
            action_row = tk.Frame(loc_card, bg=T.SURFACE)
            action_row.pack(fill="x", pady=(T.PAD_BASE, 0))

            PrimaryButton(
                action_row,
                text="📊  Abrir Excel",
                command=lambda: self._open(r.excel_path),
            ).pack(side="left", padx=(0, T.PAD_SM))

            SecondaryButton(
                action_row,
                text="📁  Abrir carpeta",
                command=lambda: self._open(r.output_dir),
            ).pack(side="left")

        # Detalle POR DOCUMENTO (agrupado por archivo)
        if r.documentos:
            self._build_detalle_documentos(body, r.documentos)

        # ── Pie ───────────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=T.BG, padx=T.PAD_XL, pady=T.PAD_BASE)
        footer.pack(fill="x")

        Divider(footer).pack(fill="x", pady=(0, T.PAD_BASE))

        PrimaryButton(
            footer,
            text="+ Procesar más documentos",
            command=self._on_new,
        ).pack(side="right")

    def _build_detalle_documentos(self, body, documentos: list):
        """Tarjeta con el detalle por documento: estado, tipo/NCF y problemas."""
        card = tk.Frame(body, bg=T.SURFACE, padx=T.CARD_PAD, pady=T.CARD_PAD)
        card.pack(fill="both", expand=True)

        con_problemas = sum(1 for d in documentos if d.get("problemas"))
        tk.Label(
            card,
            text=f"Detalle por documento  ({len(documentos)} archivos, "
                 f"{con_problemas} con observaciones)",
            font=(T.FONT_FAMILY, 10, "bold"),
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, T.PAD_SM))

        Divider(card).pack(fill="x", pady=(0, T.PAD_SM))

        wrap = tk.Frame(card, bg=T.SURFACE)
        wrap.pack(fill="both", expand=True)

        txt = tk.Text(
            wrap,
            font=T.FONT_XS,
            bg=T.SURFACE_ALT,
            fg=T.TEXT_PRIMARY,
            relief="flat",
            bd=0,
            state="disabled",
            wrap="word",
            height=12,
            spacing3=2,
        )
        scroll = tk.Scrollbar(wrap, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        # Colores por severidad
        txt.tag_configure("ok",    foreground=T.SUCCESS)
        txt.tag_configure("warn",  foreground=T.WARNING)
        txt.tag_configure("err",   foreground=T.ERROR)
        txt.tag_configure("muted", foreground=T.TEXT_DISABLED)
        txt.tag_configure("file",  foreground=T.TEXT_PRIMARY,
                          font=(T.FONT_FAMILY, 9, "bold"))
        txt.tag_configure("meta",  foreground=T.TEXT_SECONDARY)

        txt.config(state="normal")
        for d in documentos:
            icono, tag = _ESTADO_ICONO.get(d.get("estado", "ok"), ("•", "muted"))
            tipo = NOMBRES_TIPO.get(d.get("tipo"), d.get("tipo") or "?")
            ncf  = d.get("ncf") or "sin NCF"
            lineas = d.get("lineas", 0)

            txt.insert("end", f"{icono} ", tag)
            txt.insert("end", f"{d.get('archivo', '?')}", "file")
            txt.insert("end", f"   ·  {tipo} · {ncf}  ·  {lineas} línea(s)\n", "meta")

            for sev, msg in d.get("problemas", []):
                m_icono = "✗" if sev == "error" else "⚠"
                m_tag   = "err" if sev == "error" else "warn"
                txt.insert("end", f"        {m_icono} {msg}\n", m_tag)
        txt.config(state="disabled")

    def _stat_block(self, parent, value: str, label: str, color: str):
        frame = tk.Frame(parent, bg=T.SURFACE, padx=T.PAD_LG)
        frame.pack(side="left", expand=True)

        tk.Label(
            frame,
            text=value,
            font=(T.FONT_FAMILY, 28, "bold"),
            bg=T.SURFACE,
            fg=color,
        ).pack()

        tk.Label(
            frame,
            text=label,
            font=T.FONT_XS,
            bg=T.SURFACE,
            fg=T.TEXT_SECONDARY,
        ).pack()

    @staticmethod
    def _open(path: Optional[Path]):
        if path:
            from utils.files import open_path
            open_path(path)
