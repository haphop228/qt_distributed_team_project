from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import httpx
import os
import numpy as np
from scipy.io import mmread, mmwrite
from io import BytesIO
from pydantic import BaseModel
from logger import get_logger  

# Инициализация логгера
logger = get_logger("matrix_operations")

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
            logger.info(f"Checking server availability for URL: {url}")
            response = await client.get(url)
            if response.status_code == 200:
                logger.info(f"Server {url} is available.")
                return True
            else:
                logger.warning(f"Server {url} responded with status code {response.status_code}.")
                return False
    except httpx.RequestError as e:
        logger.error(f"Failed to check server availability for {url}: {e}")
        return False
    
def remove_file(file_path: str):
    """
    Удаляет временный файл.
    """
    try:
        os.remove(file_path)
        logger.info(f"Temporary file {file_path} removed.")
    except OSError as e:
        logger.error(f"Error removing file {file_path}: {e}")

@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    logger.info("Service status checked.")
    return {
        "status": "running",
        "SQLITE_URL": SQLITE_URL,
        "MONGO_SERVER_URL": MONGO_SERVER_URL,
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status
    }

def convert_np_array_to_matrix_market(matrix: np.ndarray, file_path: str):
    """
    Конвертирует numpy.array в формат Matrix Market (.mtx) и сохраняет в файл.
    """
    if not isinstance(matrix, np.ndarray):
        raise ValueError("Input must be a numpy.ndarray.")

    if matrix.ndim != 2:
        raise ValueError("Input matrix must be two-dimensional.")

    try:
        mmwrite(file_path, matrix)
        logger.info(f"Matrix successfully saved in Matrix Market format to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to write matrix to file: {e}")
        raise IOError(f"Failed to write matrix to file: {e}") from e

@app.post("/get_matrix_by_name")
async def get_matrix_by_name(matrix_name: str):
    """
    Получение матрицы по имени с MongoDB сервера и конвертация в numpy.array.
    """
    mongo_endpoint = f"{MONGO_SERVER_URL}/send_matrix_by_matrix_name"
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Requesting matrix {matrix_name} from MongoDB at {mongo_endpoint}")
            response = await client.get(mongo_endpoint, params={"matrix_name": matrix_name})
            if response.status_code == 200:
                logger.info(f"Matrix {matrix_name} retrieved successfully from MongoDB.")
                matrix_data = response.content
                try:
                    matrix = mmread(BytesIO(matrix_data))
                    if isinstance(matrix, np.ndarray):
                        logger.info("Matrix is already a dense numpy array.")
                    else:
                        logger.info("Matrix is sparse, converting to dense numpy array.")
                        matrix = matrix.toarray()
                    return matrix
                except Exception as e:
                    logger.error(f"Failed to parse the matrix file: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to parse the matrix file: {e}") from e
            else:
                logger.warning(f"Matrix not found on MongoDB server: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Matrix not found on MongoDB server")
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to MongoDB server: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB server") from e

@app.post("/print_matrix_by_matrix_name")
async def print_matrix_by_matrix_name(request: MatrixRequest):
    """
    Получение и печать матрицы по имени.
    """
    matrix_name = request.matrix_name
    try:
        matrix = await get_matrix_by_name(matrix_name)
        logger.info(f"Matrix '{matrix_name}':\n{np.round(matrix, 1)}")
        return {"message": f"Matrix '{matrix_name}' printed to the terminal successfully"}
    except HTTPException as e:
        logger.error(f"HTTP error while printing matrix: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e

def calculate_invertible_matrix(matrix: np.array) -> np.array:
    """
    Вычисляет обратную матрицу для заданной матрицы.
    """
    logger.info("Calculating inverse matrix.")
    if matrix.shape[0] != matrix.shape[1]:
        logger.error("Matrix must be square to calculate its inverse.")
        raise ValueError("Matrix must be square to calculate its inverse.")

    determinant = np.linalg.det(matrix)
    if determinant == 0:
        logger.error("Matrix is not invertible (determinant is zero).")
        raise ValueError("Matrix is not invertible (determinant is zero).")
    
    inverse_matrix = np.linalg.inv(matrix)
    logger.info("Inverse matrix calculated successfully.")
    return inverse_matrix

@app.post("/calculate_invertible_matrix_by_matrix_name")
async def calculate_invertible_matrix_by_matrix_name(request: MatrixRequest):
    """
    Вычисляет и возвращает обратную матрицу по имени матрицы.
    """
    matrix_name = request.matrix_name
    try:
        matrix = await get_matrix_by_name(matrix_name)
    except HTTPException as e:
        logger.error(f"Error fetching matrix: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=f"Failed to fetch the matrix: {e.detail}")

    try:
        inverse_matrix = calculate_invertible_matrix(matrix)
    except ValueError as e:
        logger.error(f"Matrix inversion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("Matrix inversion completed.")
    return {
        "original_matrix": matrix.tolist(),
        "inverse_matrix": inverse_matrix.tolist()
    }
