"""
Implementación manual (Python puro) de los algoritmos de ordenamiento y búsqueda
exigidos por la rúbrica. Prohibido usar sorted()/.sort()/Pandas/NumPy para ordenar
o buscar: todo se hace con comparaciones e intercambios explícitos, instrumentados
con contadores de `comparaciones` y `movimientos`, y medidos con
time.perf_counter_ns().

Convenciones de conteo usadas en todo el módulo (documentadas para la bitácora):
- `comparaciones`: cada vez que se evalúa una relación de orden (<, >, <=, >=, ==)
  entre dos claves, o -en los algoritmos de distribución (Radix/Counting)- cada
  vez que se extrae/evalúa un dígito o se determina un mínimo/máximo necesario
  para construir el arreglo de distribución.
- `movimientos`: cada escritura efectiva de un registro en una lista auxiliar,
  en un bucket, o cada intercambio (swap) cuenta como 2 movimientos (una
  escritura por cada posición involucrada).
"""
import time


# ---------------------------------------------------------------------------
# ALGORITMOS DE ORDENAMIENTO
# ---------------------------------------------------------------------------

def radix_sort(records, field):
    """Radix Sort LSD para enteros no negativos (pensado para id_estacion)."""
    t0 = time.perf_counter_ns()
    comparaciones = 0
    movimientos = 0
    arr = records[:]
    n = len(arr)

    if n == 0:
        return arr, 0, 0, time.perf_counter_ns() - t0

    max_val = arr[0][field]
    for i in range(1, n):
        comparaciones += 1
        if arr[i][field] > max_val:
            max_val = arr[i][field]

    exp = 1
    while max_val // exp > 0:
        arr, moved = _counting_sort_by_digit(arr, exp, field)
        movimientos += moved
        exp *= 10

    t1 = time.perf_counter_ns()
    return arr, comparaciones, movimientos, (t1 - t0)


def _counting_sort_by_digit(arr, exp, field):
    n = len(arr)
    output = [None] * n
    count = [0] * 10
    movimientos = 0

    for i in range(n):
        digito = (arr[i][field] // exp) % 10
        count[digito] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    for i in range(n - 1, -1, -1):
        digito = (arr[i][field] // exp) % 10
        output[count[digito] - 1] = arr[i]
        movimientos += 1
        count[digito] -= 1

    return output, movimientos


def counting_sort(records, field):
    """Counting Sort clásico, basado en el rango [min, max] del campo."""
    t0 = time.perf_counter_ns()
    comparaciones = 0
    movimientos = 0
    n = len(records)

    if n == 0:
        return records[:], 0, 0, time.perf_counter_ns() - t0

    min_val = records[0][field]
    max_val = records[0][field]
    for i in range(1, n):
        comparaciones += 1
        if records[i][field] < min_val:
            min_val = records[i][field]
        comparaciones += 1
        if records[i][field] > max_val:
            max_val = records[i][field]

    rango = max_val - min_val + 1
    count = [0] * rango

    for i in range(n):
        count[records[i][field] - min_val] += 1
        movimientos += 1

    for i in range(1, rango):
        count[i] += count[i - 1]

    output = [None] * n
    for i in range(n - 1, -1, -1):
        idx = records[i][field] - min_val
        output[count[idx] - 1] = records[i]
        movimientos += 1
        count[idx] -= 1

    t1 = time.perf_counter_ns()
    return output, comparaciones, movimientos, (t1 - t0)


def bucket_sort(records, field, rango_min=10, rango_max=45):
    """Bucket Sort agrupando por grados enteros de temperatura (10 a 45 °C).
    Cada cubeta se ordena internamente con Insertion Sort manual."""
    t0 = time.perf_counter_ns()
    comparaciones = 0
    movimientos = 0

    num_buckets = rango_max - rango_min + 1
    buckets = [[] for _ in range(num_buckets)]

    for rec in records:
        val = rec[field]
        idx = val - rango_min
        if idx < 0:
            idx = 0
        elif idx >= num_buckets:
            idx = num_buckets - 1
        buckets[idx].append(rec)
        movimientos += 1

    output = []
    for bucket in buckets:
        for i in range(1, len(bucket)):
            actual = bucket[i]
            valor_actual = actual[field]
            j = i - 1
            while j >= 0:
                comparaciones += 1
                if bucket[j][field] > valor_actual:
                    bucket[j + 1] = bucket[j]
                    movimientos += 1
                    j -= 1
                else:
                    break
            bucket[j + 1] = actual
            movimientos += 1
        output.extend(bucket)

    t1 = time.perf_counter_ns()
    return output, comparaciones, movimientos, (t1 - t0)


def quick_sort(records, field):
    """Quick Sort iterativo (pila explícita, sin límite de recursión) con
    pivote de mediana-de-tres."""
    t0 = time.perf_counter_ns()
    arr = records[:]
    comparaciones = 0
    movimientos = 0

    pila = [(0, len(arr) - 1)]
    while pila:
        low, high = pila.pop()
        if low < high:
            pivot_idx, c, m = _partition(arr, low, high, field)
            comparaciones += c
            movimientos += m
            pila.append((low, pivot_idx - 1))
            pila.append((pivot_idx + 1, high))

    t1 = time.perf_counter_ns()
    return arr, comparaciones, movimientos, (t1 - t0)


def _partition(arr, low, high, field):
    comparaciones = 0
    movimientos = 0

    mid = (low + high) // 2
    a, b, c = arr[low][field], arr[mid][field], arr[high][field]
    comparaciones += 3
    if (a <= b <= c) or (c <= b <= a):
        pivot_idx = mid
    elif (b <= a <= c) or (c <= a <= b):
        pivot_idx = low
    else:
        pivot_idx = high

    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    movimientos += 2

    pivot = arr[high][field]
    i = low - 1
    for j in range(low, high):
        comparaciones += 1
        if arr[j][field] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
            movimientos += 2

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    movimientos += 2

    return i + 1, comparaciones, movimientos


def merge_sort(records, field):
    """Merge Sort recursivo clásico (profundidad ~log2(n), sin riesgo real
    de límite de recursión para 15,000 registros)."""
    t0 = time.perf_counter_ns()
    contadores = {"comparaciones": 0, "movimientos": 0}

    def _ordenar(sub):
        if len(sub) <= 1:
            return sub
        mid = len(sub) // 2
        izquierda = _ordenar(sub[:mid])
        derecha = _ordenar(sub[mid:])
        return _merge(izquierda, derecha)

    def _merge(izquierda, derecha):
        resultado = []
        i = j = 0
        while i < len(izquierda) and j < len(derecha):
            contadores["comparaciones"] += 1
            if izquierda[i][field] <= derecha[j][field]:
                resultado.append(izquierda[i])
                i += 1
            else:
                resultado.append(derecha[j])
                j += 1
            contadores["movimientos"] += 1
        while i < len(izquierda):
            resultado.append(izquierda[i])
            i += 1
            contadores["movimientos"] += 1
        while j < len(derecha):
            resultado.append(derecha[j])
            j += 1
            contadores["movimientos"] += 1
        return resultado

    resultado = _ordenar(records[:])
    t1 = time.perf_counter_ns()
    return resultado, contadores["comparaciones"], contadores["movimientos"], (t1 - t0)


def heap_sort(records, field):
    """Heap Sort clásico (max-heap) con heapify recursivo."""
    t0 = time.perf_counter_ns()
    arr = records[:]
    n = len(arr)
    contadores = {"comparaciones": 0, "movimientos": 0}

    def heapify(size, root):
        mayor = root
        izq = 2 * root + 1
        der = 2 * root + 2

        if izq < size:
            contadores["comparaciones"] += 1
            if arr[izq][field] > arr[mayor][field]:
                mayor = izq
        if der < size:
            contadores["comparaciones"] += 1
            if arr[der][field] > arr[mayor][field]:
                mayor = der

        if mayor != root:
            arr[root], arr[mayor] = arr[mayor], arr[root]
            contadores["movimientos"] += 2
            heapify(size, mayor)

    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)

    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        contadores["movimientos"] += 2
        heapify(i, 0)

    t1 = time.perf_counter_ns()
    return arr, contadores["comparaciones"], contadores["movimientos"], (t1 - t0)


# ---------------------------------------------------------------------------
# ALGORITMOS DE BÚSQUEDA
# ---------------------------------------------------------------------------

def linear_search(records, field, valor):
    """Búsqueda secuencial sobre cualquiera de los 10 campos."""
    t0 = time.perf_counter_ns()
    comparaciones = 0
    indice_encontrado = -1

    for idx, rec in enumerate(records):
        comparaciones += 1
        if rec[field] == valor:
            indice_encontrado = idx
            break

    t1 = time.perf_counter_ns()
    return indice_encontrado, comparaciones, (t1 - t0)


def binary_search(records, field, valor):
    """Búsqueda binaria. PRECONDICIÓN (validada por la capa de negocio):
    `records` debe estar ordenado ascendentemente por `field`."""
    t0 = time.perf_counter_ns()
    comparaciones = 0
    low, high = 0, len(records) - 1
    indice_encontrado = -1

    while low <= high:
        mid = (low + high) // 2
        comparaciones += 1
        if records[mid][field] == valor:
            indice_encontrado = mid
            break
        comparaciones += 1
        if records[mid][field] < valor:
            low = mid + 1
        else:
            high = mid - 1

    t1 = time.perf_counter_ns()
    return indice_encontrado, comparaciones, (t1 - t0)
