# -*- coding: utf-8 -*-
"""Pruebas de processors/generador_excel.py"""

import os
import tempfile
import unicodedata
import unittest
from datetime import datetime

import _helpers  # noqa: F401  (inserta sys.path)
from openpyxl import load_workbook
from processors.generador_excel import (
    _es_columna_monetaria,
    _a_entero,
    _resolver_plantilla,
    generar_excel,
    FORMATO_NUM,
    FORMATO_NUM_PRECIO,
    PLANTILLAS,
    TIPO_POR_DEFECTO,
)


def _norm(s):
    """Normaliza texto para comparar sin distinguir tildes ni mayúsculas.
    (Las plantillas usan 'Número' en NC pero 'Numero' en ND/Factura.)"""
    if s is None:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(c) != "Mn"
    ).lower().strip()


def _doc(ncf="E330000000023", cantidad=3.0, monto=175361.96):
    return {
        "encabezado": {
            "ncf": ncf,
            "numero_documento": "900001309",
            "fecha_documento": datetime(2026, 6, 25),
            "fecha_vencimiento": None,
            "moneda": "DOP",
            "cliente": "EDE ESTE",
            "rnc_cliente": "101023122",
            "observaciones": None,
        },
        "detalle": [{
            "nombre": "RELIQ CONTRATO",
            "descripcion": None,
            "cantidad": cantidad,
            "unidad_medida": None,
            "monto": monto,
        }],
    }


class TestEsColumnaMonetaria(unittest.TestCase):
    def test_monetarias(self):
        for h in ["Precio Unitario Item", "Monto Item", "Valor Descuento", "Tasa Cambio"]:
            self.assertTrue(_es_columna_monetaria(h), h)

    def test_no_monetarias(self):
        for h in ["NCF", "Cliente", "Moneda", "Fecha del Documento", None, ""]:
            self.assertFalse(_es_columna_monetaria(h), repr(h))


class TestAEntero(unittest.TestCase):
    def test_convierte_digitos(self):
        self.assertEqual(_a_entero("123"), 123)
        self.assertEqual(_a_entero("0"), 0)

    def test_conserva_ceros_a_la_izquierda(self):
        # "007" no se debe volver 7 (cambiaría el dato); queda como texto.
        self.assertEqual(_a_entero("007"), "007")

    def test_no_numerico_intacto(self):
        self.assertEqual(_a_entero("A1B2"), "A1B2")
        self.assertEqual(_a_entero(None), None)
        self.assertEqual(_a_entero(55), 55)


class TestResolverPlantilla(unittest.TestCase):
    def test_tipos_conocidos(self):
        for tipo in ("factura", "nota_credito", "nota_debito"):
            cols, claves, d_map = _resolver_plantilla(tipo)
            self.assertTrue(cols and claves and d_map)

    def test_tipo_desconocido_cae_a_por_defecto(self):
        cols_def, _, _ = _resolver_plantilla(TIPO_POR_DEFECTO)
        cols_x, _, _ = _resolver_plantilla("no_existe")
        self.assertEqual(cols_x, cols_def)


class TestFormatoConstantes(unittest.TestCase):
    def test_valores(self):
        self.assertEqual(FORMATO_NUM, "#,##0.00")
        self.assertEqual(FORMATO_NUM_PRECIO, "#,##0.00####")


class TestGenerarExcel(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmp):
            os.remove(os.path.join(self.tmp, f))
        os.rmdir(self.tmp)

    def _generar(self, tipo, doc):
        out = os.path.join(self.tmp, f"{tipo}.xlsx")
        generar_excel([doc], out, tipo_documento=tipo)
        self.assertTrue(os.path.exists(out))
        return load_workbook(out)["Facturacion"]

    def test_estructura_basica(self):
        ws = self._generar("nota_debito", _doc())
        # Fila 3 = primera fila de datos (E); fila 4 = detalle (D)
        self.assertEqual(ws.cell(row=3, column=1).value, "E")
        self.assertEqual(ws.cell(row=4, column=1).value, "D")
        self.assertEqual(ws.freeze_panes, "A3")

    def test_numero_documento_es_entero(self):
        # En los 3 tipos, el "Numero Factura Interna" debe salir como entero.
        for tipo in ("factura", "nota_credito", "nota_debito"):
            ws = self._generar(tipo, _doc())
            col = next((c for c in range(1, ws.max_column + 1)
                        if _norm(ws.cell(row=1, column=c).value) == "numero factura interna"),
                       None)
            self.assertIsNotNone(col, f"{tipo}: falta columna Numero Factura Interna")
            val = ws.cell(row=3, column=col).value
            self.assertEqual(val, 900001309, tipo)
            self.assertIsInstance(val, int, tipo)

    def test_precio_unitario_formato_y_valor(self):
        for tipo in ("factura", "nota_credito", "nota_debito"):
            ws = self._generar(tipo, _doc())
            col = next((c for c in range(1, ws.max_column + 1)
                        if ws.cell(row=2, column=c).value == "Precio Unitario Item"), None)
            self.assertIsNotNone(col, f"{tipo}: falta columna Precio Unitario Item")
            celda = ws.cell(row=4, column=col)
            # Valor = monto / cantidad, con precisión completa (no redondeado)
            self.assertAlmostEqual(celda.value, 175361.96 / 3.0, places=6)
            # Formato de más decimales para no perder precisión
            self.assertEqual(celda.number_format, FORMATO_NUM_PRECIO)

    def test_tipo_none_infiere_del_documento(self):
        doc = _doc(ncf="E340000000001")  # NC
        doc["encabezado"]["tipo_documento"] = "nota_credito"
        out = os.path.join(self.tmp, "infer.xlsx")
        generar_excel([doc], out)  # sin tipo_documento explícito
        self.assertTrue(os.path.exists(out))


class TestRegistroCoincideConPlantillas(unittest.TestCase):
    def test_ids_reales_coinciden(self):
        # Los 3 tipos reales del registro deben existir como plantilla.
        from templates.registry import DOCUMENT_TYPES
        reales = [t for t in DOCUMENT_TYPES.values() if not t.reservado]
        for t in reales:
            self.assertIn(t.id, PLANTILLAS, f"{t.id} sin plantilla")


if __name__ == "__main__":
    unittest.main(verbosity=2)
