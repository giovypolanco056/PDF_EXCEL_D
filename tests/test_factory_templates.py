# -*- coding: utf-8 -*-
"""Pruebas de processors/factory.py y templates/registry.py"""

import unittest

import _helpers  # noqa: F401
from processors.factory import get_processor
from processors.nota_credito import (
    FacturaProcessor,
    NotaCreditoProcessor,
    NotaDebitoProcessor,
)
from templates.registry import get_type, all_types, DOCUMENT_TYPES


class TestGetProcessor(unittest.TestCase):
    def test_tipos_reales(self):
        self.assertIsInstance(get_processor("factura"), FacturaProcessor)
        self.assertIsInstance(get_processor("nota_credito"), NotaCreditoProcessor)
        self.assertIsInstance(get_processor("nota_debito"), NotaDebitoProcessor)

    def test_nombres_visibles(self):
        self.assertEqual(get_processor("factura").nombre, "Factura")
        self.assertEqual(get_processor("nota_credito").nombre, "Nota de Crédito")
        self.assertEqual(get_processor("nota_debito").nombre, "Nota de Débito")

    def test_tipo_reservado_error_claro(self):
        with self.assertRaises(ValueError) as ctx:
            get_processor("tipo4")
        self.assertIn("no está implementado", str(ctx.exception))

    def test_tipo_desconocido_error(self):
        with self.assertRaises(ValueError) as ctx:
            get_processor("no_existe_xyz")
        self.assertIn("desconocido", str(ctx.exception).lower())


class TestRegistry(unittest.TestCase):
    def test_get_type_conocido(self):
        t = get_type("factura")
        self.assertIsNotNone(t)
        self.assertEqual(t.id, "factura")
        self.assertEqual(t.sheet_name, "Facturacion")

    def test_get_type_desconocido(self):
        self.assertIsNone(get_type("no_existe"))

    def test_all_types_incluye_los_tres_reales(self):
        ids = {t.id for t in all_types() if not t.reservado}
        self.assertEqual(ids, {"factura", "nota_credito", "nota_debito"})

    def test_ids_coinciden_con_su_clave(self):
        for clave, t in DOCUMENT_TYPES.items():
            self.assertEqual(clave, t.id)

    def test_reservados_marcados(self):
        for clave in ("tipo4", "tipo5", "tipo6"):
            self.assertTrue(get_type(clave).reservado)


if __name__ == "__main__":
    unittest.main(verbosity=2)
