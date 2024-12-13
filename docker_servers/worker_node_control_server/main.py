from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import asyncio
import httpx
import os
import numpy as np
from scipy.io import mmread, mmwrite
from io import BytesIO
from pydantic import BaseModel
from logger import log  # Используем кастомный логгер

app = FastAPI()
TEMP_DIR = "temp_mtx_files"

# Load configurations from environment variables
SQLITE_URL = os.getenv("SQLITE_URL")
MONGO_SERVER_URL = os.getenv("MONGO_SERVER_URL")
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL")

WORKER_NODE_1_URL = os.getenv("WORKER_NODE_1_URL")
WORKER_NODE_2_URL = os.getenv("WORKER_NODE_2_URL")
WORKER_NODE_3_URL = os.getenv("WORKER_NODE_3_URL")

WORKER_NODE_URLS = {
    "WORKER_NODE_1": WORKER_NODE_1_URL,
    "WORKER_NODE_2": WORKER_NODE_2_URL,
    "WORKER_NODE_3": WORKER_NODE_3_URL,
}

class MatrixRequest(BaseModel):
    matrix_name: str

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
    
def remove_file(file_path: str):
    """
    Удаляет временный файл.
    """
    try:
        os.remove(file_path)
        log(f"Temporary file {file_path} removed.")
    except OSError as e:
        log(f"Error removing file {file_path}: {e}", level="error")

@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    worker1_node_status = await check_server_availability(f"{WORKER_NODE_1_URL}/status")
    worker2_node_status = await check_server_availability(f"{WORKER_NODE_2_URL}/status")
    worker3_node_status = await check_server_availability(f"{WORKER_NODE_3_URL}/status")
    log("Service status checked.")
    return {
        "status": "running",
        "SQLITE_URL": SQLITE_URL,
        "MONGO_SERVER_URL": MONGO_SERVER_URL,
        "WORKER_NODE_1_URL": WORKER_NODE_1_URL,
        "WORKER_NODE_2_URL": WORKER_NODE_2_URL,
        "WORKER_NODE_3_URL": WORKER_NODE_3_URL,
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
        "worker1_node_status" : worker1_node_status,
        "worker2_node_status" : worker2_node_status,
        "worker3_node_status" : worker3_node_status,
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
        log(f"Matrix successfully saved in Matrix Market format to {file_path}")
        return file_path
    except Exception as e:
        log(f"Failed to write matrix to file: {e}", level="error")
        raise IOError(f"Failed to write matrix to file: {e}") from e

@app.post("/get_matrix_by_name")
async def get_matrix_by_name(matrix_name: str):
    """
    Получение матрицы по имени с MongoDB сервера и конвертация в numpy.array.
    """
    mongo_endpoint = f"{MONGO_SERVER_URL}/get_matrix_by_matrix_name"
    try:
        async with httpx.AsyncClient() as client:
            log(f"Requesting matrix {matrix_name} from MongoDB at {mongo_endpoint}")
            response = await client.get(mongo_endpoint, params={"matrix_name": matrix_name})
            if response.status_code == 200:
                log(f"Matrix {matrix_name} retrieved successfully from MongoDB.")
                matrix_data = response.content
                try:
                    matrix = mmread(BytesIO(matrix_data))
                    if isinstance(matrix, np.ndarray):
                        log("Matrix is already a dense numpy array.")
                    else:
                        log("Matrix is sparse, converting to dense numpy array.")
                        matrix = matrix.toarray()
                    return matrix
                except Exception as e:
                    log(f"Failed to parse the matrix file: {e}", level="error")
                    raise HTTPException(status_code=500, detail=f"Failed to parse the matrix file: {e}") from e
            else:
                log(f"Matrix not found on MongoDB server: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Matrix not found on MongoDB server")
    except httpx.RequestError as e:
        log(f"Failed to connect to MongoDB server: {e}", level="error")
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB server") from e

@app.post("/print_matrix_by_matrix_name")
async def print_matrix_by_matrix_name(request: MatrixRequest):
    """
    Получение и печать матрицы по имени.
    """
    matrix_name = request.matrix_name
    try:
        matrix = await get_matrix_by_name(matrix_name)
        log(f"Matrix '{matrix_name}'")
        return {"message": f"Matrix '{matrix_name}' printed to the terminal successfully"}
    except HTTPException as e:
        log(f"HTTP error while printing matrix: {e.detail}", level="error")
        raise e
    except Exception as e:
        log(f"Unexpected error: {e}", level="error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e
    
    
# Функция отправки задачи на worker node
async def send_task_to_worker_node(matrix: np.array, algorithm: str, retries: int = 5, retry_delay: float = 1.0):
    """
    Отправляет задачу на наименее загруженный worker node. Если все узлы заняты, повторяет попытку.

    Args:
        matrix (np.array): Матрица для обработки.
        algorithm (str): Алгоритм обработки (например, "lu", "qr", "ldl").
        retries (int): Количество попыток.
        retry_delay (float): Задержка между попытками (в секундах).

    Returns:
        dict: Ответ от выбранного worker node.

    Raises:
        HTTPException: Если ни один узел не доступен после всех попыток.
    """
    for attempt in range(retries):
        log(f"Attempt {attempt + 1} of {retries} to send task.", level="info")

        worker_statuses = []
        async with httpx.AsyncClient() as client:
            for worker_name, worker_url in WORKER_NODE_URLS.items():
                if not worker_url:
                    log(f"URL for {worker_name} is not defined.", level="error")
                    continue

                try:
                    log(f"Checking status of {worker_name} at {worker_url}.", level="info")
                    response = await client.get(f"{worker_url}/status")
                    if response.status_code == 200:
                        status = response.json()
                        log(f"Status of {worker_name}: {status}", level="info")
                        worker_statuses.append((worker_name, worker_url, status))
                    else:
                        log(f"Failed to get status of {worker_name}. HTTP {response.status_code}: {response.text}", level="error")
                except Exception as e:
                    log(f"Error checking status of {worker_name}: {e}", level="error")

        # Фильтрация свободных узлов
        free_workers = [
            (name, url, status)
            for name, url, status in worker_statuses
            if not status.get("running", True)
        ]

        if free_workers:
            # Сортировка свободных узлов по нагрузке
            free_workers.sort(key=lambda x: (x[2]["load"]["cpu"], x[2]["load"]["memory"]))
            selected_worker = free_workers[0]
            worker_name, worker_url, _ = selected_worker

            # Отправка задачи на выбранный узел
            try:
                data_to_send = {
                    "input_matrix": matrix.tolist(),
                    "algorithm": algorithm,
                }
                log(f"Sending task to {worker_name} at {worker_url}.", level="info")
                response = await client.post(f"{worker_url}/process_task", json=data_to_send)

                if response.status_code == 200:
                    log(f"Task successfully sent to {worker_name}. Response: {response.json()}", level="info")
                    return response.json()
                else:
                    log(f"Failed to process task on {worker_name}. HTTP {response.status_code}: {response.text}", level="error")
                    return response.json()
            except Exception as e:
                log(f"Error sending task to {worker_name}: {e}", level="error")
                HTTPException(status_code=503, detail=f"Error sending task to {worker_name}: {e}")

        # Если все узлы заняты, ждем перед повторной попыткой
        log(f"All workers are busy. Retrying in {retry_delay} seconds...", level="warning")
        await asyncio.sleep(retry_delay)

    # Если после всех попыток узел не найден
    log("No available worker nodes after maximum retries.", level="error")
    raise HTTPException(status_code=503, detail="No available worker nodes.")


async def send_task_to_worker_nodes(matrix: np.array, destination: dict,):
    """
    Отправляет матрицу на обработку воркер-нодам с учетом указанного алгоритма.

    :param matrix: Матрица для обработки.
    :param destination: Словарь с информацией о нодах и алгоритмах:
        {
            "WORKER_NODE_1": [WORKER_NODE_1_URL, 'LU'],
            "WORKER_NODE_2": [WORKER_NODE_2_URL, 'QR'],
            "WORKER_NODE_3": [WORKER_NODE_3_URL, 'LDL'],
        }
    :return: Словарь с ответами от нод или ошибками.
    """
    responses = {}
    log("Starting task distribution to worker nodes.", level="info")

    async with httpx.AsyncClient() as client:
        tasks = []

        for worker_name, (worker_url, algorithm) in destination.items():
            if not worker_url:
                log(f"URL for {worker_name} is not defined.", level="error")
                responses[worker_name] = {"error": f"URL for {worker_name} is not defined."}
                continue

            # Подготовка данных для отправки
            data_to_send = {
                "input_matrix": matrix.tolist(),  # Преобразуем матрицу в список для передачи через JSON
                "algorithm": algorithm,    # Алгоритм обработки (LU, QR, LDL и т.д.)
            }
            log(f"Preparing to send matrix to {worker_name} at {worker_url} using algorithm {algorithm}.", level="info")

            # Создание задачи отправки POST-запроса
            task = client.post(f"{worker_url}/process_task", json=data_to_send)
            tasks.append((worker_name, task))

        # Выполнение всех запросов
        for worker_name, task in tasks:
            try:
                response = await task
                if response.status_code == 200:
                    log(f"Successfully sent matrix to {worker_name}. Response: {response.json()}", level="info")
                    responses[worker_name] = response.json()
                else:
                    log(f"Failed to process matrix on {worker_name}. HTTP {response.status_code}: {response.text}", level="error")
                    responses[worker_name] = {"error": f" -_- HTTP {response.status_code}"}
            except Exception as e:
                log(f"Failed to connect to {worker_name} at {destination[worker_name][0]}: {e}", level="error")
                responses[worker_name] = {"error": str(e)}

    log(f"Final responses: {responses}", level="debug")

    log("Task distribution to worker nodes completed.", level="info")
    return responses


def process_response(response: dict) -> dict:
    """
    Обрабатывает и форматирует ответ от воркер-ноды.

    :param response: response с информацией от функции send_task_to_worker_nodes.
    :return: JSON-ответ.
    """
    log("Processing responses from worker nodes.", level="info")
    formatted_responses = {}

    for worker, result in response.items():
        if "error" in result:
            # Если произошла ошибка, логируем и добавляем в итоговый словарь
            log(f"Worker {worker} reported an error: {result['error']}", level="error")
            formatted_responses[worker] = {
                "status": "error",
                "message": "Internal Server Error"
            }
        else:
            # Обрабатываем успешный результат
            log(f"Processing successful response from {worker}.", level="info")
            input_matrix = result.get("input_matrix", [])
            algorithm = result.get("algorithm", "unknown")
            computed_result = result.get("result", [])
            time_taken = result.get("time_taken", "unknown")

            log(f"Worker {worker} used algorithm '{algorithm}' and completed in {time_taken} seconds.", level="info")
            
            formatted_responses[worker] = {
                "status": "success",
                "algorithm": algorithm,
                "time_taken": time_taken,
                "result": computed_result
            }

            # Форматируем красивый вывод в консоль
            print("\n" + "-" * 50)
            print(f"WORKER: {worker}")
            print(f"Algorithm: {algorithm}")
            print(f"Time Taken: {time_taken} seconds")
            # print("Input Matrix:")
            # for row in input_matrix:
            #     print(row)
            # print("\nResult:")
            # for block in computed_result:
            #     print("Block:")
            #     for row in block:
            #         print(row)
            print("-" * 50)
    
    log(f"Responses \n\n{formatted_responses}\n\n")

    log("Responses processing completed.", level="info")
    
    return formatted_responses

# MAIN METHOD
@app.post("/calculate_all_decompositions_of_matrix_by_matrix_name")
async def calculate_invertible_matrix_by_matrix_name(request: MatrixRequest):
    """
    Вычисляет и возвращает все разложения матрицы по имени матрицы.
    """
    matrix_name = request.matrix_name
    try:
        matrix = await get_matrix_by_name(matrix_name)
    except HTTPException as e:
        log(f"Error fetching matrix: {e.detail}", level="error")
        raise HTTPException(status_code=e.status_code, detail=f"Failed to fetch the matrix: {e.detail}")

    try:
        log('Sending matrix to worker nodes')
        result = await send_task_to_worker_nodes(matrix, WORKER_NODE_URLS)
    except ValueError as e:
        log(f"Matrix inversion error: {e}", level="error")
        raise HTTPException(status_code=400, detail=str(e))

    try:
        log('Making result beautiful!')
        final_result = process_response(response=result)
    except Exception as e:
        log(f"Error on worker node : {e}", level='error')
        
        
    log("Matrix inversion completed.")
    
    return final_result



def calculate_invertible_matrix(matrix: np.array) -> np.array:
    """
    Вычисляет обратную матрицу для заданной матрицы.
    """
    log("Calculating inverse matrix.")
    if matrix.shape[0] != matrix.shape[1]:
        log("Matrix must be square to calculate its inverse.", level="error")
        raise ValueError("Matrix must be square to calculate its inverse.")

    determinant = np.linalg.det(matrix)
    if determinant == 0:
        log("Matrix is not invertible (determinant is zero).", level="error")
        raise ValueError("Matrix is not invertible (determinant is zero).")
    
    
    inverse_matrix = np.linalg.inv(matrix)
    log("Inverse matrix calculated successfully.")
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
        log(f"Error fetching matrix: {e.detail}", level="error")
        raise HTTPException(status_code=e.status_code, detail=f"Failed to fetch the matrix: {e.detail}")

    try:
        inverse_matrix = calculate_invertible_matrix(matrix)
    except ValueError as e:
        log(f"Matrix inversion error: {e}", level="error")
        raise HTTPException(status_code=400, detail=str(e))

    log("Matrix inversion completed.")
    return {
        "original_matrix": matrix.tolist(),
        "inverse_matrix": inverse_matrix.tolist()
    }
