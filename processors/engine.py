# -*- coding: utf-8 -*-
"""
processors/engine.py

Motor de procesamiento por lotes.
Se ejecuta en un hilo separado para no bloquear la UI.
Comunica progreso y resultados mediante callbacks.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

from processors.factory import get_processor
from processors.generador_excel import PLANTILLAS
from templates.registry import get_type
from utils.files import collect_pdfs, validate_pdf
from utils.logger import get_logger

log = get_logger()

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _clave_duplicado(enc: dict) -> str:
    """
    Clave robusta para detectar documentos duplicados.

    Prioriza el NCF (identificador fiscal ÚNICO del comprobante): dos PDFs con
    el mismo NCF son el mismo documento aunque cambie el nombre del archivo o
    la ruta. Si el NCF no se pudo extraer, cae a número+fecha; y si tampoco
    hay número, usa el NCF vacío + fecha para no colapsar documentos distintos.
    """
    ncf = (enc.get("ncf") or "").strip().upper()
    if ncf:
        return f"NCF:{ncf}"
    num = str(enc.get("numero_documento") or "").strip()
    fecha = enc.get("fecha_documento")
    fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha or "")
    return f"NUM:{num}|{fecha_str}"


@dataclass
class ProcessResult:
    """Resultado completo de un lote de procesamiento."""
    total: int = 0
    exitosos: int = 0
    omitidos: int = 0        # duplicados no sobreescritos
    fallidos: int = 0
    advertencias: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    # Reporte detallado por documento (para la pantalla de resultados):
    #   {archivo, ncf, tipo, estado, lineas, problemas: [(sev, msg), …]}
    #   estado ∈ {"ok", "advertencia", "error", "omitido", "reemplazado"}
    documentos: list[dict] = field(default_factory=list)
    excel_path: Optional[Path] = None
    output_dir: Optional[Path] = None


# Tipo del callback de progreso: (actual, total, mensaje)
ProgressCallback = Callable[[int, int, str], None]
# Tipo del callback de duplicado: (nombre_pdf, numero_doc, fecha) → bool
DuplicateCallback = Callable[[str, str, str], bool]


def run_batch(
    type_id: str,
    pdf_paths: list[str],
    output_dir: Optional[str],
    on_progress: ProgressCallback,
    on_duplicate: DuplicateCallback,
    on_done: Callable[[ProcessResult], None],
    on_error: Callable[[str], None],
) -> threading.Thread:
    """
    Lanza el procesamiento en un hilo de fondo.
    Devuelve el Thread iniciado (útil para join si se necesita).
    """
    def _run():
        try:
            result = _process(
                type_id, pdf_paths, output_dir,
                on_progress, on_duplicate,
            )
            on_done(result)
        except Exception as exc:
            log.exception("Error inesperado en el motor de procesamiento")
            on_error(str(exc))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def _process(
    type_id: str,
    raw_paths: list[str],
    output_dir_raw: Optional[str],
    on_progress: ProgressCallback,
    on_duplicate: DuplicateCallback,
) -> ProcessResult:

    result = ProcessResult()
    processor = get_processor(type_id)

    # Resolver carpeta de salida
    out_dir = Path(output_dir_raw) if output_dir_raw else _OUTPUT_DIR / type_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del Excel de salida: uno NUEVO por cada proceso (timestamp),
    # nunca se sobreescribe ni se acumula en un archivo previo.
    doc_type = get_type(type_id)
    excel_base = doc_type.excel_filename if doc_type else type_id
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_name = f"{excel_base}_{ts}.xlsx"
    excel_path = out_dir / excel_name
    result.output_dir = out_dir

    # Recolectar PDFs
    pdfs = collect_pdfs(raw_paths)
    result.total = len(pdfs)
    if not pdfs:
        raise ValueError("No se encontraron archivos PDF en la selección.")

    on_progress(0, result.total, "Validando archivos…")

    # Primera pasada: validar y extraer
    documentos_ok: list[dict] = []
    for i, pdf_path in enumerate(pdfs, 1):
        on_progress(i - 1, result.total, f"Leyendo {pdf_path.name}…")

        info = {
            "archivo": pdf_path.name, "ncf": None, "tipo": None,
            "estado": "ok", "lineas": 0, "problemas": [],
        }
        result.documentos.append(info)

        ok, err = validate_pdf(pdf_path)
        if not ok:
            info["estado"] = "fallido"
            info["problemas"].append(("error", err))
            result.errores.append(f"{pdf_path.name}: {err}")
            result.fallidos += 1
            log.error(f"{pdf_path.name}: {err}")
            continue

        try:
            doc = processor.procesar_pdf(pdf_path)   # los problemas vienen en doc
            enc = doc["encabezado"]
            info["ncf"]     = enc.get("ncf")
            info["tipo"]    = enc.get("tipo_documento")
            info["lineas"]  = len(doc["detalle"])
            info["problemas"] = list(doc.get("problemas", []))

            # Advertir si el tipo detectado no coincide con el elegido.
            detectado = enc.get("tipo_documento")
            if (
                type_id in PLANTILLAS
                and detectado in PLANTILLAS
                and detectado != type_id
            ):
                info["problemas"].append((
                    "advertencia",
                    f"Detectado como '{detectado}' pero se procesa como '{type_id}'",
                ))
                log.warning(
                    f"Tipo no coincide en {pdf_path.name}: "
                    f"detectado={detectado}, seleccionado={type_id}"
                )

            # Estado global del documento según la severidad de sus problemas
            if any(sev == "error" for sev, _ in info["problemas"]):
                info["estado"] = "error"
            elif info["problemas"]:
                info["estado"] = "advertencia"

            # Volcar problemas al listado plano (log de la pantalla de proceso)
            for sev, msg in info["problemas"]:
                result.advertencias.append(f"{pdf_path.name}: {msg}")

            doc["_info"] = info
            documentos_ok.append(doc)
        except Exception as exc:
            info["estado"] = "fallido"
            info["problemas"].append(("error", str(exc)))
            result.errores.append(f"{pdf_path.name}: {exc}")
            result.fallidos += 1
            log.error(f"{pdf_path.name}: {exc}", exc_info=True)

    if not documentos_ok:
        raise ValueError(
            "Ningún PDF pudo procesarse correctamente. "
            "Revisa el log para más detalles."
        )

    # Segunda pasada: detectar duplicados DENTRO del mismo lote.
    # Como cada proceso genera un Excel nuevo, no hay archivo previo contra
    # el cual comparar; solo se avisa si el mismo documento (número|fecha)
    # viene repetido en la selección de PDFs de esta corrida.
    on_progress(result.total, result.total, "Verificando duplicados…")

    # clave → posición del documento en documentos_finales (para poder
    # reemplazarlo si el usuario decide sobreescribir un duplicado del lote).
    por_clave: dict[str, int] = {}
    documentos_finales: list[dict] = []

    for doc in documentos_ok:
        enc  = doc["encabezado"]
        num  = str(enc.get("numero_documento") or "")
        fecha = enc.get("fecha_documento")
        fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha or "")
        clave = _clave_duplicado(enc)   # por NCF (robusto), con respaldo num|fecha
        nombre = doc["ruta_pdf"].name

        if clave in por_clave:
            # Mostrar el NCF en el diálogo cuando exista (más informativo)
            ident = (enc.get("ncf") or num or "").strip()
            sobreescribir = on_duplicate(nombre, ident, fecha_str)
            if sobreescribir:
                # Reemplazar la entrada anterior del lote por esta (no
                # duplicar filas: cada proceso genera un Excel nuevo).
                doc_previo = documentos_finales[por_clave[clave]]
                if doc_previo.get("_info"):
                    doc_previo["_info"]["estado"] = "reemplazado"
                    doc_previo["_info"]["problemas"].append(
                        ("advertencia", f"Duplicado (NCF {ident}): reemplazado por {nombre}")
                    )
                documentos_finales[por_clave[clave]] = doc
                log.info(f"Sobreescribiendo duplicado del lote: {nombre}")
            else:
                result.omitidos += 1
                if doc.get("_info"):
                    doc["_info"]["estado"] = "omitido"
                    doc["_info"]["problemas"].append(
                        ("advertencia", f"Duplicado (NCF {ident}): omitido")
                    )
                log.info(f"Duplicado omitido: {nombre}")
        else:
            por_clave[clave] = len(documentos_finales)
            documentos_finales.append(doc)

    if not documentos_finales:
        raise ValueError(
            "Todos los documentos eran duplicados y fueron omitidos. "
            "No se generó el Excel."
        )

    # Generar Excel — la plantilla se fija por el tipo elegido por el usuario,
    # no por lo detectado en el primer PDF (resultado determinista).
    on_progress(result.total, result.total, "Generando Excel…")
    processor.generar_excel(documentos_finales, str(excel_path), tipo_documento=type_id)

    # documentos_finales = nuevos + sobreescritos; los omitidos nunca entraron.
    result.exitosos = len(documentos_finales)
    result.excel_path = excel_path
    log.info(
        f"Lote completado — exitosos={result.exitosos} "
        f"omitidos={result.omitidos} fallidos={result.fallidos}"
    )
    return result
