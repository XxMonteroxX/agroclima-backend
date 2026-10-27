# Sistema de Monitoreo Agroclimático — Maíz y Aguacate

Backend FastAPI para el **Proyecto 1**. Procesa en RAM 15,000 registros
agroclimáticos de Jalisco, Michoacán, Sinaloa y Veracruz, con los algoritmos
de ordenamiento y búsqueda implementados **100% manualmente en Python puro**
(sin `.sort()`, `sorted()`, Pandas ni NumPy para ordenar/buscar), instrumentados
con contadores de comparaciones, movimientos y tiempo en nanosegundos.

## Estructura del proyecto

```
agroclima_backend/
├── main.py                           # Endpoints FastAPI
├── storage.py                        # Estado en RAM, bitácoras, backup, Método Alfa
├── algorithms.py                     # Radix/Counting/Bucket/Quick/Merge/Heap Sort + búsquedas
├── generate_dataset.py               # Generador del CSV de 15,000 registros (ya ejecutado)
├── dataset_agroclimatico_15000.csv   # Dataset fuente (10 columnas, 15,000 filas)
├── requirements.txt
└── README.md
```

Al ejecutarse, el sistema además generará automáticamente en esta misma carpeta:

- `bitacora_ordenacion.txt` — una línea por cada ordenamiento ejecutado.
- `bitacora_busqueda.txt` — una línea por cada búsqueda ejecutada.
- `registros_ordenados_backup.csv` — respaldo de los 15,000 registros, creado
  en la **primera** ordenación que se ejecute.

## 1. Instalación

Requiere Python 3.10+.

```bash
pip install -r requirements.txt
# o bien:
pip install fastapi "uvicorn[standard]" pydantic
```

## 2. Ejecución del servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Documentación interactiva (Swagger): `http://localhost:8000/docs`

El dataset ya viene generado (`dataset_agroclimatico_15000.csv`, 15,000 filas).
Si quisieras regenerarlo con otra semilla o volumen de datos distinto, edita y
vuelve a correr `python3 generate_dataset.py`.

## 3. Flujo de uso recomendado

1. **`POST /api/fase1/cargar`** — carga el CSV a RAM (lista de diccionarios) y
   mide el tiempo de carga.
2. **`POST /api/fase2/disparador-ordenamiento`** — sortea un campo clave
   (`id_estacion`, `temperatura_promedio` o `fecha_registro`) y un algoritmo
   permitido para ese campo, lo ejecuta y actualiza cuál es el campo
   actualmente ordenado en RAM.
3. **`GET /api/fase3/disparador-busqueda`** — sortea entre Búsqueda Binaria y
   Búsqueda Lineal. Si sale Binaria, indica el `campo_requerido` (el que esté
   ordenado en ese momento) o devuelve una alerta de seguridad si la RAM aún
   no está ordenada por ningún campo.
4. **`POST /api/fase3/ejecutar-busqueda`** — ejecuta la búsqueda con el
   `metodo`, `campo` y `valor` indicados.
5. **`GET /api/estado`** — consulta el estado general: si hay datos cargados,
   el campo ordenado actual y el resumen del Método Alfa.

## 4. Endpoints — contrato detallado

### `POST /api/fase1/cargar`
Sin body. Respuesta:
```json
{
  "mensaje": "Se realizó la carga de los 15,000 registros con sus 10 columnas a la estructura [ArrayList/Lista de Objetos] y le tomó [12345678] nanosegundos completar la acción.",
  "tiempo_ns": 12345678,
  "total_registros": 15000,
  "muestra_primeros_30": [ { ...10 campos... }, ... ],
  "muestra_ultimos_30": [ { ...10 campos... }, ... ]
}
```

### `POST /api/fase2/disparador-ordenamiento`
Sin body. Requiere haber llamado antes a `/api/fase1/cargar`. Respuesta:
```json
{
  "campo_seleccionado": {"clave": 3, "nombre": "fecha_registro"},
  "metodo_asignado": "Merge Sort",
  "tiempo_ns": 59297917,
  "comparaciones": 102252,
  "movimientos": 208616,
  "mensaje_benchmarking": "Ordenamiento 'Merge Sort' sobre el campo 'fecha_registro' completado en 59297917 ns, con 102252 comparaciones y 208616 movimientos/asignaciones de memoria.",
  "metodo_alfa": {
    "nombre": "Merge Sort",
    "veces_ejecutado": 2,
    "historial_completo": {"Radix Sort": 1, "Merge Sort": 2, "...": "..."}
  },
  "muestra_primeros_30": [ ... ],
  "muestra_ultimos_30": [ ... ]
}
```

### `GET /api/fase3/disparador-busqueda`
Respuesta cuando sale Binaria y **sí** hay un campo ordenado:
```json
{
  "metodo_seleccionado": "Búsqueda Binaria",
  "alerta_seguridad": false,
  "campo_requerido": "temperatura_promedio",
  "mensaje": "Solicite al usuario el valor a buscar para el campo obligatorio 'temperatura_promedio' ..."
}
```
Respuesta cuando sale Binaria y **no** hay ningún campo ordenado aún:
```json
{
  "metodo_seleccionado": "Búsqueda Binaria",
  "alerta_seguridad": true,
  "campo_requerido": null,
  "mensaje": "ALERTA DE SEGURIDAD: la memoria RAM no está ordenada por ningún campo todavía. ..."
}
```
Respuesta cuando sale Lineal:
```json
{
  "metodo_seleccionado": "Búsqueda Lineal",
  "alerta_seguridad": false,
  "campos_disponibles": ["id_estacion", "temperatura_promedio", "...", "velocidad_viento"],
  "mensaje": "Solicite al usuario que elija cualquiera de los 10 campos disponibles y el valor a buscar."
}
```

### `POST /api/fase3/ejecutar-busqueda`
Body:
```json
{ "metodo": "Búsqueda Binaria", "campo": "temperatura_promedio", "valor": 30 }
```
Respuesta:
```json
{
  "encontrado": true,
  "indice_ram": 4821,
  "registro": { ...10 campos... },
  "benchmarking": {
    "tiempo_ns": 7122,
    "comparaciones": 7,
    "mensaje": "Búsqueda 'Búsqueda Binaria' sobre el campo 'temperatura_promedio' completada en 7122 ns con 7 comparaciones."
  }
}
```
Si se solicita Búsqueda Binaria sobre un campo que **no** es el actualmente
ordenado en RAM, el servidor responde `409 Conflict` con el detalle del rechazo
por seguridad de memoria (no se ejecuta la búsqueda).

### `GET /api/estado`
```json
{
  "datos_cargados": true,
  "total_registros": 15000,
  "campo_actualmente_ordenado": "temperatura_promedio",
  "ultimo_metodo_usado": "Bucket Sort",
  "metodo_alfa": {"nombre": "Bucket Sort", "veces_ejecutado": 3},
  "historial_metodos": {"Bucket Sort": 3, "Merge Sort": 2, "...": "..."}
}
```

## 5. Decisiones técnicas relevantes

- **Quick Sort es iterativo** (pila explícita), así que no hay riesgo de
  `RecursionError` sin importar el tamaño del dataset. Merge Sort y Heap Sort
  son recursivos pero su profundidad máxima es ~`log2(15000) ≈ 14`, muy por
  debajo del límite de Python; aun así se eleva `sys.setrecursionlimit` por
  seguridad.
- **Radix Sort / Counting Sort** no comparan elementos entre sí (son
  algoritmos de distribución): sus `comparaciones` reportadas corresponden a
  las operaciones de determinar el máximo/mínimo del campo necesarias para
  construir el arreglo de conteo; sus `movimientos` son las escrituras reales
  en los arreglos auxiliares.
- **Bucket Sort** agrupa en una cubeta por cada grado entero de 10 a 45 °C y
  ordena cada cubeta con Insertion Sort manual.
- Un **swap** (intercambio de dos posiciones) se contabiliza como **2
  movimientos** (una escritura por cada posición), de forma consistente en
  Quick Sort y Heap Sort.
- El estado de la "RAM" (`estado.registros`, campo ordenado, historial de
  métodos) vive en memoria del proceso de `uvicorn`: si reinicias el servidor,
  vuelve a cero y deberás llamar a `/api/fase1/cargar` de nuevo.
- CORS está abierto (`allow_origins=["*"]`) para poder consumir la API desde
  cualquier frontend web de desarrollo.
