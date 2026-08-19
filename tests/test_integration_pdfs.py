# -*- coding: utf-8 -*-
"""
Pruebas de integración de extremo a extremo con PDFs REALES.

Se ejecutan solo si los PDFs de muestra existen en el equipo (ver _helpers.
SAMPLES); en otro caso se saltan automáticamente, sin fallar.
"""

import os
import tempfile
import unittest
from pathlib import Path

from _helpers import SAMPLES, leer_pdf
from openpyxl import load_workbook
from processors.factory import get_processor
from processors.extractor_encabezado import extraer_encabezado
from processors.extractor_detalle import extraer_detalle
from processors.engine import _process


@unittest.skipUnless(SAMPLES, "No hay PDFs de muestra en este equipo")
class TestPdfsReales(unittest.TestCase):

    def test_montos_esperados(self):
        for s in SAMPLES:
            with self.subTest(pdf=os.path.basename(s["path"])):
                texto, palabras = leer_pdf(s["path"])
                enc = extraer_encabezado(texto)
                det = extraer_detalle(palabras, numero_documento=enc.get("numero_documento"))
                montos = [l["monto"] for l in det]
                self.assertEqual(montos, s["montos"])

    def test_tipo_detectado(self):
        for s in SAMPLES:
            with self.subTest(pdf=os.path.basename(s["path"])):
                texto, _ = leer_pdf(s["path"])
                enc = extraer_encabezado(texto)
                self.assertEqual(enc["tipo_documento"], s["tipo"])

    def test_procesar_pdf_completo(self):
        for s in SAMPLES:
            with self.subTest(pdf=os.path.basename(s["path"])):
                proc = get_processor(s["tipo"])
                doc = proc.procesar_pdf(Path(s["path"]))
                self.assertIn("encabezado", doc)
                self.assertIn("detalle", doc)
                self.assertIn("problemas", doc)
                self.assertTrue(len(doc["detalle"]) >= 1)

    def test_pipeline_genera_excel_valido(self):
        for s in SAMPLES:
            with self.subTest(pdf=os.path.basename(s["path"])):
                with tempfile.TemporaryDirectory() as tmp:
                    res = _process(
                        s["tipo"], [s["path"]], tmp,
                        lambda a, b, c: None,      # on_progress
                        lambda n, i, f: False,     # on_duplicate
                    )
                    self.assertEqual(res.exitosos, 1)
                    self.assertEqual(res.fallidos, 0)
                    self.assertTrue(res.excel_path and Path(res.excel_path).exists())
                    ws = load_workbook(res.excel_path)["Facturacion"]
                    # Debe haber al menos una fila E y una D
                    col1 = [ws.cell(row=r, column=1).value for r in range(3, ws.max_row + 1)]
                    self.assertIn("E", col1)
                    self.assertIn("D", col1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
