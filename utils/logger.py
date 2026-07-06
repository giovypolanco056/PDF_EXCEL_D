# -*- coding: utf-8 -*-
"""
utils/logger.py — Configuración centralizada de logs
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def get_logger(name: str = "pdf2excel") -> logging.Logger:
    """Devuelve (o crea) el logger de la aplicación."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # ya configurado

    logger.setLevel(logging.DEBUG)
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Archivo rotativo diario
    log_file = _LOG_DIR / f"{datetime.now():%Y-%m-%d}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    ))

    # Consola (solo WARNING+)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
