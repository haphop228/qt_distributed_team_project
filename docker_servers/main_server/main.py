from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import os
from logger import log  # Используем кастомный логгер

app = FastAPI()

# Загрузка конфигураций
SQLITE_URL = os.getenv("SQLITE_URL")
MONGO_SERVER_URL = os.getenv("MONGO_SERVER_URL")
WORKER_CONTROL_SERVER_URL = os.getenv("WORKER_CONTROL_SERVER_URL")

# Pydantic модель для регистрации пользователя
class RegisterCredentials(BaseModel):
    name: str
    email: str
    login: str
    password: str

# Pydantic модель для входа
class LoginCredentials(BaseModel):
    login: str
    password: str

# Pydantic модель для получения id
class IdCredentials(BaseModel):
    login: str

class MatrixName(BaseModel):
    matrix_name: str

# Функция для проверки доступности серверов
async def check_server_availability(url: str):
    try:
        log(f"Checking server availability: {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                log(f"Server available: {url}")
                return True
    except httpx.RequestError as e:
        log(f"Request error while checking {url}: {e}", level="error")
    return False

# API для входа пользователя
@app.post("/login")
async def login_user(credentials: LoginCredentials):
    log(f"User login attempt: {credentials.login}")
    if not await check_server_availability(f"{SQLITE_URL}/status"):
        log(f"SQLite server unavailable: {SQLITE_URL}/status", level="error")
        raise HTTPException(status_code=503, detail="SQLite сервер недоступен")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SQLITE_URL}/login", json=credentials.dict())

    if response.status_code != 200:
        log(f"Login failed for user {credentials.login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка входа")

    log(f"User {credentials.login} logged in successfully.")
    return response.json()

# API для регистрации пользователя
@app.post("/register")
async def register(credentials: RegisterCredentials):
    log(f"User registration attempt: {credentials.login}")
    if not await check_server_availability(f"{SQLITE_URL}/status"):
        log(f"SQLite server unavailable: {SQLITE_URL}/status", level="error")
        raise HTTPException(status_code=503, detail="SQLite сервер недоступен")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SQLITE_URL}/register", json=credentials.model_dump())

    if response.status_code != 200:
        log(f"Registration failed for user {credentials.login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка регистрации")

    log(f"User {credentials.login} registered successfully.")
    return response.json()

# API для сохранения матрицы
@app.post("/save_matrix")
async def save_matrix(login: str = Form(...), matrix_file: UploadFile = File(...)):
    log(f"Saving matrix {matrix_file.filename} for user {login}")
    if not await check_server_availability(f"{MONGO_SERVER_URL}/status"):
        log(f"MongoDB server unavailable: {MONGO_SERVER_URL}/status", level="error")
        raise HTTPException(status_code=503, detail="MongoDB сервер недоступен")

    async with httpx.AsyncClient() as client:
        files = {'matrix_file': (matrix_file.filename, await matrix_file.read())}
        data = {'login': login}
        response = await client.post(f"{MONGO_SERVER_URL}/save_matrix", data=data, files=files)

    if response.status_code != 200:
        log(f"Matrix save failed for user {login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка при сохранении матрицы")

    log(f"Matrix {matrix_file.filename} saved successfully for user {login}.")
    return response.json()

# API для получения списка матриц
@app.post("/get_matrix_names_by_user_login")
async def get_matrix_names_by_user_login(credentials: IdCredentials):
    log(f"Fetching matrix list for user {credentials.login}")
    if not await check_server_availability(f"{MONGO_SERVER_URL}/status") or not await check_server_availability(f"{SQLITE_URL}/status"):
        log(f"One or more servers unavailable: {MONGO_SERVER_URL}, {SQLITE_URL}", level="error")
        raise HTTPException(status_code=503, detail="Один из серверов недоступен")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MONGO_SERVER_URL}/get_matrix_names_by_user_login", json=credentials.model_dump())

    if response.status_code != 200:
        log(f"Failed to fetch matrices for user {credentials.login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка при получении списка матриц")

    log(f"Matrices for user {credentials.login} fetched successfully.")
    return response.json()

# API для вычисления обратимой матрицы
@app.post("/calculate_invertible_matrix_by_matrix_name")
async def calculate_invertible_matrix_by_matrix_name(credentials: MatrixName):
    matrix_name = credentials.matrix_name
    log(f"Calculating invertible matrix for {matrix_name}")

    if not await check_server_availability(f"{MONGO_SERVER_URL}/status") or not await check_server_availability(f"{WORKER_CONTROL_SERVER_URL}/status"):
        log(f"Required servers unavailable: {MONGO_SERVER_URL}, {WORKER_CONTROL_SERVER_URL}", level="error")
        raise HTTPException(status_code=503, detail="Необходимые серверы недоступны")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{WORKER_CONTROL_SERVER_URL}/calculate_invertible_matrix_by_matrix_name", json=credentials.model_dump())

    if response.status_code != 200:
        error_details = response.json() if response.headers.get("content-type") == "application/json" else response.text
        log(f"Calculation failed for {matrix_name}: {error_details}", level="error")
        raise HTTPException(status_code=response.status_code, detail=error_details)

    log(f"Invertible matrix for {matrix_name} calculated successfully.")
    return response.json()

# API для получения статуса
@app.get("/status")
async def get_status():
    log("Fetching server status")
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    worker_control_server_status = await check_server_availability(f"{WORKER_CONTROL_SERVER_URL}/status")

    log(f"Server statuses: SQLite={sqlite_status}, MongoDB={mongo_server_status}, WorkerControl={worker_control_server_status}")
    return {
        "status": "running",
        "SQLITE_URL": SQLITE_URL,
        "MONGO_SERVER_URL": MONGO_SERVER_URL,
        "WORKER_CONTROL_SERVER_URL": WORKER_CONTROL_SERVER_URL,
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
        "worker_control_server_status": worker_control_server_status
    }
