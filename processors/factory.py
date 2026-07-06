# -*- coding: utf-8 -*-
"""
processors/factory.py

Fábrica de procesadores.
Devuelve el procesador correcto dado un tipo de documento.
Para agregar un nuevo tipo: importar la clase e incluirla en _MAP.
"""

from processors.base import BaseProcessor
from processors.nota_credito import (
    FacturaProcessor,
    NotaCreditoProcessor,
    NotaDebitoProcessor,
)
from templates.registry import get_type

_MAP: dict[str, type[BaseProcessor]] = {
    "factura":      FacturaProcessor,
    "nota_credito": NotaCreditoProcessor,
    "nota_debito":  NotaDebitoProcessor,
}


def get_processor(type_id: str) -> BaseProcessor:
    cls = _MAP.get(type_id)
    if cls is None:
        # Tipos reservados (aún sin implementar): mensaje claro para el usuario
        # en vez de generar silenciosamente un Excel con la plantilla equivocada.
        doc_type = get_type(type_id)
        if doc_type is not None and doc_type.reservado:
            raise ValueError(
                f"El tipo «{doc_type.label}» todavía no está implementado. "
                f"Selecciona Factura, Nota de Crédito o Nota de Débito."
            )
        raise ValueError(f"Tipo de documento desconocido: '{type_id}'")
    return cls()
