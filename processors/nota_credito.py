# -*- coding: utf-8 -*-
"""
processors/nota_credito.py

Procesador para Notas de Crédito / Notas de Débito / Facturas EGEHID.
Envuelve la lógica existente en extractor_encabezado.py,
extractor_detalle.py y generador_excel.py.
"""

from typing import Optional

from processors.base import BaseProcessor
from processors.extractor_encabezado import extraer_encabezado
from processors.extractor_detalle import extraer_detalle
from processors.generador_excel import generar_excel


class NotaCreditoProcessor(BaseProcessor):
    nombre = "Nota de Crédito"

    def extraer_encabezado(self, texto: str) -> dict:
        return extraer_encabezado(texto)

    def extraer_detalle(self, palabras: list, numero_documento: Optional[str] = None) -> list:
        return extraer_detalle(palabras, numero_documento=numero_documento)

    def generar_excel(
        self, documentos: list, ruta_salida: str, tipo_documento: Optional[str] = None
    ) -> None:
        generar_excel(documentos, ruta_salida, tipo_documento=tipo_documento)


class FacturaProcessor(NotaCreditoProcessor):
    """Factura usa la misma lógica que Nota de Crédito por ahora.
    Separar cuando el formato de extracción difiera."""
    nombre = "Factura"


class NotaDebitoProcessor(NotaCreditoProcessor):
    """Nota de Débito usa la misma lógica de extracción que Nota de
    Crédito (extractor_encabezado.py ya detecta y diferencia el tipo
    por el prefijo del NCF / título del PDF). generador_excel.py
    selecciona automáticamente la plantilla de 36 columnas porque lee
    encabezado["tipo_documento"] == "nota_debito"."""
    nombre = "Nota de Débito"
