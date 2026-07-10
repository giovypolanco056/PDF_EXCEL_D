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


# Regex para separar "NOMBRE CONCEPTO 1 kWh" → (nombre, cantidad, unidad)
# Captura: texto libre, número opcional (entero o decimal), unidad opcional
_PAT_CANTIDAD_UNIDAD = re.compile(
    r"^(.*?)\s+([\d]+(?:[.,]\d+)?)\s+([A-Za-z]+%?)\s*$"
)

# Formato de un IMPORTE monetario: dígitos con separador de miles opcional
# y 1-2 decimales (p.ej. "22,789,532.00", "1708.18", "-5,124.53").
# Se usa para localizar el monto por su FORMA, no por su posición X, de modo
# que la extracción funcione aunque la columna esté en otro lugar. Un año
# suelto como "2025"/"2026" NO cumple (no tiene decimales) y se ignora.
_PAT_MONTO = re.compile(r"^-?\d[\d,]*\.\d{1,2}$")


def _convertir_monto(valor: str) -> Optional[float]:
    """Convierte montos con formato '131,453.24' a float."""
    limpio = valor.strip().replace(",", "")
    try:
        return float(limpio)
    except ValueError:
        return None


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
            UNIDADES_VALIDAS = {"kwh", "kw", "mwh", "mw", "m3", "gj", "mmbtu", "unidad", "unidades"}
            if unidad.lower() in UNIDADES_VALIDAS:
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

    # Fin de la tabla: la primera fila "Total …" posterior a la cabecera.
    # (Ancla de texto, no de coordenadas: funciona esté donde esté la tabla.)
    palabra_fin = next(
        (w for w in palabras
         if w["text"].strip().lower() == "total" and w["top"] > top_cabecera),
        None,
    )
    top_fin = palabra_fin["top"] if palabra_fin else float("inf")

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
            if _PAT_MONTO.match(linea_ord[i]["text"].strip()):
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