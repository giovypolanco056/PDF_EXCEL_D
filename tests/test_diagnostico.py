# -*- coding: utf-8 -*-
"""Pruebas de processors/diagnostico.py"""

import unittest
from datetime import datetime

import _helpers  # noqa: F401
from processors.diagnostico import diagnosticar, resumir


def _enc_completo():
    return {
        "ncf": "E310000000347",
        "numero_documento": "600004598",
        "fecha_documento": datetime(2026, 6, 30),
        "rnc_cliente": "101023122",
        "cliente": "EDE ESTE",
        "total": 100.0,
    }


def _severidades(problemas):
    return {sev for sev, _ in problemas}


def _mensajes(problemas):
    return " | ".join(m for _, m in problemas)


class TestDiagnosticar(unittest.TestCase):
    def test_documento_completo_sin_problemas(self):
        self.assertEqual(diagnosticar(_enc_completo(), [{"monto": 100.0}]), [])

    def test_ncf_ausente_es_error(self):
        enc = _enc_completo()
        enc["ncf"] = None
        problemas = diagnosticar(enc, [{"monto": 100.0}])
        self.assertIn("error", _severidades(problemas))
        self.assertIn("NCF", _mensajes(problemas))

    def test_numero_ausente_es_error(self):
        enc = _enc_completo()
        enc["numero_documento"] = None
        self.assertIn("error", _severidades(diagnosticar(enc, [{"monto": 100.0}])))

    def test_campos_opcionales_son_advertencia(self):
        enc = _enc_completo()
        enc["rnc_cliente"] = None
        enc["cliente"] = None
        enc["fecha_documento"] = None
        problemas = diagnosticar(enc, [{"monto": 100.0}])
        self.assertEqual(_severidades(problemas), {"advertencia"})

    def test_sin_detalle_es_error(self):
        problemas = diagnosticar(_enc_completo(), [])
        self.assertIn("error", _severidades(problemas))
        self.assertIn("detalle", _mensajes(problemas).lower())

    def test_lineas_sin_monto_es_advertencia(self):
        problemas = diagnosticar(_enc_completo(), [{"monto": 100.0}, {"monto": None}])
        self.assertIn("advertencia", _severidades(problemas))
        self.assertIn("sin monto", _mensajes(problemas).lower())

    def test_total_no_cuadra(self):
        enc = _enc_completo()
        enc["total"] = 1000.0
        problemas = diagnosticar(enc, [{"monto": 400.0}])
        self.assertIn("advertencia", _severidades(problemas))
        self.assertIn("cuadra", _mensajes(problemas).lower())

    def test_total_ausente_es_advertencia(self):
        enc = _enc_completo()
        enc["total"] = None
        problemas = diagnosticar(enc, [{"monto": 100.0}])
        self.assertIn("advertencia", _severidades(problemas))


class TestResumir(unittest.TestCase):
    def test_none_si_limpio(self):
        self.assertIsNone(resumir(_enc_completo(), [{"monto": 100.0}]))

    def test_texto_si_hay_problemas(self):
        enc = _enc_completo()
        enc["ncf"] = None
        self.assertIsInstance(resumir(enc, [{"monto": 100.0}]), str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
