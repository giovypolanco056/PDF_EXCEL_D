# -*- coding: utf-8 -*-
"""Pruebas de utils/files.py"""

import os
import tempfile
import unittest
from pathlib import Path

import _helpers  # noqa: F401
from utils.files import collect_pdfs, validate_pdf, safe_output_path

_PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF\n"


def _crear_pdf(ruta: Path):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(_PDF_BYTES)


class TestValidatePdf(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        for f in self.tmp.rglob("*"):
            if f.is_file():
                f.unlink()
        # limpiar subdirectorios
        for d in sorted(self.tmp.rglob("*"), reverse=True):
            if d.is_dir():
                d.rmdir()
        self.tmp.rmdir()

    def test_no_existe(self):
        ok, msg = validate_pdf(self.tmp / "nope.pdf")
        self.assertFalse(ok)
        self.assertIn("no existe", msg.lower())

    def test_vacio(self):
        p = self.tmp / "vacio.pdf"
        p.write_bytes(b"")
        ok, msg = validate_pdf(p)
        self.assertFalse(ok)
        self.assertIn("vac", msg.lower())

    def test_no_es_pdf(self):
        p = self.tmp / "falso.pdf"
        p.write_bytes(b"esto no es un pdf")
        ok, _ = validate_pdf(p)
        self.assertFalse(ok)

    def test_pdf_valido(self):
        p = self.tmp / "bueno.pdf"
        _crear_pdf(p)
        ok, msg = validate_pdf(p)
        self.assertTrue(ok)
        self.assertEqual(msg, "")


class TestCollectPdfs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        for f in sorted(self.tmp.rglob("*"), reverse=True):
            if f.is_file():
                f.unlink()
            else:
                f.rmdir()
        self.tmp.rmdir()

    def test_recursivo_y_case_insensitive(self):
        _crear_pdf(self.tmp / "a.pdf")
        _crear_pdf(self.tmp / "sub" / "b.PDF")   # subcarpeta + mayúsculas
        encontrados = collect_pdfs([str(self.tmp)])
        nombres = {p.name for p in encontrados}
        self.assertEqual(nombres, {"a.pdf", "b.PDF"})

    def test_dedup(self):
        p = self.tmp / "a.pdf"
        _crear_pdf(p)
        self.assertEqual(len(collect_pdfs([str(p), str(p)])), 1)

    def test_archivo_sin_extension_por_contenido(self):
        # Archivo pasado directamente, sin extensión .pdf pero con firma %PDF-.
        p = self.tmp / "documento_sin_ext"
        _crear_pdf(p)
        encontrados = collect_pdfs([str(p)])
        self.assertEqual(len(encontrados), 1)

    def test_no_pdf_se_ignora(self):
        p = self.tmp / "nota.txt"
        p.write_text("hola")
        self.assertEqual(collect_pdfs([str(p)]), [])

    def test_ordenado(self):
        for n in ["c.pdf", "a.pdf", "b.pdf"]:
            _crear_pdf(self.tmp / n)
        nombres = [p.name for p in collect_pdfs([str(self.tmp)])]
        self.assertEqual(nombres, sorted(nombres))


class TestSafeOutputPath(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        for f in self.tmp.rglob("*"):
            if f.is_file():
                f.unlink()
        self.tmp.rmdir()

    def test_no_colisiona(self):
        primero = safe_output_path(self.tmp, "salida.xlsx")
        self.assertEqual(primero.name, "salida.xlsx")

    def test_evita_sobreescritura(self):
        (self.tmp / "salida.xlsx").write_text("x")
        segundo = safe_output_path(self.tmp, "salida.xlsx")
        self.assertEqual(segundo.name, "salida_1.xlsx")


if __name__ == "__main__":
    unittest.main(verbosity=2)
