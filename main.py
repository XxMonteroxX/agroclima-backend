"""
PROYECTO 1: Sistema de Monitoreo Agroclimático de Cultivos de Maíz y Aguacate
Backend FastAPI con servicio de Frontend integrado para despliegue web.

Ejecutar en local:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import random
import sys
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import storage
from storage import ALGORITMOS_POR_CAMPO, CAMPOS, CAMPOS_CLAVE, estado

# Límite de recursión por seguridad en algoritmos
sys.setrecursionlimit(10000)

app = FastAPI(
    title="Sistema de Monitoreo Agroclimático - Maíz y Aguacate",
    description=(
        "API académica que procesa en RAM 15,000 registros agroclimáticos de "
        "Jalisco, Michoacán, Sinaloa y Veracruz, implementando manualmente "
        "Radix Sort, Counting Sort, Bucket Sort, Quick Sort, Merge Sort, "
        "Heap Sort, Búsqueda Binaria y Búsqueda Lineal."
    ),
    version="1.0.0",
)

# Soporte CORS para permitir peticiones web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BusquedaPayload(BaseModel):
    metodo: str
    campo: str
    valor: Any


# ---------------------------------------------------------------------------
# FASE 1: CARGA A MEMORIA RAM
# ---------------------------------------------------------------------------

@app.post("/api/fase1/cargar")
def cargar():
    if not storage.DATASET_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No se encontró el archivo '{storage.DATASET_PATH.name}' junto "
                f"a main.py. Coloque el dataset de 15,000 registros en esa ruta."
            ),
        )

    tiempo_ns, total = storage.cargar_csv()

    return {
        "mensaje": (
            f"Se realizó la carga de los 15,000 registros con sus 10 columnas a la "
            f"estructura [ArrayList/Lista de Objetos] y le tomó [{tiempo_ns}] "
            f"nanosegundos completar la acción."
        ),
        "tiempo_ns": tiempo_ns,
        "total_registros": total,
        "muestra_primeros_30": estado.registros[:30],
        "muestra_ultimos_30": estado.registros[-30:],
        "primeros_30": estado.registros[:30],
        "ultimos_30": estado.registros[-30:],
    }


# ---------------------------------------------------------------------------
# FASE 2: DISPARADOR ALEATORIO DE ORDENAMIENTO
# ---------------------------------------------------------------------------

@app.post("/api/fase2/disparador-ordenamiento")
def disparador_ordenamiento():
    if not estado.cargado:
        raise HTTPException(
            status_code=400,
            detail="Los datos no han sido cargados en RAM. Ejecute antes /api/fase1/cargar.",
        )

    clave = random.choice(list(CAMPOS_CLAVE.keys()))
    campo = CAMPOS_CLAVE[clave]
    metodo = random.choice(ALGORITMOS_POR_CAMPO[campo])

    comparaciones, movimientos, tiempo_ns = storage.ejecutar_ordenamiento(campo, metodo)
    alfa_nombre, alfa_conteo = storage.metodo_alfa()

    return {
        "campo_seleccionado": {"clave": clave, "nombre": campo},
        "campo": campo,
        "clave": clave,
        "metodo_asignado": metodo,
        "metodo": metodo,
        "tiempo_ns": tiempo_ns,
        "comparaciones": comparaciones,
        "movimientos": movimientos,
        "mensaje_benchmarking": (
            f"Ordenamiento '{metodo}' sobre el campo '{campo}' completado en "
            f"{tiempo_ns} ns, con {comparaciones} comparaciones y {movimientos} "
            f"movimientos/asignaciones de memoria."
        ),
        "metodo_alfa": {
            "nombre": alfa_nombre,
            "veces_ejecutado": alfa_conteo,
            "historial_completo": dict(estado.conteo_metodos),
        },
        "muestra_primeros_30": estado.registros[:30],
        "muestra_ultimos_30": estado.registros[-30:],
        "primeros_30": estado.registros[:30],
        "ultimos_30": estado.registros[-30:],
    }


# ---------------------------------------------------------------------------
# FASE 3: DISPARADOR ALEATORIO DE BÚSQUEDA
# ---------------------------------------------------------------------------

@app.get("/api/fase3/disparador-busqueda")
def disparador_busqueda():
    if not estado.cargado:
        raise HTTPException(
            status_code=400,
            detail="Los datos no han sido cargados en RAM. Ejecute antes /api/fase1/cargar.",
        )

    metodo = random.choice(["Búsqueda Binaria", "Búsqueda Lineal"])

    if metodo == "Búsqueda Binaria":
        if estado.campo_actualmente_ordenado is None:
            return {
                "metodo_seleccionado": metodo,
                "metodo": metodo,
                "alerta_seguridad": True,
                "campo_requerido": None,
                "campo": None,
                "mensaje": (
                    "ALERTA DE SEGURIDAD: la memoria RAM no está ordenada por ningún "
                    "campo todavía. La Búsqueda Binaria requiere ejecutar primero "
                    "/api/fase2/disparador-ordenamiento."
                ),
            }
        return {
            "metodo_seleccionado": metodo,
            "metodo": metodo,
            "alerta_seguridad": False,
            "campo_requerido": estado.campo_actualmente_ordenado,
            "campo": estado.campo_actualmente_ordenado,
            "mensaje": (
                f"Solicite al usuario el valor a buscar para el campo obligatorio "
                f"'{estado.campo_actualmente_ordenado}' (único campo actualmente "
                f"ordenado en RAM)."
            ),
        }

    return {
        "metodo_seleccionado": metodo,
        "metodo": metodo,
        "alerta_seguridad": False,
        "campo": random.choice(CAMPOS),
        "campos_disponibles": CAMPOS,
        "mensaje": "Solicite al usuario que elija cualquiera de los 10 campos disponibles y el valor a buscar.",
    }


# ---------------------------------------------------------------------------
# FASE 3: EJECUCIÓN DE BÚSQUEDA
# ---------------------------------------------------------------------------

@app.post("/api/fase3/ejecutar-busqueda")
def ejecutar_busqueda(payload: BusquedaPayload):
    if not estado.cargado:
        raise HTTPException(status_code=400, detail="Los datos no han sido cargados en RAM.")

    if payload.campo not in CAMPOS:
        raise HTTPException(
            status_code=422,
            detail=f"Campo '{payload.campo}' no válido. Campos disponibles: {CAMPOS}",
        )

    if payload.metodo not in ("Búsqueda Binaria", "Búsqueda Lineal"):
        raise HTTPException(
            status_code=422,
            detail="Método inválido. Use 'Búsqueda Binaria' o 'Búsqueda Lineal'.",
        )

    try:
        encontrado, idx, registro, comparaciones, tiempo_ns = storage.ejecutar_busqueda(
            payload.metodo, payload.campo, payload.valor
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "encontrado": encontrado,
        "indice_ram": idx,
        "indice": idx,
        "registro": registro,
        "tiempo_ns": tiempo_ns,
        "comparaciones": comparaciones,
        "benchmarking": {
            "tiempo_ns": tiempo_ns,
            "comparaciones": comparaciones,
            "mensaje": (
                f"Búsqueda '{payload.metodo}' sobre el campo '{payload.campo}' "
                f"completada en {tiempo_ns} ns con {comparaciones} comparaciones."
            ),
        },
    }


# ---------------------------------------------------------------------------
# ESTADO GENERAL Y MONTAJE FRONTEND
# ---------------------------------------------------------------------------

@app.get("/api/estado")
def obtener_estado():
    alfa_nombre, alfa_conteo = storage.metodo_alfa()
    return {
        "datos_cargados": estado.cargado,
        "total_registros": len(estado.registros),
        "campo_actualmente_ordenado": estado.campo_actualmente_ordenado,
        "ultimo_metodo_usado": estado.ultimo_metodo,
        "metodo_alfa": {"nombre": alfa_nombre, "veces_ejecutado": alfa_conteo},
        "historial_metodos": dict(estado.conteo_metodos),
    }


# Montar carpeta static para CSS, JS y otros recursos
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Servir la interfaz web principal directamente en la raíz "/"
@app.get("/")
def raiz():
    ruta_index = os.path.join("static", "index.html")
    if os.path.exists(ruta_index):
        return FileResponse(ruta_index)
    return {
        "proyecto": "Sistema de Monitoreo Agroclimático - Maíz y Aguacate",
        "documentacion": "/docs",
        "aviso": "Coloque index.html dentro de la carpeta static/ para ver la interfaz.",
    }