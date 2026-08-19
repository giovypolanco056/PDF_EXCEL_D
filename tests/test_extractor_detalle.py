# -*- coding: utf-8 -*-
"""Pruebas de processors/extractor_detalle.py"""

import unittest

from _helpers import W, tabla_sintetica  # noqa: E402  (inserta sys.path)
from processors.extractor_detalle import (
    _es_monto,
    _convertir_monto,
    _parsear_descripcion,
    _agrupar_por_linea,
    extraer_detalle,
)


class TestEsMonto(unittest.TestCase):
    def test_acepta_formatos_validos(self):
        for s in ["1708.18", "22,789,532.00", "-5,124.53", "1,708.1835",
                  "0.00", "1.5", "4,774,623", "(5,124.53)"]:
            self.assertTrue(_es_monto(s), f"debería aceptar {s!r}")

    def test_conserva_mas_de_dos_decimales(self):
        # El bug corregido: antes \d{1,2} rechazaba esto.
        self.assertTrue(_es_monto("1,708.1835"))
        self.assertTrue(_es_monto("2.44105"))

    def test_entero_con_separador_de_miles_es_monto(self):
        # Bug: '4,774,623' (sin decimales) antes se descartaba.
        self.assertTrue(_es_monto("4,774,623"))

    def test_rechaza_anios_y_enteros_pelados(self):
        # Un año o un entero sin separador ni decimales NO es monto.
        for s in ["2025", "2026", "1", "4774623", "abc", "", "kWh", ".", "12."]:
            self.assertFalse(_es_monto(s), f"NO debería aceptar {s!r}")


class TestConvertirMonto(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(_convertir_monto("131,453.24"), 131453.24)
        self.assertEqual(_convertir_monto("-5,124.53"), -5124.53)
        self.assertEqual(_convertir_monto("1,708.1835"), 1708.1835)

    def test_entero_con_separador(self):
        self.assertEqual(_convertir_monto("4,774,623"), 4774623.0)

    def test_negativo_contable(self):
        # "(5,124.53)" (paréntesis) = negativo.
        self.assertEqual(_convertir_monto("(5,124.53)"), -5124.53)

    def test_invalido_devuelve_none(self):
        self.assertIsNone(_convertir_monto("abc"))
        self.assertIsNone(_convertir_monto(""))


class TestParsearDescripcion(unittest.TestCase):
    def test_nombre_cantidad_unidad(self):
        self.assertEqual(_parsear_descripcion("ENERGIA 1 kWh"), ("ENERGIA", 1.0, "kWh"))
        self.assertEqual(_parsear_descripcion("POTENCIA 2 kW"), ("POTENCIA", 2.0, "kW"))

    def test_cantidad_decimal(self):
        nombre, cant, uni = _parsear_descripcion("ENERGIA 1.5 kWh")
        self.assertEqual((nombre, cant, uni), ("ENERGIA", 1.5, "kWh"))

    def test_anio_no_es_unidad(self):
        # "2025" NO es unidad → no se debe partir el nombre.
        self.assertEqual(
            _parsear_descripcion("RELIQ CONTRATO DC 2025"),
            ("RELIQ CONTRATO DC 2025", 1.0, None),
        )

    def test_sin_cantidad(self):
        self.assertEqual(
            _parsear_descripcion("SERVICIO GENERAL"),
            ("SERVICIO GENERAL", 1.0, None),
        )


class TestAgruparPorLinea(unittest.TestCase):
    def test_agrupa_por_top(self):
        palabras = [W("a", 10, 100), W("b", 40, 101), W("c", 10, 130)]
        lineas = _agrupar_por_linea(palabras, tolerancia=2.0)
        self.assertEqual(len(lineas), 2)

    def test_separa_lineas_lejanas(self):
        palabras = [W("a", 10, 100), W("b", 10, 110)]
        self.assertEqual(len(_agrupar_por_linea(palabras, tolerancia=2.0)), 2)


class TestExtraerDetalle(unittest.TestCase):
    def test_extraccion_basica(self):
        palabras = tabla_sintetica([("ENERGIA 1 kWh", "4,774,623.00")])
        det = extraer_detalle(palabras)
        self.assertEqual(len(det), 1)
        self.assertEqual(det[0]["monto"], 4774623.0)
        self.assertEqual(det[0]["cantidad"], 1.0)
        self.assertEqual(det[0]["unidad_medida"], "kWh")

    def test_preserva_decimales_completos(self):
        # Regresión del bug de precisión: 4 decimales deben conservarse.
        palabras = tabla_sintetica([("TARIFA ESPECIAL", "1,708.1835")])
        det = extraer_detalle(palabras)
        self.assertEqual(len(det), 1)
        self.assertEqual(det[0]["monto"], 1708.1835)

    def test_guarda_cantidad_con_unidad_no_es_monto(self):
        # "2.44105 MW" es una cantidad, NO un importe: no debe leerse como monto.
        palabras = tabla_sintetica([("Potencia Reliquidada: 2.44105 MW", None)])
        det = extraer_detalle(palabras)
        # La línea no tiene importe → se descarta.
        self.assertEqual(det, [])

    def test_sin_cabecera_concepto_devuelve_vacio(self):
        palabras = [W("Cualquier", 10, 10), W("cosa", 40, 10), W("100.00", 300, 10)]
        self.assertEqual(extraer_detalle(palabras), [])

    def test_independiente_de_la_posicion(self):
        # Mismo dato, columna de monto MUY a la izquierda: debe extraerse igual.
        a = tabla_sintetica([("ENERGIA 1 kWh", "4,774,623.00")], x_monto=300)
        b = tabla_sintetica([("ENERGIA 1 kWh", "4,774,623.00")], x_monto=120)
        self.assertEqual(extraer_detalle(a)[0]["monto"], extraer_detalle(b)[0]["monto"])

    def test_varias_lineas(self):
        palabras = tabla_sintetica([
            ("ENERGIA 1 kWh", "4,774,623.00"),
            ("POTENCIA 1 kW", "22,789,532.00"),
        ])
        det = extraer_detalle(palabras)
        self.assertEqual([d["monto"] for d in det], [4774623.0, 22789532.0])

    def test_numero_documento_se_propaga(self):
        palabras = tabla_sintetica([("ENERGIA 1 kWh", "4,774,623.00")])
        det = extraer_detalle(palabras, numero_documento="600004598")
        self.assertEqual(det[0]["numero_documento"], "600004598")

    def test_concepto_con_palabra_total_no_corta_la_tabla(self):
        # Regresión (bug crítico): un concepto que contenga "Total" en medio
        # NO debe terminar la tabla y perder las líneas siguientes.
        palabras = tabla_sintetica([
            ("ENERGIA 1 kWh", "4,774,623.00"),
            ("AJUSTE Total ENERGIA", "1,000,000.00"),
            ("POTENCIA 1 kW", "22,789,532.00"),
        ])
        det = extraer_detalle(palabras)
        self.assertEqual(len(det), 3)
        self.assertEqual(sum(d["monto"] for d in det), 28564155.00)

    def test_monto_entero_con_separador(self):
        # Regresión: '4,774,623' (sin decimales) debe extraerse.
        palabras = tabla_sintetica([("ENERGIA 1 kWh", "4,774,623")])
        det = extraer_detalle(palabras)
        self.assertEqual(det[0]["monto"], 4774623.0)

    def test_monto_negativo_contable(self):
        # Regresión: '(5,124.53)' (paréntesis) = -5124.53
        palabras = tabla_sintetica([("DEVOLUCION SERVICIO", "(5,124.53)")])
        det = extraer_detalle(palabras)
        self.assertEqual(det[0]["monto"], -5124.53)


if __name__ == "__main__":
    unittest.main(verbosity=2)
