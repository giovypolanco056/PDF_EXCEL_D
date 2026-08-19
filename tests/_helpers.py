# -*- coding: utf-8 -*-
"""
tests/_helpers.py — utilidades compartidas por las pruebas.

- Inserta la raíz del proyecto en sys.path para que `import processors...`
  funcione sin importar desde dónde se corran las pruebas.
- W(): construye una "palabra" de pdfplumber (texto + coordenadas) para
  fabricar tablas sintéticas sin depender de un PDF real.
- SAMPLES: PDFs reales de muestra que EXISTAN en el equipo, con sus montos
  esperados, para las pruebas de integración (se saltan si no están).
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def W(text, x0, top, ancho=30, alto=8):
    """Crea una palabra estilo pdfplumber con coordenadas."""
    return {
        "text": text,
        "x0": float(x0),
        "x1": float(x0 + ancho),
        "top": float(top),
        "bottom": float(top + alto),
    }


def tabla_sintetica(filas, x_monto=300, top_ini=25, paso=20):
    """
    Construye la lista de palabras de una tabla de detalle sintética.
    `filas` = lista de (texto_descripcion, texto_monto|None).
    Incluye la cabecera "Concepto"/"Total RD$" y la fila final "Total".
    """
    palabras = [W("Concepto", 10, 10), W("Total", x_monto, 10)]
    top = top_ini
    for desc, monto in filas:
        x = 12
        for tok in desc.split():
            palabras.append(W(tok, x, top))
            x += 45
        if monto is not None:
            palabras.append(W(monto, x_monto, top))
        top += paso
    # Fila de cierre de la tabla
    palabras.append(W("Total", 12, top + paso))
    palabras.append(W("en", 45, top + paso))
    palabras.append(W("RD$", 75, top + paso))
    palabras.append(W("0.00", x_monto, top + paso))
    return palabras


# ── PDFs reales de muestra (solo los que existan) ────────────────────────────
_CANDIDATOS = [
    {
        "path": r"C:\Users\giovy\Downloads\aes andres.pdf",
        "tipo": "factura",
        "montos": [4774623.0, 22789532.0, 4177489.0],
    },
    {
        "path": r"C:\Users\giovy\Downloads\Trabajar_ND_E31-E46\Nota Debitos\900001309.pdf",
        "tipo": "nota_debito",
        "montos": [175361.96],
    },
    {
        "path": r"C:\Users\giovy\Downloads\Trabajar_ND_E31-E46\Nota creditos\NC\800001189.pdf",
        "tipo": "nota_credito",
        "montos": [641754.12, 71282.28, 5124.53, 1708.18],
    },
]

SAMPLES = [c for c in _CANDIDATOS if os.path.exists(c["path"])]


def leer_pdf(ruta):
    """Extrae (texto_completo, palabras_con_offset) de un PDF real."""
    import pdfplumber

    textos, palabras, off = [], [], 0.0
    with pdfplumber.open(ruta) as pdf:
        for p in pdf.pages:
            textos.append(p.extract_text() or "")
            for w in p.extract_words():
                c = dict(w)
                c["top"] += off
                palabras.append(c)
            ws = p.extract_words()
            if ws:
                off += max(w["bottom"] for w in ws) + 10
    return "\n".join(textos), palabras
