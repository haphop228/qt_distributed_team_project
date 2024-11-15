from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import httpx
import os
import numpy as np
from scipy.io import mmread,mmwrite
from io import BytesIO
from pydantic import BaseModel

app = FastAPI()
TEMP_DIR = "temp_mtx_files"

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
    
def remove_file(file_path: str):
    """
    Удаляет временный файл.
    """
    try:
        os.remove(file_path)
        print(f"Temporary file {file_path} removed.")
    except OSError as e:
        print(f"Error removing file {file_path}: {e}")

@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    return {
        "status": "running",
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
    }

def convert_np_array_to_matrix_market(matrix: np.ndarray, file_path: str):
    """
    Конвертирует numpy.array в формат Matrix Market (.mtx) и сохраняет в файл.

    Args:
        matrix (np.ndarray): Матрица в формате numpy.array.
        file_path (str): Путь к файлу для сохранения в формате .mtx.

    Raises:
        ValueError: Если входная матрица не двухмерная.
        IOError: Если не удается сохранить файл.
    """
    if not isinstance(matrix, np.ndarray):
        raise ValueError("Input must be a numpy.ndarray.")

    if matrix.ndim != 2:
        raise ValueError("Input matrix must be two-dimensional.")

    try:
        mmwrite(file_path, matrix)
        print(f"Matrix successfully saved in Matrix Market format to {file_path}")
        return file_path
    except Exception as e:
        raise IOError(f"Failed to write matrix to file: {e}") from e

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
                    matrix = mmread(BytesIO(matrix_data))
                    # Проверяем, является ли матрица разреженной (если да, преобразуем в плотную)
                    if isinstance(matrix, np.ndarray):
                        print("Matrix is already a dense numpy array")
                    else:
                        print("Matrix is sparse, converting to dense numpy array")
                        matrix = matrix.toarray()  # Преобразуем разреженную матрицу в плотную
                    print("Matrix converted to np.array")
                    return matrix
                except Exception as e:
                    print(f"Failed to parse the matrix file (mtx -> np array): {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to parse the matrix file: {e}") from e
            else:
                print("Matrix not found on MongoDB server")
                raise HTTPException(status_code=response.status_code, detail="Matrix not found on MongoDB server")
    except httpx.RequestError as e:
        print("Failed to connect to MongoDB server")
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
        print("Matrix must be square to calculate its inverse")
        raise ValueError("Matrix must be square to calculate its inverse.")

    # Проверка на необратимость
    determinant = np.linalg.det(matrix)
    if determinant == 0:
        print("Matrix is not invertible (determinant is zero).")
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
        print(f"error in getting matrix from MONGO : {e, e.detail}")
        raise HTTPException(status_code=e.status_code, detail=f"Failed to fetch the matrix: {e.detail}")

    # Вычисление обратной матрицы
    try:
        print(f"Trying to get matrix^-1 with calculate_invertible_matrix")
        inverse_matrix = calculate_invertible_matrix(matrix)
    except ValueError as e:
        print(f"error in np.linalg.inv = {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    print("matrix^-1 computed successfully!")
    # Возвращение результата в формате JSON (списки для сериализации)
    return {
        "original_matrix": matrix.tolist(),
        "inverse_matrix": inverse_matrix.tolist()
    }
    