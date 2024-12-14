# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import os
from typing import List
import numpy as np
from logger import log  # Используем кастомный логгер
import time
import psutil  # Для мониторинга загрузки ресурсов
import asyncio

WORKER_NODE_CONTROL_SERVER_URL = os.getenv("WORKER_NODE_CONTROL_SERVER_URL")
app = FastAPI()

# Используем asyncio.Event для управления состоянием задачи
processing_task_active = False


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
    
    return [L, U]


def qr_decomposition(matrix: np.ndarray) -> List[np.ndarray]:
    """
    Выполняет QR-разложение матрицы без использования встроенных функций NumPy для QR.
    
    :param matrix: Прямоугольная матрица.
    :return: Список из двух матриц [Q, R], где Q - ортогональная, R - верхняя треугольная.
    """
    time.sleep(0.1)
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
    
    return [Q[:, :n], R[:n, :]]


def ldl_decomposition(matrix: np.ndarray) -> List[np.ndarray]:
    """
    Выполняет LDL-разложение симметричной положительно определённой матрицы.
    
    :param matrix: Симметричная положительно определённая матрица.
    :return: Список из двух матриц [L, D], где L - нижняя треугольная с единицами на диагонали, D - диагональная.
    """
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
    return [L, D_matrix, L.T]



# Маршрут для обработки запросов
@app.post("/process_task")
async def process_task(request: DecompositionRequest):
    
    # # Установка флага начала обработки
    global processing_task_active
    processing_task_active = True
    # Установка флага начала обработки

    
    log(f"Starting to process... {processing_task_active}")
    
    input_matrix = request.input_matrix
    algorithm = request.algorithm.lower()

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
        start_time = time.time()
        # TODO : что бы я не делал, эта задача полностью перекрывает любые запросы к серверу
        result = await asyncio.to_thread(decomposition_func, matrix)
        end_time = time.time()
        time_taken = end_time - start_time
        log(f"{algorithm.upper()} decomposition completed in {time_taken:.3f} seconds.", level="info")
    except Exception as e:
        processing_task_active = False
        log(f"Error during {algorithm.upper()} decomposition: {e}", level="error")
        raise HTTPException(status_code=500, detail=f"Error during decomposition: {e}")

    # Формирование ответа
    response = {
        "input_matrix": input_matrix,
        "algorithm": algorithm,
        "result": [block.tolist() for block in result],
        "time_taken": round(time_taken, 3)
    }

    processing_task_active = False
    log(f"Task ended...{processing_task_active}")
    return response

@app.get("/status")
async def get_status():
    """
    Возвращает состояние сервиса, включая загруженность CPU, использование памяти и статус.
    """
    global processing_task_active
    try:
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