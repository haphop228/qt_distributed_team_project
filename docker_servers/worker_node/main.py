# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os
from typing import List
import numpy as np
from logger import log  # Используем кастомный логгер
import time

WORKER_NODE_CONTROL_SERVER_URL = os.getenv("WORKER_NODE_CONTROL_SERVER_URL")
app = FastAPI()

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
@app.post("/decompose_matrix")
async def decompose_matrix(request: DecompositionRequest):
    """
    'input_matrix': [ [ 1,2 ] , [3, 4] ],\n
    'algorithm': 'lu',\n
    'result': [ [ [ 3, 1] , [ 3, 3] ] , [ [1,2],[3,2] ] ]\n
    'time_taken": 3.123\n
    """
    input_matrix = request.input_matrix
    algorithm = request.algorithm.lower()

    # Преобразование матрицы в формат numpy
    try:
        matrix = np.array(input_matrix)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square.")
    except Exception as e:
        log(f"Error processing input matrix: {e}", level="error")
        raise HTTPException(status_code=400, detail=f"Invalid input matrix: {e}")

    # Выбор функции разложения
    decomposition_func = {
        "lu": lu_decomposition,
        "qr": qr_decomposition,
        "ldl": ldl_decomposition
    }.get(algorithm)

    if decomposition_func is None:
        log(f"Unsupported algorithm: {algorithm}", level="error")
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {algorithm}")

    # Выполнение разложения с измерением времени
    try:
        log(f"Starting {algorithm.upper()} decomposition.")
        start_time = time.time()
        result = decomposition_func(matrix)
        end_time = time.time()
        time_taken = end_time - start_time
        log(f"{algorithm.upper()} decomposition completed in {time_taken:.3f} seconds.", level="info")
    except Exception as e:
        log(f"Error during {algorithm.upper()} decomposition: {e}", level="error")
        raise HTTPException(status_code=500, detail=f"Error during decomposition: {e}")

    # Формирование ответа
    response = {
        "input_matrix": input_matrix,
        "algorithm": algorithm,
        "result": [block.tolist() for block in result],
        "time_taken": round(time_taken, 3)
    }
    return response


# Function to check server availability
async def check_server_availability(url: str):
    try:
        async with httpx.AsyncClient() as client:
            log(f"Checking server availability for URL: {url}")
            response = await client.get(url)
            if response.status_code == 200:
                log(f"Server {url} is available.")
                return True
            else:
                log(f"Server {url} responded with status code {response.status_code}.")
                return False
    except httpx.RequestError as e:
        log(f"Failed to check server availability for {url}: {e}", level="error")
        return False
    
@app.get("/status")
async def get_status():
    log("Service status checked.")
    return {
        "status": "running",
        "WORKER_CONTROL_URL": WORKER_NODE_CONTROL_SERVER_URL
    }