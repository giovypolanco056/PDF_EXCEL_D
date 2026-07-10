# -*- coding: utf-8 -*-
"""
processors/diagnostico.py

Revisa un documento ya extraído (encabezado + detalle) y devuelve la lista
concreta de problemas que tiene, para poder decirle al usuario EXACTAMENTE
qué le faltó a cada PDF en vez de un genérico "falló".

Es independiente de la posición: solo mira si los campos se pudieron extraer
(no dónde estaban), así que tolera facturas que no presenten algún campo.
"""

from typing import Optional


# Campos del encabezado a verificar: (clave, etiqueta, severidad)
#   "error"       → dato imprescindible que faltó
#   "advertencia" → dato deseable que faltó, pero no bloquea
_CAMPOS_ENCABEZADO = [
    ("ncf",              "NCF",                        "error"),
    ("numero_documento", "Número de documento",        "error"),
    ("fecha_documento",  "Fecha del documento",        "advertencia"),
    ("rnc_cliente",      "RNC del cliente",            "advertencia"),
    ("cliente",          "Razón social del cliente",   "advertencia"),
]


def diagnosticar(encabezado: dict, detalle: list) -> list[tuple[str, str]]:
    """
    Devuelve una lista de (severidad, mensaje) con los problemas encontrados.
    Lista vacía = documento sin problemas.

    severidad ∈ {"error", "advertencia"}.
    """
    problemas: list[tuple[str, str]] = []

    # 1. Campos del encabezado ausentes
    for clave, etiqueta, severidad in _CAMPOS_ENCABEZADO:
        if not encabezado.get(clave):
            problemas.append((severidad, f"{etiqueta} no encontrado"))

    # 2. Detalle
    if not detalle:
        problemas.append(("error", "Sin líneas de detalle"))
    else:
        sin_monto = sum(1 for l in detalle if l.get("monto") is None)
        if sin_monto:
            problemas.append(
                ("advertencia", f"{sin_monto} línea(s) de detalle sin monto")
            )

    # 3. Cuadre de totales (encabezado vs suma del detalle)
    total = encabezado.get("total")
    if total is None:
        problemas.append(("advertencia", "Total del documento no encontrado"))
    elif detalle:
        suma = sum((l.get("monto") or 0) for l in detalle)
        if abs(total - suma) >= 0.01:
            problemas.append((
                "advertencia",
                f"El total no cuadra: encabezado={total:,.2f}, "
                f"suma del detalle={suma:,.2f}",
            ))

    return problemas


def resumir(encabezado: dict, detalle: list) -> Optional[str]:
    """Devuelve un texto de una línea con los problemas, o None si no hay."""
    problemas = diagnosticar(encabezado, detalle)
    if not problemas:
        return None
    partes = [f"{'✗' if sev == 'error' else '⚠'} {msg}" for sev, msg in problemas]
    return "; ".join(partes)
