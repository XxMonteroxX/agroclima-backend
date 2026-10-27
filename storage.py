"""
Capa de negocio: mantiene el estado en RAM (lista de diccionarios cargada desde
el CSV), orquesta los algoritmos de algorithms.py, escribe las bitácoras con el
formato exacto exigido y calcula el "Método Alfa".
"""
import csv
import time
from pathlib import Path

from algorithms import (
    radix_sort,
    counting_sort,
    bucket_sort,
    quick_sort,
    merge_sort,
    heap_sort,
    linear_search,
    binary_search,
)

BASE_DIR = Path(__file__).parent

DATASET_PATH = BASE_DIR / "dataset_agroclimatico_15000.csv"
BITACORA_ORDEN_PATH = BASE_DIR / "bitacora_ordenacion.txt"
BITACORA_BUSQUEDA_PATH = BASE_DIR / "bitacora_busqueda.txt"
BACKUP_PATH = BASE_DIR / "registros_ordenados_backup.csv"

CAMPOS = [
    "id_estacion",
    "temperatura_promedio",
    "fecha_registro",
    "estado",
    "municipio",
    "humedad_relativa",
    "precipitacion_mm",
    "tipo_cultivo_predominante",
    "presion_atmosferica",
    "velocidad_viento",
]

CAMPOS_ENTEROS = {"id_estacion", "temperatura_promedio", "fecha_registro"}
CAMPOS_FLOTANTES = {"humedad_relativa", "precipitacion_mm", "presion_atmosferica", "velocidad_viento"}

CAMPOS_CLAVE = {
    1: "id_estacion",
    2: "temperatura_promedio",
    3: "fecha_registro",
}

ALGORITMOS_POR_CAMPO = {
    "id_estacion": ["Radix Sort", "Counting Sort"],
    "temperatura_promedio": ["Bucket Sort"],
    "fecha_registro": ["Quick Sort", "Merge Sort", "Heap Sort"],
}

_FUNCIONES_ORDENAMIENTO = {
    "Radix Sort": radix_sort,
    "Counting Sort": counting_sort,
    "Bucket Sort": bucket_sort,
    "Quick Sort": quick_sort,
    "Merge Sort": merge_sort,
    "Heap Sort": heap_sort,
}


class EstadoRAM:
    """Representa el estado único y global de la 'RAM' simulada del sistema."""

    def __init__(self):
        self.registros = []
        self.cargado = False
        self.campo_actualmente_ordenado = None
        self.ultimo_metodo = None
        self.primera_ordenacion_hecha = False
        self.conteo_metodos = {}
        self.tiempo_carga_ns = None


estado = EstadoRAM()


def castear_valor(campo, valor):
    """Convierte el valor recibido por JSON al tipo nativo del campo para que
    las comparaciones (==, <, >) sean correctas."""
    if campo in CAMPOS_ENTEROS:
        return int(valor)
    if campo in CAMPOS_FLOTANTES:
        return float(valor)
    return str(valor)


def cargar_csv():
    """Lee dataset_agroclimatico_15000.csv completo a una lista de diccionarios
    en RAM, midiendo el tiempo de carga en nanosegundos."""
    t0 = time.perf_counter_ns()
    registros = []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            registros.append({
                "id_estacion": int(fila["id_estacion"]),
                "temperatura_promedio": int(fila["temperatura_promedio"]),
                "fecha_registro": int(fila["fecha_registro"]),
                "estado": fila["estado"],
                "municipio": fila["municipio"],
                "humedad_relativa": float(fila["humedad_relativa"]),
                "precipitacion_mm": float(fila["precipitacion_mm"]),
                "tipo_cultivo_predominante": fila["tipo_cultivo_predominante"],
                "presion_atmosferica": float(fila["presion_atmosferica"]),
                "velocidad_viento": float(fila["velocidad_viento"]),
            })

    t1 = time.perf_counter_ns()
    tiempo_ns = t1 - t0

    estado.registros = registros
    estado.cargado = True
    estado.campo_actualmente_ordenado = None
    estado.ultimo_metodo = None
    estado.tiempo_carga_ns = tiempo_ns

    return tiempo_ns, len(registros)


def ejecutar_ordenamiento(campo, metodo):
    """Ejecuta el algoritmo indicado sobre estado.registros, actualiza el
    estado de la RAM, escribe la bitácora y genera el backup si aplica."""
    funcion = _FUNCIONES_ORDENAMIENTO[metodo]
    ordenados, comparaciones, movimientos, tiempo_ns = funcion(estado.registros, campo)

    estado.registros = ordenados
    estado.campo_actualmente_ordenado = campo
    estado.ultimo_metodo = metodo
    estado.conteo_metodos[metodo] = estado.conteo_metodos.get(metodo, 0) + 1

    linea = (
        f"Se ordenaron 15,000 registros por el campo [{campo}] usando el método "
        f"[{metodo}] en [{tiempo_ns}] nanosegundos. Comparaciones: [{comparaciones}], "
        f"Asignaciones/Movimientos de Memoria: [{movimientos}]\n"
    )
    with open(BITACORA_ORDEN_PATH, "a", encoding="utf-8") as f:
        f.write(linea)

    if not estado.primera_ordenacion_hecha:
        guardar_backup()
        estado.primera_ordenacion_hecha = True

    return comparaciones, movimientos, tiempo_ns


def guardar_backup():
    """Respaldo de la primera ordenación: los 15,000 registros ordenados en
    registros_ordenados_backup.csv."""
    with open(BACKUP_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(estado.registros)


def metodo_alfa():
    """El método de ordenamiento más ejecutado hasta el momento ('Método Alfa')."""
    if not estado.conteo_metodos:
        return None, 0
    nombre_alfa = max(estado.conteo_metodos, key=lambda k: estado.conteo_metodos[k])
    return nombre_alfa, estado.conteo_metodos[nombre_alfa]


def ejecutar_busqueda(metodo, campo, valor):
    """Ejecuta Búsqueda Binaria o Lineal sobre estado.registros, valida las
    condiciones de memoria física y escribe la bitácora de búsqueda."""
    valor_casteado = castear_valor(campo, valor)

    if metodo == "Búsqueda Binaria":
        if estado.campo_actualmente_ordenado != campo:
            raise ValueError(
                f"ALERTA DE SEGURIDAD DE MEMORIA: la RAM no está ordenada por el campo "
                f"'{campo}'. Campo actualmente ordenado: "
                f"{estado.campo_actualmente_ordenado or 'ninguno'}. "
                f"La Búsqueda Binaria fue rechazada."
            )
        idx, comparaciones, tiempo_ns = binary_search(estado.registros, campo, valor_casteado)
    elif metodo == "Búsqueda Lineal":
        idx, comparaciones, tiempo_ns = linear_search(estado.registros, campo, valor_casteado)
    else:
        raise ValueError(f"Método de búsqueda no reconocido: '{metodo}'")

    encontrado = idx != -1
    registro = estado.registros[idx] if encontrado else None

    linea = (
        f"Se realizó la búsqueda en 15,000 registros por el campo [{campo}] usando "
        f"el método de búsqueda [{metodo}] en [{tiempo_ns}] nanosegundos. "
        f"Comparaciones: [{comparaciones}]\n"
    )
    with open(BITACORA_BUSQUEDA_PATH, "a", encoding="utf-8") as f:
        f.write(linea)

    return encontrado, idx, registro, comparaciones, tiempo_ns
