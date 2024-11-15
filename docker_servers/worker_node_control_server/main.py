from fastapi import FastAPI, HTTPException
import httpx
import os
import numpy as np
from scipy.io import mmread
from io import BytesIO
from pydantic import BaseModel

app = FastAPI()

# Load configurations from environment variables
SQLITE_URL = os.getenv("SQLITE_URL")
MONGO_SERVER_URL = os.getenv("MONGO_SERVER_URL")
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL")

class MatrixRequest(BaseModel):
    matrix_name: str

# Function to check server availability
async def check_server_availability(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.status_code == 200
    except httpx.RequestError:
        return False

@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    main_server_status = await check_server_availability(f"{MAIN_SERVER_URL}/status")
    return {
        "status": "running",
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
        "main_server_status": main_server_status
    }
@app.post("/get_matrix_by_name")
async def get_matrix_by_name(matrix_name: str):
    """
    Получение матрицы по имени с MongoDB сервера и конвертация в numpy.array.
    """
    mongo_endpoint = f"{MONGO_SERVER_URL}/send_matrix_by_matrix_name"
    try:
        async with httpx.AsyncClient() as client:
            print(f"Trying to get matrix {matrix_name} from MongoDB")
            response = await client.get(mongo_endpoint, params={"matrix_name": matrix_name})
            if response.status_code == 200:
                matrix_data = response.content
                # Конвертируем данные из Matrix Market в numpy.array
                try:
                    matrix = mmread(BytesIO(matrix_data)).toarray()
                    print("Matrix converted to np.array")
                    return matrix
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to parse the matrix file: {e}") from e
            else:
                raise HTTPException(status_code=response.status_code, detail="Matrix not found on MongoDB server")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB server") from e

@app.post("/print_matrix_by_matrix_name")
async def print_matrix_by_matrix_name(request: MatrixRequest):
    """
    Получение и печать матрицы по имени.
    """
    matrix_name = request.matrix_name
    try:
        # Получаем матрицу в формате numpy.array
        matrix = await get_matrix_by_name(matrix_name)
        print(f"Matrix '{matrix_name}':\n", np.round(matrix, 1))  # Округляем до 1 знака после запятой
        return {"message": f"Matrix '{matrix_name}' printed to the terminal successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e
    
def calculate_invertible_matrix(matrix: np.array) -> np.array:
    """
    Вычисляет обратную матрицу для заданной матрицы.
    
    :param matrix: Входная матрица в формате numpy.array.
    :return: Обратная матрица в формате numpy.array.
    :raises ValueError: Если матрица не квадратная или необратимая.
    """
    print(f'Trying to get invertible with np.linalg.inv')
    # Проверка на квадратную форму
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be square to calculate its inverse.")

    # Проверка на необратимость
    determinant = np.linalg.det(matrix)
    if determinant == 0:
        raise ValueError("Matrix is not invertible (determinant is zero).")
    
    # Вычисление обратной матрицы
    inverse_matrix = np.linalg.inv(matrix)
    return inverse_matrix

@app.post("/calculate_invertible_matrix_by_matrix_name")
async def calculate_invertible_matrix_by_matrix_name(request: MatrixRequest):
    """
    Вычисляет и возвращает обратную матрицу по имени матрицы.
    
    Args:
        request (MatrixRequest): Объект, содержащий имя матрицы (matrix_name).
    
    Returns:
        dict: Оригинальная и обратная матрица в виде списков (для JSON-сериализации).
        
    запрос POST:
    -H "Content-Type: application/json" -d '{"matrix_name": "Matrix_FIDAP005.mtx"}'

    Ответ сервера:
    
        "original_matrix": [
            [2, 1],
            [5, 3]
        ],
        "inverse_matrix": [
            [3.0, -1.0],
            [-5.0, 2.0]
        ]
    
    \nОтвет при ошибке:\n
    {
    "detail": "Failed to fetch the matrix: Matrix not found on MongoDB server"
    }
    
    {
    "detail": "Matrix is not invertible (determinant is zero)."
    }
    """
    matrix_name = request.matrix_name
    # Получение матрицы по имени
    try:
        print(f"Trying to get {matrix_name} with await get_matrix_by_name")
        matrix = await get_matrix_by_name(matrix_name)  # Возвращает матрицу как np.array
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Failed to fetch the matrix: {e.detail}")

    # Вычисление обратной матрицы
    try:
        print(f"Trying to get matrix^-1 with calculate_invertible_matrix")
        inverse_matrix = calculate_invertible_matrix(matrix)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    print("matrix^-1 computed successfully!")
    # Возвращение результата в формате JSON (списки для сериализации)
    return {
        "original_matrix": matrix.tolist(),
        "inverse_matrix": inverse_matrix.tolist()
    }
