# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import os
import queue
from typing import List
import numpy as np
from logger import log  # Используем кастомный логгер
import time
import psutil  # Для мониторинга загрузки ресурсов
import asyncio

WORKER_NODE_CONTROL_SERVER_URL = os.getenv("WORKER_NODE_CONTROL_SERVER_URL")
app = FastAPI()

# Используем для управления состоянием задачи
processing_task_active = False
task_lock = threading.Lock()  # Для потокобезопасного доступа к переменной
# Очередь для хранения результата
result_queue = queue.Queue()

algorithm_gl = ''
matrix_name_gl = ''
time_taken_gl = 0

# Модель данных для входного JSON
class DecompositionRequest(BaseModel):
    input_matrix: List[List[float]]
    algorithm: str


def lu_decomposition(matrix: np.ndarray) -> List[np.ndarray]:
    """
    Выполняет LU-разложение матрицы без использования встроенных функций NumPy для LU.
    
    :param matrix: Квадратная матрица.
    :return: Список из двух матриц [L, U], где L - нижняя треугольная, U - верхняя треугольная.
    """
    global processing_task_active, time_taken_gl
    start = time.time()
    time.sleep(0.1)
    n = matrix.shape[0]
    L = np.zeros((n, n))
    U = np.zeros((n, n))
    
    for i in range(n):
        # Вычисление элементов матрицы U
        for j in range(i, n):
            U[i, j] = matrix[i, j] - sum(L[i, k] * U[k, j] for k in range(i))
        
        # Вычисление элементов матрицы L
        for j in range(i, n):
            if i == j:
                L[j, i] = 1  # Диагональные элементы L равны 1
            else:
                L[j, i] = (matrix[j, i] - sum(L[j, k] * U[k, i] for k in range(i))) / U[i, i]
    
    with task_lock:
        processing_task_active = False
    end = time.time()
    time_taken_gl = (end - start)
    result_queue.put([L, U])
    


def qr_decomposition(matrix: np.ndarray) -> List[np.ndarray]:
    """
    Выполняет QR-разложение матрицы без использования встроенных функций NumPy для QR.
    
    :param matrix: Прямоугольная матрица.
    :return: Список из двух матриц [Q, R], где Q - ортогональная, R - верхняя треугольная.
    """
    log(f"QR decompos function started!")
    global processing_task_active, time_taken_gl
    start = time.time()
    time.sleep(6)
    m, n = matrix.shape
    Q = np.zeros((m, m))  # Ортогональная матрица
    R = np.zeros((m, n))  # Верхняя треугольная матрица
    A = matrix.copy()
    
    for i in range(n):
        # Вычисляем норму столбца
        norm = np.linalg.norm(A[:, i])
        
        # Вектор Q[:, i] - нормированный столбец
        Q[:, i] = A[:, i] / norm
        
        # Обновляем матрицу R
        for j in range(i, n):
            R[i, j] = np.dot(Q[:, i], A[:, j])
        
        # Обновляем матрицу A, вычитая проекцию
        for j in range(i + 1, n):
            A[:, j] -= Q[:, i] * R[i, j]
            
    with task_lock:
        processing_task_active = False
        
    end = time.time()
    time_taken_gl = (end - start)
    result_queue.put([Q[:, :n], R[:n, :]])
    


def ldl_decomposition(matrix: np.ndarray) -> List[np.ndarray]:
    """
    Выполняет LDL-разложение симметричной положительно определённой матрицы.
    
    :param matrix: Симметричная положительно определённая матрица.
    :return: Список из двух матриц [L, D], где L - нижняя треугольная с единицами на диагонали, D - диагональная.
    """
    global processing_task_active, time_taken_gl
    start = time.time()
    time.sleep(0.1)
    if not np.allclose(matrix, matrix.T):
        raise ValueError("Matrix must be symmetric for LDL decomposition.")

    n = matrix.shape[0]
    L = np.eye(n)  # Нижняя треугольная матрица с единицами на диагонали
    D = np.zeros(n)  # Диагональная матрица (как вектор)

    for i in range(n):
        # Вычисляем диагональный элемент D
        D[i] = matrix[i, i] - sum(L[i, k] ** 2 * D[k] for k in range(i))

        # Вычисляем элементы нижней треугольной матрицы L
        for j in range(i + 1, n):
            L[j, i] = (matrix[j, i] - sum(L[j, k] * L[i, k] * D[k] for k in range(i))) / D[i]

    D_matrix = np.diag(D)  # Преобразуем в диагональную матрицу для удобства
    
    with task_lock:
        processing_task_active = False
        
    end = time.time()
    time_taken_gl = (end - start)
    result_queue.put([L, D_matrix, L.T])



# Маршрут для обработки запросов
@app.post("/process_task")
async def process_task(request: DecompositionRequest):
    
    # Очистка очереди перед запуском новой задачи
    while not result_queue.empty():
        result_queue.get()
    
    # # Установка флага начала обработки
    global processing_task_active, matrix_name_gl, algorithm_gl
    
    with task_lock:
        if processing_task_active:
            raise HTTPException(status_code=400, detail="Task is already running.")
        log(f"makin processing_task_active = True from process_task")
        processing_task_active = True
    
    log(f"Starting to process... {processing_task_active}")
    
    input_matrix = request.input_matrix
    algorithm = request.algorithm.lower()
    algorithm_gl = algorithm
    matrix_name_gl = input_matrix

    # Преобразование матрицы в формат numpy
    try:
        matrix = np.array(input_matrix)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square.")
    except Exception as e:
        processing_task_active = False
        log(f"Error processing input matrix: {e}", level="error")
        raise HTTPException(status_code=400, detail=f"Invalid input matrix: {e}")

    # Выбор функции разложения
    decomposition_func = {
        "lu": lu_decomposition,
        "qr": qr_decomposition,
        "ldl": ldl_decomposition
    }.get(algorithm)

    if decomposition_func is None:
        processing_task_active = False
        log(f"Unsupported algorithm: {algorithm}", level="error")
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {algorithm}")

    # Выполнение разложения с измерением времени
    try:
        log(f"Starting {algorithm.upper()} decomposition in a separate thread.")
        # TODO : что бы я не делал, эта задача полностью перекрывает любые запросы к серверу
        # Запуск задачи в отдельном потоке
        thread = threading.Thread(target=decomposition_func,args=(matrix,), daemon=True)
        thread.start()
    except Exception as e:
        processing_task_active = False
        log(f"Error during {algorithm.upper()} decomposition: {e}", level="error")
        raise HTTPException(status_code=500, detail=f"Error during decomposition: {e}")

    return {"message": "Task started"}


@app.get("/get_result")
def get_result():
    """
    Возвращает результат выполнения задачи, если он доступен.
    """
    global processing_task_active, matrix_name_gl, algorithm_gl, time_taken_gl
    
    if result_queue.empty() or processing_task_active == True:
        raise HTTPException(status_code=404, detail=f"Result not ready yet - {result_queue.empty() , processing_task_active}")

    # Извлекаем результат из очереди
    result = result_queue.get()

        # Формирование ответа
    response = {
        "input_matrix": matrix_name_gl,
        "algorithm": algorithm_gl,
        "result": [block.tolist() for block in result],
        "time_taken": round(time_taken_gl, 3)
    }

    log(f"Task ended...{processing_task_active}")
    processing_task_active = False
    return response


@app.get("/status")
async def get_status():
    """
    Возвращает состояние сервиса, включая загруженность CPU, использование памяти и статус.
    """
    global processing_task_active
    try:
        with task_lock:
            # Получение данных о CPU и памяти
            cpu_usage = psutil.cpu_percent(interval=0.1)  # Загрузка CPU в процентах
            memory_info = psutil.virtual_memory()  # Информация о памяти
            memory_usage = memory_info.percent  # Использование памяти в процентах
            # Проверка выполнения задачи
            is_running = processing_task_active
            
            # Формирование ответа
            status_info = {
                "is_running": is_running,
                "WORKER_CONTROL_URL": WORKER_NODE_CONTROL_SERVER_URL,
                "load": {
                    "cpu": cpu_usage,
                    "memory": memory_usage
                }
            }
            log(f"Status check: {status_info}")
            return status_info
    except Exception as e:
        log(f"Error retrieving status: {e}", level="error")
        raise HTTPException(status_code=500, detail=f"Error retrieving status: {e}")