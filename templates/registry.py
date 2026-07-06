# -*- coding: utf-8 -*-
"""
templates/registry.py

Registro central de tipos de documento.
Para agregar un nuevo tipo: añadir una entrada al diccionario DOCUMENT_TYPES.
No es necesario modificar ningún otro archivo.

IMPORTANTE: el campo `id` debe coincidir exactamente con las claves usadas
en generador_excel.py → PLANTILLAS = {"nota_credito", "nota_debito", "factura"},
ya que ese valor es el que se pasa como `tipo_documento` al generar el Excel.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentType:
    id: str                        # Identificador interno único
    label: str                     # Nombre visible en la UI
    icon: str                      # Emoji / ícono decorativo
    description: str               # Descripción breve
    excel_filename: str            # Nombre base del Excel de salida
    sheet_name: str = "Facturacion"
    color: str = "#2563EB"         # Color de acento en la UI
    reservado: bool = False        # True = espacio reservado, aún sin implementar


# ── Registro de tipos ─────────────────────────────────────────────────────────
# Los 3 tipos corresponden 1:1 con las plantillas definidas en
# generador_excel.py (COLS_FACTURA, COLS_NOTA_CREDITO, COLS_NOTA_DEBITO).
DOCUMENT_TYPES: dict[str, DocumentType] = {
    "factura": DocumentType(
        id="factura",
        label="Factura",
        icon="🧾",
        description="Facturas comerciales EGEHID",
        excel_filename="Facturas",
        color="#2563EB",
    ),
    "nota_credito": DocumentType(
        id="nota_credito",
        label="Nota de Crédito",
        icon="📋",
        description="Notas de crédito y ajustes",
        excel_filename="Notas_Credito",
        color="#059669",
    ),
    "nota_debito": DocumentType(
        id="nota_debito",
        label="Nota de Débito",
        icon="📝",
        description="Notas de débito con datos de pago",
        excel_filename="Notas_Debito",
        color="#D97706",
    ),
    # ── Espacios reservados para futuros tipos de documento ───────────────────
    # Aparecen en la UI pero aún no tienen plantilla ni extractor propio.
    # Para activarlos: crear el procesador, la plantilla en generador_excel.py
    # y poner reservado=False.
    "tipo4": DocumentType(
        id="tipo4",
        label="Tipo 4",
        icon="📑",
        description="— próximamente",
        excel_filename="Tipo4",
        color="#DC2626",
        reservado=True,
    ),
    "tipo5": DocumentType(
        id="tipo5",
        label="Tipo 5",
        icon="🗂️",
        description="— próximamente",
        excel_filename="Tipo5",
        color="#7C3AED",
        reservado=True,
    ),
    "tipo6": DocumentType(
        id="tipo6",
        label="Tipo 6",
        icon="📂",
        description="— próximamente",
        excel_filename="Tipo6",
        color="#0891B2",
        reservado=True,
    ),
}


def get_type(type_id: str) -> Optional[DocumentType]:
    return DOCUMENT_TYPES.get(type_id)


def all_types() -> list[DocumentType]:
    return list(DOCUMENT_TYPES.values())