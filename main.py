# -*- coding: utf-8 -*-
"""
main.py — Punto de entrada de la aplicación PDF → Excel
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz de la app esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
