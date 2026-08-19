"""
extractor_detalle.py

Extrae las líneas de DETALLE (Concepto / Total RD$) de una Nota de
Crédito / Factura / Nota de Débito EGEHID.

Diseño:
- El detalle se extrae usando las PALABRAS CON COORDENADAS (x0, top, etc.)
  que entrega pdfplumber, porque el texto plano mezcla la descripción y el
  monto sin un separador fiable.
- Se ubica la fila de encabezado de la tabla ("Concepto" / "Total RD$")
  para conocer en qué posición vertical empieza la tabla y en qué columna
  X arranca cada campo.
- Soporte para PDF de varias páginas: procesar.py concatena las palabras
  de todas las páginas ajustando el offset vertical.

Campos devueltos por línea:
    {
        "numero_documento": str | None,
        "nombre":           str,        ← nombre del ítem (sin cantidad ni unidad)
        "descripcion":      str | None, ← descripción adicional (vacío si no hay)
        "cantidad":         float,      ← extraída del PDF; 1.0 si no aparece
        "unidad_medida":    str | None, ← "kWh", "kW", etc.; None si no aparece
        "monto":            float | None
    }

Facturas del MERCADO SPOT tienen un subtítulo entre el encabezado de la
tabla y las filas de datos ("TRANSACCIONES ECONOMICAS DEL MERCADO SPOT
CORRESPONDIENTE AL MES DE MARZO 2026"). Ese bloque se salta
automáticamente porque no tiene monto numérico.

Para las Facturas, la celda "Concepto" contiene texto como:
    "ENERGIA 1 kWh"
    "POTENCIA 1 kW"
    "DERECHO DE CONEXION 1 kW"
donde la cantidad y la unidad están al final del nombre. Esta función
separa nombre, cantidad y unidad usando regex.

Para las Notas de Crédito y Notas de Débito, el concepto es solo el
nombre sin cantidad ni unidad:
    "RELIQ CONTRATO POTENCIA 2025"
En ese caso cantidad = 1.0 y unidad_medida = None.
"""

import re
from typing import Optional


# Unidades de medida conocidas. Sirven para NO confundir una cantidad con
# unidad (p.ej. "2.44105 MW") con un importe monetario.
_UNIDADES_MEDIDA = {"kwh", "kw", "mwh", "mw", "m3", "gj", "mmbtu", "unidad", "unidades"}

# Regex para separar "NOMBRE CONCEPTO 1 kWh" → (nombre, cantidad, unidad)
# Captura: texto libre, número opcional (entero o decimal), unidad opcional
_PAT_CANTIDAD_UNIDAD = re.compile(
    r"^(.*?)\s+([\d]+(?:[.,]\d+)?)\s+([A-Za-z]+%?)\s*$"
)

# Forma numérica candidata a IMPORTE: paréntesis/negativo opcional, dígitos
# con separador de miles opcional y decimales opcionales.
#   Acepta: "22,789,532.00", "1,708.1835", "-5,124.53", "4,774,623", "(5,124.53)"
_PAT_NUM = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?$")


def _es_monto(token: str) -> bool:
    """
    True si el token es un IMPORTE monetario (por su FORMA, no su posición X).

    Un número "pelado" sin punto decimal, sin separador de miles y sin
    paréntesis (p. ej. un año "2025" o una cantidad "1") NO se considera
    importe: exigir al menos una de esas señales evita capturar años/IDs
    como si fueran montos.
    """
    t = token.strip()
    if not _PAT_NUM.match(t):
        return False
    return ("." in t) or ("," in t) or ("(" in t)


def _convertir_monto(valor: str) -> Optional[float]:
    """
    Convierte un importe a float. Soporta:
      - separador de miles:      "131,453.24" → 131453.24
      - más de dos decimales:    "1,708.1835" → 1708.1835
      - signo negativo:          "-5,124.53"  → -5124.53
      - negativo contable:       "(5,124.53)" → -5124.53
    """
    t = valor.strip()
    negativo = False
    if t.startswith("(") and t.endswith(")"):
        negativo = True
        t = t[1:-1].strip()
    t = t.replace(",", "")
    try:
        num = float(t)
    except ValueError:
        return None
    return -num if negativo else num


# Fila del GRAN TOTAL que cierra la tabla de detalle: "Total en RD$ …".
# Sirve para NO cortar la tabla en un concepto que casualmente contenga la
# palabra "Total" (p. ej. "AJUSTE TOTAL ENERGIA"), lo que perdía líneas.
_PAT_FIN_TABLA = re.compile(r"^total\s+en\s+(rd\$|rd|dop|usd|eur)\b", re.IGNORECASE)


def _es_numero(texto: str) -> bool:
    try:
        float(texto.replace(",", ""))
        return True
    except ValueError:
        return False


def _parsear_descripcion(texto: str) -> tuple[str, float, Optional[str]]:
    """
    Intenta separar "NOMBRE 1 kWh" en (nombre, cantidad, unidad).
    Si no hay cantidad/unidad al final, devuelve (texto_completo, 1.0, None).
    Solo se reconoce si la parte final tiene exactamente (número unidad)
    para evitar falsos positivos con nombres como "CONTRATO DC 2025".
    """
    m = _PAT_CANTIDAD_UNIDAD.match(texto.strip())
    if m:
        nombre   = m.group(1).strip()
        cantidad_str = m.group(2).replace(",", ".")
        unidad   = m.group(3).strip()
        try:
            cantidad = float(cantidad_str)
            # Solo aceptar unidades de medida conocidas para evitar
            # partir "RELIQ CONTRATO DC 2025" en nombre="RELIQ CONTRATO DC" + cantidad=2025
            if unidad.lower() in _UNIDADES_MEDIDA:
                return nombre, cantidad, unidad
        except ValueError:
            pass
    return texto.strip(), 1.0, None


def _agrupar_por_linea(palabras: list, tolerancia: float = 2.0) -> list:
    """Agrupa palabras de pdfplumber en líneas según su coordenada 'top'."""
    lineas = []
    for palabra in sorted(palabras, key=lambda w: (w["top"], w["x0"])):
        ubicada = False
        for linea in lineas:
            if abs(linea[0]["top"] - palabra["top"]) <= tolerancia:
                linea.append(palabra)
                ubicada = True
                break
        if not ubicada:
            lineas.append([palabra])
    return lineas


def _top_fin_tabla(palabras: list, top_cabecera: float) -> float:
    """
    Coordenada 'top' donde termina la tabla de detalle.

    Preferentemente la fila del GRAN TOTAL ("Total en RD$ …"); si no aparece,
    como respaldo, la primera fila cuyo PRIMER token (más a la izquierda) sea
    exactamente "Total". Así un concepto que contenga la palabra "Total" en
    medio (p. ej. "AJUSTE TOTAL ENERGIA") ya NO corta la tabla.
    """
    debajo = [w for w in palabras if w["top"] > top_cabecera + 2]
    lineas = sorted(_agrupar_por_linea(debajo), key=lambda ln: min(w["top"] for w in ln))
    respaldo = None
    for linea in lineas:
        ordenada = sorted(linea, key=lambda w: w["x0"])
        texto = " ".join(w["text"] for w in ordenada).strip()
        if _PAT_FIN_TABLA.match(texto):
            return min(w["top"] for w in linea)
        if respaldo is None and ordenada[0]["text"].strip().lower() == "total":
            respaldo = min(w["top"] for w in linea)
    return respaldo if respaldo is not None else float("inf")


def extraer_detalle(palabras: list, numero_documento: Optional[str] = None) -> list:
    """
    Recibe la lista de palabras con coordenadas y devuelve una lista de
    diccionarios, uno por cada línea de detalle:
        {
            "numero_documento": str | None,
            "nombre":           str,
            "descripcion":      str | None,
            "cantidad":         float,
            "unidad_medida":    str | None,
            "monto":            float | None
        }
    """
    # Localizar cabecera: "Concepto" y la columna de monto ("RD$" o "USD")
    palabra_concepto = next(
        (w for w in palabras if w["text"].strip().lower().replace(":", "") == "concepto"),
        None,
    )
    if palabra_concepto is None:
        return []

    top_cabecera = palabra_concepto["top"]

    # Fin de la tabla: la fila del GRAN TOTAL ("Total en RD$ …"), no cualquier
    # palabra "Total" (que podría estar DENTRO de un concepto y cortar la tabla
    # antes de tiempo, perdiendo líneas de detalle).
    top_fin = _top_fin_tabla(palabras, top_cabecera)

    # Palabras entre la cabecera y el "Total"
    palabras_tabla = [
        w for w in palabras
        if w["top"] > top_cabecera + 2 and w["top"] < top_fin
    ]

    lineas = _agrupar_por_linea(palabras_tabla)

    detalle = []
    for linea in lineas:
        # Reconstruir la fila ordenando por posición horizontal.
        linea_ord = sorted(linea, key=lambda w: w["x0"])

        # El importe es el ÚLTIMO token con FORMATO monetario. Localizarlo por
        # su forma (dígitos + decimales) y no por su coordenada X hace la
        # extracción independiente de la posición: da igual en qué columna
        # esté el monto, o que los números grandes empiecen más a la izquierda.
        idx_monto = None
        for i in range(len(linea_ord) - 1, -1, -1):
            if _es_monto(linea_ord[i]["text"].strip()):
                # No confundir una CANTIDAD con unidad (p.ej. "2.44105 MW")
                # con un importe: si el token siguiente es una unidad de
                # medida, este número es la cantidad, no el monto.
                siguiente = (
                    linea_ord[i + 1]["text"].strip().lower().rstrip(".")
                    if i + 1 < len(linea_ord) else ""
                )
                if siguiente in _UNIDADES_MEDIDA:
                    continue
                idx_monto = i
                break

        if idx_monto is None:
            continue  # fila sin importe (subtítulo, encabezado intermedio, etc.)

        texto_monto = linea_ord[idx_monto]["text"].strip()
        texto_desc  = " ".join(w["text"] for w in linea_ord[:idx_monto]).strip()

        if not texto_desc:
            continue

        monto = _convertir_monto(texto_monto)

        # Separar nombre, cantidad y unidad de medida
        nombre, cantidad, unidad_medida = _parsear_descripcion(texto_desc)

        detalle.append({
            "numero_documento": numero_documento,
            "nombre":           nombre,
            "descripcion":      None,   # el PDF no proporciona descripción separada
            "cantidad":         cantidad,
            "unidad_medida":    unidad_medida,
            "monto":            monto,
        })

    return detalle


if __name__ == "__main__":
    import sys
    import pdfplumber

    ruta = sys.argv[1] if len(sys.argv) > 1 else "../muestras/800001168.pdf"

    palabras_todas = []
    offset_vertical = 0.0

    with pdfplumber.open(ruta) as pdf:
        for page in pdf.pages:
            palabras_pagina = page.extract_words()
            for palabra in palabras_pagina:
                copia = dict(palabra)
                copia["top"] = copia["top"] + offset_vertical
                palabras_todas.append(copia)
            if palabras_pagina:
                offset_vertical += max(w["bottom"] for w in palabras_pagina) + 10

    resultado = extraer_detalle(palabras_todas)
    for fila in resultado:
        print(fila)