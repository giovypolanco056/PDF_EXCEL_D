# -*- mode: python ; coding: utf-8 -*-
"""
pdf2excel.spec — Archivo de empaquetado PyInstaller

Uso:
    pip install pyinstaller
    pyinstaller pdf2excel.spec

El ejecutable queda en dist/PDF2Excel/PDF2Excel.exe
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Incluir carpetas necesarias en el bundle
        (str(ROOT / "templates"),   "templates"),
        (str(ROOT / "processors"),  "processors"),
        (str(ROOT / "ui"),          "ui"),
        (str(ROOT / "utils"),       "utils"),
    ],
    hiddenimports=[
        "pdfplumber",
        "openpyxl",
        "openpyxl.styles",
        "openpyxl.utils",
        "pdfminer",
        "pdfminer.high_level",
        "pdfminer.layout",
        "PIL",
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas", "scipy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PDF2Excel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Sin ventana de consola en Windows
    icon=str(ROOT / "assets" / "icon.ico") if (ROOT / "assets" / "icon.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PDF2Excel",
)
