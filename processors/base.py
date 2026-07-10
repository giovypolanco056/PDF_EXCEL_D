# -*- coding: utf-8 -*-
"""
processors/base.py

Clase base para todos los procesadores de documentos.
Cada tipo de documento hereda de BaseProcessor e implementa:
  - extraer_encabezado(texto) → dict
  - extraer_detalle(palabras, numero_documento) → list
  - generar_excel(documentos, ruta_salida) → None

El método `procesar_pdf` es común a todos los tipos.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional
import pdfplumber

from utils.logger import get_logger
from processors.diagnostico import diagnosticar

log = get_logger()


class BaseProcessor(ABC):
    """Procesador base. Subclasificar para cada tipo de documento."""

    # Nombre visible (para logs)
    nombre: str = "Documento"

    def procesar_pdf(
        self,
        ruta_pdf: Path,
        on_warning: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """
        Abre el PDF, extrae texto y palabras con coordenadas,
        llama a los extractores específicos del tipo y devuelve
        {"encabezado": ..., "detalle": ..., "ruta_pdf": ...}.
        Lanza ValueError / IOError si el archivo no es procesable.
        """
        log.info(f"[{self.nombre}] Procesando: {ruta_pdf.name}")

        textos: list[str] = []
        palabras_todas: list[dict] = []
        offset = 0.0

        with pdfplumber.open(ruta_pdf) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("El PDF no contiene páginas")

            for page in pdf.pages:
                texto = page.extract_text() or ""
                textos.append(texto)

                palabras_pag = page.extract_words()
                for w in palabras_pag:
                    copia = dict(w)
                    copia["top"] = copia["top"] + offset
                    palabras_todas.append(copia)

                if palabras_pag:
                    offset += max(w["bottom"] for w in palabras_pag) + 10

        texto_completo = "\n".join(textos)
        if not texto_completo.strip():
            raise ValueError("No se pudo extraer texto (¿PDF escaneado/imagen?)")

        encabezado = self.extraer_encabezado(texto_completo)

        detalle = self.extraer_detalle(
            palabras_todas,
            numero_documento=encabezado.get("numero_documento"),
        )

        # Diagnóstico detallado: reportar EXACTAMENTE qué problemas tiene el
        # documento (campos ausentes, sin detalle, total que no cuadra…), sin
        # detener el proceso. Tolera facturas que no presenten algún campo.
        problemas = diagnosticar(encabezado, detalle)
        for severidad, msg in problemas:
            marca = "✗" if severidad == "error" else "⚠"
            texto = f"{ruta_pdf.name}: {marca} {msg}"
            if on_warning:
                on_warning(texto)
            if severidad == "error":
                log.warning(f"[{self.nombre}] {texto}")
            else:
                log.info(f"[{self.nombre}] {texto}")

        return {
            "encabezado": encabezado,
            "detalle": detalle,
            "ruta_pdf": ruta_pdf,
            "problemas": problemas,
        }

    @abstractmethod
    def extraer_encabezado(self, texto: str) -> dict:
        """Extrae campos del encabezado desde el texto plano del PDF."""
        ...

    @abstractmethod
    def extraer_detalle(self, palabras: list, numero_documento: Optional[str]) -> list:
        """Extrae líneas de detalle desde las palabras con coordenadas."""
        ...

    @abstractmethod
    def generar_excel(
        self, documentos: list, ruta_salida: str, tipo_documento: Optional[str] = None
    ) -> None:
        """Genera el Excel de salida con los documentos procesados."""
        ...
