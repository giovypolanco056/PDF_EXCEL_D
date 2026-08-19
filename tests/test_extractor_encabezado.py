# -*- coding: utf-8 -*-
"""Pruebas de processors/extractor_encabezado.py"""

import unittest
from datetime import datetime

import _helpers  # noqa: F401  (inserta sys.path)
from processors.extractor_encabezado import (
    detectar_moneda,
    _convertir_fecha,
    _convertir_monto,
    detectar_tipo_documento,
    extraer_observaciones,
    extraer_encabezado,
)


class TestDetectarMoneda(unittest.TestCase):
    def test_pesos_por_defecto(self):
        self.assertEqual(detectar_moneda("Total en RD$ 1,000.00"), "DOP")
        self.assertEqual(detectar_moneda("Total en DOP 1,000.00"), "DOP")

    def test_dolares(self):
        self.assertEqual(detectar_moneda("Total en USD 1,000.00"), "USD")

    def test_euros(self):
        self.assertEqual(detectar_moneda("Total en EUR 1,000.00"), "EUR")

    def test_mencion_suelta_no_cambia_moneda(self):
        # "USD"/"dólares" en observaciones NO debe marcar USD si el total es RD$.
        texto = "Observaciones: pago en dólares USD equivalente\nTotal en RD$ 1,000.00"
        self.assertEqual(detectar_moneda(texto), "DOP")

    def test_sin_total_asume_dop(self):
        self.assertEqual(detectar_moneda("documento sin total"), "DOP")


class TestConvertirFecha(unittest.TestCase):
    def test_formatos_validos(self):
        self.assertEqual(_convertir_fecha("30.06.2026"), datetime(2026, 6, 30))
        self.assertEqual(_convertir_fecha("30/06/2026"), datetime(2026, 6, 30))
        self.assertEqual(_convertir_fecha("30-06-2026"), datetime(2026, 6, 30))

    def test_sin_cero_inicial(self):
        self.assertEqual(_convertir_fecha("2.6.2026"), datetime(2026, 6, 2))

    def test_invalida_devuelve_none(self):
        self.assertIsNone(_convertir_fecha("31.13.2026"))  # mes 13 no existe
        self.assertIsNone(_convertir_fecha("no es fecha"))
        self.assertIsNone(_convertir_fecha(None))


class TestConvertirMontoEncabezado(unittest.TestCase):
    def test_formato_normal(self):
        self.assertEqual(_convertir_monto("1,234.56"), 1234.56)
        self.assertEqual(_convertir_monto("31,741,644.00"), 31741644.0)

    def test_formato_europeo(self):
        self.assertEqual(_convertir_monto("166.881,78"), 166881.78)

    def test_invalido(self):
        self.assertIsNone(_convertir_monto("abc"))
        self.assertIsNone(_convertir_monto(None))


class TestDetectarTipoDocumento(unittest.TestCase):
    def test_por_prefijo_ncf(self):
        self.assertEqual(detectar_tipo_documento("", "E340000000001"), "nota_credito")
        self.assertEqual(detectar_tipo_documento("", "E330000000001"), "nota_debito")
        self.assertEqual(detectar_tipo_documento("", "E310000000001"), "factura")
        self.assertEqual(detectar_tipo_documento("", "E450000000001"), "factura")

    def test_prefijo_insensible_a_mayusculas(self):
        self.assertEqual(detectar_tipo_documento("", "e340000000001"), "nota_credito")

    def test_respaldo_por_titulo(self):
        # NCF con prefijo desconocido → usar el título visible.
        self.assertEqual(
            detectar_tipo_documento("NOTA DE CREDITO No. 1", "Z990000000001"),
            "nota_credito",
        )
        self.assertEqual(
            detectar_tipo_documento("NOTA DE DEBITO No. 1", None), "nota_debito"
        )

    def test_desconocido(self):
        self.assertEqual(detectar_tipo_documento("texto cualquiera", None), "desconocido")


class TestExtraerObservaciones(unittest.TestCase):
    def test_extrae_bloque(self):
        texto = "OBSERVACIONES : Pago del mes de junio\nElaborado Por"
        self.assertEqual(extraer_observaciones(texto), "Pago del mes de junio")

    def test_sin_observaciones(self):
        self.assertIsNone(extraer_observaciones("documento sin ese bloque"))


class TestExtraerEncabezadoIntegracion(unittest.TestCase):
    TEXTO = (
        "FACT. CREDITO FISCAL\n"
        "NCF : E310000000347\n"
        "Factura No. : 600004598\n"
        "Fecha de Factura : 30.06.2026\n"
        "Fecha Vcto. Factura : 30.07.2026\n"
        "RNC : 101023122\n"
        "Cliente : EDE ESTE\n"
        "Total en RD$ 31,741,644.00\n"
        "OBSERVACIONES : Pago del mes de junio\n"
        "Elaborado Por\n"
    )

    def setUp(self):
        self.enc = extraer_encabezado(self.TEXTO)

    def test_campos_basicos(self):
        self.assertEqual(self.enc["ncf"], "E310000000347")
        self.assertEqual(self.enc["numero_documento"], "600004598")
        self.assertEqual(self.enc["rnc_cliente"], "101023122")
        self.assertEqual(self.enc["cliente"], "EDE ESTE")

    def test_fechas_convertidas(self):
        self.assertEqual(self.enc["fecha_documento"], datetime(2026, 6, 30))
        self.assertEqual(self.enc["fecha_vencimiento"], datetime(2026, 7, 30))

    def test_total_y_moneda(self):
        self.assertEqual(self.enc["total"], 31741644.0)
        self.assertEqual(self.enc["moneda"], "DOP")

    def test_tipo_y_observaciones(self):
        self.assertEqual(self.enc["tipo_documento"], "factura")
        self.assertEqual(self.enc["observaciones"], "Pago del mes de junio")

    def test_campos_ausentes_son_none(self):
        # Un texto sin etiquetas no debe romper: todo None, sin excepción.
        vacio = extraer_encabezado("documento sin etiquetas conocidas")
        self.assertIsNone(vacio["ncf"])
        self.assertIsNone(vacio["total"])
        self.assertEqual(vacio["tipo_documento"], "desconocido")


if __name__ == "__main__":
    unittest.main(verbosity=2)
