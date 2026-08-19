# -*- coding: utf-8 -*-
"""
run_tests.py — Ejecuta TODA la batería de pruebas.

Uso:
    python run_tests.py

Descubre y corre los tests de la carpeta tests/. Devuelve código de salida
0 si todo pasa, 1 si algo falla (útil para CI).
"""

import os
import sys
import unittest

# La consola de Windows (cp1252) no codifica algunos símbolos de los mensajes.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(ROOT, "tests")
sys.path.insert(0, ROOT)     # para 'import processors', 'import utils', …
sys.path.insert(0, TESTS)    # para 'import _helpers'


def main() -> int:
    suite = unittest.TestLoader().discover(start_dir=TESTS, top_level_dir=TESTS)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
