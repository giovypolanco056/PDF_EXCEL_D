# -*- coding: utf-8 -*-
"""
utils/files.py — Helpers de archivos y validación de PDFs
"""

from pathlib import Path
from typing import Optional
import os

from utils.logger import get_logger

log = get_logger()


def _es_pdf_por_contenido(path: Path) -> bool:
    """True si el archivo empieza con la firma %PDF-, sin importar su
    extensión (permite aceptar PDFs mal nombrados o sin extensión)."""
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def collect_pdfs(paths: list[str]) -> list[Path]:
    """
    Recibe una lista de rutas (archivos o carpetas) y devuelve todos los
    PDF encontrados, sin duplicados y ordenados.

    Robusto ante formato y posición:
      - Carpetas: se recorren de forma RECURSIVA (rglob), así que los PDF
        se encuentran aunque estén en subcarpetas.
      - Extensión sin importar mayúsculas/minúsculas (.pdf, .PDF, .Pdf…).
      - Archivos seleccionados directamente: se aceptan aunque no tengan
        extensión .pdf, si su contenido es realmente un PDF (firma %PDF-).
    """
    found: set[Path] = set()
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() == ".pdf":
                    found.add(f)
        elif p.is_file():
            if p.suffix.lower() == ".pdf" or _es_pdf_por_contenido(p):
                found.add(p)
    return sorted(found)


def validate_pdf(path: Path) -> tuple[bool, str]:
    """
    Validación básica de un PDF sin abrirlo completamente.
    Devuelve (ok, mensaje_error).
    """
    if not path.exists():
        return False, "El archivo no existe"
    if path.stat().st_size == 0:
        return False, "El archivo está vacío"
    try:
        with open(path, "rb") as f:
            header = f.read(5)
        if header != b"%PDF-":
            return False, "No es un archivo PDF válido"
    except OSError as e:
        return False, f"No se puede leer el archivo: {e}"
    return True, ""


def safe_output_path(base_dir: Path, filename: str) -> Path:
    """
    Devuelve una ruta de salida que no sobreescriba archivos existentes.
    Agrega _1, _2, ... si ya existe.
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    candidate = base_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = base_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def open_path(path: Path) -> None:
    """Abre un archivo o carpeta con la aplicación predeterminada del SO."""
    import subprocess, sys
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        # No romper la UI si el SO no puede abrir la ruta, pero dejar rastro:
        # sin esto, el usuario hace clic y "no pasa nada" sin explicación.
        log.warning("No se pudo abrir la ruta %s", path, exc_info=True)
