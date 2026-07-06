"""
extractor_encabezado.py

Extrae los campos de ENCABEZADO de Facturas / Notas de Crédito / Notas de
Débito EGEHID a partir del texto plano del PDF.

Diseño:
- La extracción se basa en ANCLAS DE TEXTO (regex sobre etiquetas conocidas:
  "NCF :", "Cliente :", etc.), NO en coordenadas absolutas fijas.
- Esto hace el extractor tolerante a pequeños desplazamientos verticales/
  horizontales de los campos entre un PDF y otro, siempre que las etiquetas
  de texto se mantengan iguales.
- Si en el futuro cambia el formato (otra etiqueta, otro orden), solo hay
  que ajustar el diccionario PATRONES, sin tocar la lógica de extracción.

Tipo de documento:
- Se determina por el PREFIJO del NCF (el tipo de comprobante fiscal
  dominicano lo codifica el prefijo de 3 caracteres: E31, E32, E33, E34,
  E44, E45, E46, etc.) y, como respaldo, por el título visible del PDF
  ("NOTA DE CREDITO", "NOTA DE DEBITO", "FACT. CREDITO FISCAL", etc.).
  Ver `detectar_tipo_documento()` y `PREFIJOS_TIPO`.
"""

import re
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Patrones de extracción
# ---------------------------------------------------------------------------
# "numero_documento" cubre los 3 rótulos que usa el portal EGEHID:
#   "Nota de Crédito No. :"   (Notas de Crédito)
#   "Nota Débito No. :"       (Notas de Débito)
#   "Factura No. :"           (Facturas)
PATRONES = {
    "fecha_documento": r"Fecha\s+de\s+Factura\s*:\s*([\d.]+)",
    "ncf": r"NCF\s*:\s*([A-Z0-9]+)",
    "ncf_modificado": r"NCF\s+Modificado\s*:\s*([A-Z0-9]+)",
    "fecha_ncf_modificado": r"Fecha\s+NCF\s+Modificado\s*:\s*([\d.\/\-]+)",
    "rnc_cliente": r"RNC\s*:\s*(\d[\d-]*)",
    "cliente": r"Cliente\s*:\s*(.+?)(?:\s{2,}|\s+Fecha\s+Vcto|$)",
    "numero_documento": (
        r"(?:Nota\s+de\s+Cr[eé]dito\s+No\.|Nota\s+D[eé]bito\s+No\.|Factura\s+No\.)"
        r"\s*:\s*(\d+)"
    ),
    "fecha_vencimiento": r"Fecha\s+Vcto\.\s+Factura\s*:\s*([\d.]+)",
    "total": r"Total\s+en\s+(?:RD\$|USD|DOP)\s+([\d,]+\.\d{2})",
}


# ---------------------------------------------------------------------------
# Detección del tipo de documento
# ---------------------------------------------------------------------------
# Identificador interno usado en todo el proyecto para elegir la plantilla
# de Excel correcta. Valores posibles:
#   "factura"       → plantilla de Factura (la más amplia, 68 columnas)
#   "nota_debito"   → plantilla de Nota de Débito (36 columnas)
#   "nota_credito"  → plantilla de Nota de Crédito (31 columnas)
PREFIJOS_TIPO = {
    # Notas de Crédito
    "E34": "nota_credito",
    # Notas de Débito
    "E33": "nota_debito",
    # Facturas (todos los tipos de comprobante fiscal de factura)
    "E31": "factura",
    "E32": "factura",
    "E44": "factura",
    "E45": "factura",
    "E46": "factura",
}

# Respaldo por título visible, usado solo si el NCF no tiene un prefijo
# reconocido (PDF dañado, formato distinto, etc.)
TITULOS_TIPO = {
    "nota_credito": r"NOTA\s+DE\s+CREDITO",
    "nota_debito":  r"NOTA\s+DE\s+D[EÉ]BITO",
    "factura":      r"FACT\.\s*CREDITO\s+FISCAL|\bFACTURA\b(?!\s+DE\s+(?:CR[EÉ]DITO|D[EÉ]BITO))",
}

# Etiqueta visible para mostrar en la UI / logs
NOMBRES_TIPO = {
    "factura":      "Factura",
    "nota_credito": "Nota de Crédito",
    "nota_debito":  "Nota de Débito",
}


INDICADOR_BIEN_SERVICIO = 1


def _convertir_fecha(valor: Optional[str]) -> Optional[datetime]:
    if not valor:
        return None
    valor = valor.strip()
    # %d y %m ya aceptan valores con o sin cero inicial ("2.6.2026" y
    # "02.06.2026"), así que no hacen falta las directivas %-d/%-m (que
    # además son inválidas en Windows y lanzarían ValueError).
    for formato in (
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            pass
    return None


def _convertir_monto(valor: Optional[str]) -> Optional[float]:
    if not valor:
        return None
    valor = valor.strip()
    # Formato europeo: 166.881,78 → convertir a 166881.78
    if "," in valor and "." in valor:
        if valor.index(",") > valor.index("."):
            # El punto es separador de miles, la coma es decimal
            valor = valor.replace(".", "").replace(",", ".")
        else:
            # El punto es decimal (formato normal), quitar comas
            valor = valor.replace(",", "")
    elif "," in valor:
        # Solo coma — asumir decimal europeo
        valor = valor.replace(",", ".")
    else:
        valor = valor.replace(",", "")
    try:
        return float(valor)
    except ValueError:
        return None


def detectar_tipo_documento(texto: str, ncf: Optional[str] = None) -> str:
    """
    Devuelve el identificador interno del tipo de documento:
    "factura", "nota_credito", "nota_debito", o "desconocido".

    Estrategia (en orden de prioridad):
      1. Prefijo de 3 caracteres del NCF (más confiable: es el dato
         oficial que codifica el tipo de comprobante fiscal).
      2. Título visible en el PDF, como respaldo si el NCF no tiene
         un prefijo reconocido.
    """
    if ncf:
        prefijo = ncf.strip()[:3].upper()
        if prefijo in PREFIJOS_TIPO:
            return PREFIJOS_TIPO[prefijo]

    for tipo, patron in TITULOS_TIPO.items():
        if re.search(patron, texto, re.IGNORECASE):
            return tipo

    return "desconocido"


def extraer_observaciones(texto: str) -> Optional[str]:
    """
    Extrae el bloque de observaciones del documento.

    Captura todo el texto que aparece debajo de "OBSERVACIONES"
    hasta antes de la firma o del final del documento.
    """

    patron = (
        r"OBSERVACIONES\s*:?\s*"
        r"(.*?)"
        r"(?=_{3,}|Elaborado\s+Por|Revisado\s+Por|Aprobado\s+Por|Licda\.|Lic\.|$)"
    )

    coincidencia = re.search(
        patron,
        texto,
        re.IGNORECASE | re.DOTALL,
    )

    if not coincidencia:
        return None

    observaciones = coincidencia.group(1)

    # Reemplazar múltiples espacios y saltos de línea por uno solo
    observaciones = re.sub(r"\s+", " ", observaciones)

    observaciones = observaciones.strip()

    return observaciones if observaciones else None


def extraer_encabezado(texto: str) -> dict:
    """
    Extrae los datos del encabezado del PDF.

    Devuelve un diccionario con los datos convertidos a sus
    tipos correspondientes. Incluye "tipo_documento" con el
    identificador interno ("factura" | "nota_credito" | "nota_debito")
    usado para elegir la plantilla de Excel correcta.
    """

    encabezado = {}

    for campo, patron in PATRONES.items():

        coincidencia = re.search(
            patron,
            texto,
            re.IGNORECASE | re.MULTILINE,
        )

        if coincidencia:

            valor = coincidencia.group(1).strip()

            encabezado[campo] = valor if valor else None

        else:

            encabezado[campo] = None

    # Conversión de tipos
    encabezado["fecha_documento"] = _convertir_fecha(encabezado["fecha_documento"])
    encabezado["fecha_vencimiento"] = _convertir_fecha(encabezado["fecha_vencimiento"])
    encabezado["fecha_ncf_modificado"] = _convertir_fecha(encabezado.get("fecha_ncf_modificado"))
    encabezado["total"] = _convertir_monto(encabezado["total"])

    # Detectar moneda: USD si el texto lo menciona, DOP/RD$ en caso contrario
    if re.search(r'\bUSD\b|d[oó]lares?', texto, re.IGNORECASE):
        encabezado["moneda"] = "USD"
    elif re.search(r'\bEUR\b|euros?', texto, re.IGNORECASE):
        encabezado["moneda"] = "EUR"
    else:
        encabezado["moneda"] = "DOP"

    # Campos calculados
    encabezado["tipo_documento"] = detectar_tipo_documento(texto, encabezado.get("ncf"))
    encabezado["indicador_bien_servicio"] = INDICADOR_BIEN_SERVICIO
    encabezado["observaciones"] = extraer_observaciones(texto)

    return encabezado


if __name__ == "__main__":

    import pdfplumber

    with pdfplumber.open("../muestras/800001168.pdf") as pdf:

        texto_pdf = pdf.pages[0].extract_text()

    resultado = extraer_encabezado(texto_pdf)

    for clave, valor in resultado.items():

        print(f"{clave:25}: {valor}")