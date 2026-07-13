# -*- coding: utf-8 -*-
"""
processors/constantes.py

Constantes y REGLAS DE NEGOCIO centralizadas del portal EGEHID / DGII.

Reúne en un solo lugar los valores FIJOS que exige el formato de carga del
portal y que NO provienen del PDF. Antes estaban dispersos como "números
mágicos" repartidos entre extractor_encabezado.py y generador_excel.py.

Al centralizarlos:
  - Un cambio de la DGII (p. ej. renovar la vigencia del NCF) se hace en UN
    solo sitio, no buscando constantes escondidas en el código.
  - Cada valor queda documentado con la columna del portal a la que
    corresponde y por qué es fijo.

Cualquier otro dato de las filas E/D proviene exclusivamente del PDF.
"""

from datetime import datetime


# ── Fila E — encabezado del documento ────────────────────────────────────────
# Valores fijos que exige la plantilla del portal en la fila de encabezado.

# Columna "Tipo de Ingresos".
IND_INGRESO = 1

# Columna "Tipo de Pago".
TIPO_PAGO = 2

# Columna "Termino de Pago". Solo existe en las plantillas de Factura y
# Nota de Débito (la de Nota de Crédito no trae esta columna).
TERMINO_PAGO = 0

# Columna "Codigo de Modificación". Aplica ÚNICAMENTE a notas de crédito y
# débito, que modifican un comprobante previo; las facturas la dejan vacía.
COD_MODIFICACION_NOTA = 3


# ── Fila D — detalle de ítem ─────────────────────────────────────────────────
# Columna "Indicador Bien o Servicio" (a nivel de línea de detalle).
D_IND_BIEN_SERVICIO = 2

# Columna "Indicador Tasa ITBIS".
D_IND_TASA_ITBIS = 4


# ── Encabezado — indicador global de bien/servicio ───────────────────────────
# Se guarda en el encabezado extraído (no en el detalle). Valor fijo en las
# facturas de EGEHID.
INDICADOR_BIEN_SERVICIO = 1


# ── Fecha de expiración del NCF (autorización e-CF de la DGII) ────────────────
# Valor FIJO que NO aparece en el PDF; el portal EGEHID lo exige en la columna
# "Fecha Expiracion NCF" de las plantillas de Factura y Nota de Débito.
#
# ▸▸ ACTUALIZAR aquí cuando la DGII renueve la vigencia de la secuencia de NCF.
FECHA_EXPIRACION_NCF = datetime(2027, 12, 31)
