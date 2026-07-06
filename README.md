# PDF → Excel  |  EGEHID
Aplicación de escritorio para convertir documentos PDF a Excel.

## Estructura del proyecto

```
app/
├── main.py                    ← Punto de entrada
├── requirements.txt           ← Dependencias Python
├── pdf2excel.spec             ← Config para generar .exe (PyInstaller)
│
├── ui/                        ← Interfaz gráfica
│   ├── app.py                 ← Ventana principal y navegación
│   ├── theme.py               ← Colores, fuentes, dimensiones
│   ├── widgets.py             ← Componentes reutilizables
│   ├── screen_select_type.py  ← Paso 1: elegir tipo de documento
│   ├── screen_select_files.py ← Paso 2: seleccionar PDFs
│   ├── screen_processing.py   ← Paso 3: barra de progreso
│   └── screen_result.py       ← Paso 4: resultado y descarga
│
├── processors/                ← Lógica de extracción
│   ├── base.py                ← Clase base (BaseProcessor)
│   ├── factory.py             ← Fábrica de procesadores
│   ├── engine.py              ← Motor de procesamiento por lotes
│   ├── nota_credito.py        ← Procesadores por tipo de documento
│   ├── extractor_encabezado.py
│   ├── extractor_detalle.py
│   └── generador_excel.py
│
├── templates/
│   └── registry.py            ← Registro de tipos de documento
│
├── utils/
│   ├── logger.py              ← Configuración de logs
│   └── files.py               ← Helpers de archivos
│
├── outputs/                   ← Excel generados (se crea automáticamente)
└── logs/                      ← Archivos de log (se crea automáticamente)
```

## Instalación

```bash
# 1. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate          # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
python main.py
```

## Generar ejecutable para Windows

```bash
pip install pyinstaller
pyinstaller pdf2excel.spec
# El ejecutable queda en:  dist/PDF2Excel/PDF2Excel.exe
```

## Agregar un nuevo tipo de documento

1. Crear la clase del procesador en `processors/` (hereda de `BaseProcessor`)
2. Registrar el tipo en `templates/registry.py` (agregar entrada al diccionario)
3. Agregar el mapeo en `processors/factory.py`

No es necesario modificar ningún otro archivo.

## Flujo de la aplicación

```
Inicio
  └── Pantalla 1: Seleccionar tipo de documento
        └── Pantalla 2: Seleccionar archivos PDF o carpeta
              └── Pantalla 3: Procesamiento (hilo de fondo, barra de progreso)
                    ├── Diálogo: duplicados detectados → preguntar sobreescribir
                    └── Pantalla 4: Resultado
                          ├── Botón: Abrir Excel
                          ├── Botón: Abrir carpeta
                          └── Botón: Procesar más documentos → volver a inicio
```
