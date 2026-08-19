# -*- coding: utf-8 -*-
"""Pruebas de processors/engine.py (clave de duplicados)"""

import unittest
from datetime import datetime

import _helpers  # noqa: F401
from processors.engine import _clave_duplicado, ProcessResult


class TestClaveDuplicado(unittest.TestCase):
    def test_mismo_ncf_misma_clave(self):
        a = {"ncf": "E330000000023", "numero_documento": "1", "fecha_documento": None}
        b = {"ncf": "E330000000023", "numero_documento": "999", "fecha_documento": None}
        self.assertEqual(_clave_duplicado(a), _clave_duplicado(b))

    def test_ncf_insensible_a_mayusculas(self):
        a = {"ncf": "E330000000023"}
        b = {"ncf": "e330000000023"}
        self.assertEqual(_clave_duplicado(a), _clave_duplicado(b))

    def test_ncf_distinto_clave_distinta(self):
        a = {"ncf": "E330000000023"}
        b = {"ncf": "E330000000024"}
        self.assertNotEqual(_clave_duplicado(a), _clave_duplicado(b))

    def test_sin_ncf_usa_numero_y_fecha(self):
        a = {"ncf": None, "numero_documento": "600004640",
             "fecha_documento": datetime(2026, 6, 25)}
        clave = _clave_duplicado(a)
        self.assertIn("600004640", clave)
        self.assertIn("2026-06-25", clave)

    def test_sin_ncf_numeros_distintos_no_colisionan(self):
        a = {"ncf": None, "numero_documento": "1", "fecha_documento": None}
        b = {"ncf": None, "numero_documento": "2", "fecha_documento": None}
        self.assertNotEqual(_clave_duplicado(a), _clave_duplicado(b))

    def test_con_ncf_ignora_numero_y_fecha(self):
        # Con NCF presente, num/fecha no deben influir en la clave.
        a = {"ncf": "E31", "numero_documento": "1", "fecha_documento": datetime(2026, 1, 1)}
        b = {"ncf": "E31", "numero_documento": "2", "fecha_documento": datetime(2020, 5, 5)}
        self.assertEqual(_clave_duplicado(a), _clave_duplicado(b))


class TestProcessResultDefaults(unittest.TestCase):
    def test_valores_iniciales(self):
        r = ProcessResult()
        self.assertEqual((r.total, r.exitosos, r.omitidos, r.fallidos), (0, 0, 0, 0))
        self.assertEqual(r.documentos, [])
        self.assertEqual(r.advertencias, [])
        self.assertEqual(r.errores, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
