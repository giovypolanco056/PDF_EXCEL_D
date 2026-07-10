# -*- coding: utf-8 -*-
"""
probar_errores.py — Prueba de diagnóstico de PDFs

Analiza uno o varios PDF (o carpetas) y reporta, por cada documento, qué
problemas tiene (campos que no se pudieron extraer, sin detalle, total que no
cuadra, etc.) SIN generar el Excel. Útil para revisar un lote antes de
procesarlo y saber exactamente qué falla en cada uno.

Uso:
    python probar_errores.py                      # revisa la carpeta actual
    python probar_errores.py "C:\\ruta\\Facturas"
    python probar_errores.py factura1.pdf factura2.pdf
"""

import sys
from pathlib import Path

# La consola de Windows suele ser cp1252 y no codifica ✓/✗/⚠. Forzar UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pdfplumber

from processors.extractor_encabezado import extraer_encabezado, NOMBRES_TIPO
from processors.extractor_detalle import extraer_detalle
from processors.diagnostico import diagnosticar
from utils.files import collect_pdfs, validate_pdf


def _analizar(ruta: Path):
    """Extrae encabezado y detalle de un PDF. Devuelve (enc, det)."""
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
    enc = extraer_encabezado("\n".join(textos))
    det = extraer_detalle(palabras, numero_documento=enc.get("numero_documento"))
    return enc, det


def main(argv: list[str]) -> int:
    rutas = argv or ["."]
    pdfs = collect_pdfs(rutas)

    if not pdfs:
        print("No se encontraron PDFs en:", ", ".join(rutas))
        return 1

    print(f"Analizando {len(pdfs)} PDF(s)…\n")
    n_ok = n_adv = n_err = 0

    for pdf in pdfs:
        ok, err = validate_pdf(pdf)
        if not ok:
            print(f"✗ {pdf.name}: NO es un PDF válido — {err}")
            n_err += 1
            continue

        try:
            enc, det = _analizar(pdf)
        except Exception as exc:                       # noqa: BLE001
            print(f"✗ {pdf.name}: error al leer — {exc}")
            n_err += 1
            continue

        problemas = diagnosticar(enc, det)
        tipo = NOMBRES_TIPO.get(enc.get("tipo_documento"), enc.get("tipo_documento") or "?")
        ncf = enc.get("ncf") or "sin NCF"

        if not problemas:
            print(f"✓ {pdf.name}  [{tipo} · {ncf}]  — OK ({len(det)} líneas)")
            n_ok += 1
            continue

        hay_error = any(sev == "error" for sev, _ in problemas)
        icono = "✗" if hay_error else "⚠"
        if hay_error:
            n_err += 1
        else:
            n_adv += 1
        print(f"{icono} {pdf.name}  [{tipo} · {ncf}]")
        for sev, msg in problemas:
            print(f"      {'✗' if sev == 'error' else '⚠'} {msg}")

    print("\n" + "─" * 50)
    print(f"Resumen:  {n_ok} OK   |   {n_adv} con advertencias   |   {n_err} con errores")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
