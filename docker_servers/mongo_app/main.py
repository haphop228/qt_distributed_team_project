# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os
import tempfile
from mongo_service import (
    save_matrix_to_db,
    get_matrix_from_db,
    find_matrices_by_user_id,
    find_matrix_by_filename,
    list_files_in_db,
    check_mongodb_availability,
)  # Импортируем функции из mongo_service.py
from logger import log  # Используем кастомный логгер

# Получаем URL из переменных окружения
SQLITE_URL = os.getenv("SQLITE_URL", "http://localhost:8000")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
app = FastAPI()

# Pydantic модель для получения данных
class UserInput(BaseModel):
    login: str

# Функция для проверки доступности серверов
async def check_server_availability(url: str):
    log(f"Checking server availability at {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                log(f"Server at {url} is available")
                return True
    except httpx.RequestError as e:
        log(f"Failed to reach server at {url}: {e}", level="error")
        return False
    log(f"Server at {url} is unavailable", level="error")
    return False

@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_mongodb_availability()

    if not mongo_server_status:
        log("MongoDB server is unavailable", level="error")
        raise HTTPException(status_code=500, detail="MongoDB server is unavailable")
    if not sqlite_status:
        log("SQLite server is unavailable", level="error")
        raise HTTPException(status_code=500, detail="SQLite server is unavailable")

    log(f"Status check: MongoDB ({MONGODB_URL}), SQLite ({SQLITE_URL})")
    return {
        "status": "running",
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
    }

async def get_user_id(credentials: UserInput):
    log(f"Requesting user ID for login: {credentials.login}")
    login_data = {"login": credentials.login}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SQLITE_URL}/id_request", json=login_data)
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("user_id")
            log(f"User ID retrieved for login {credentials.login}: {user_id}")
            return user_id
        else:
            log(f"Failed to retrieve user ID for login {credentials.login}: {response.text}", level="error")
            raise HTTPException(status_code=response.status_code, detail="Failed to retrieve user ID")

@app.post("/save_matrix")
async def save_matrix(
    login: str = Form(...),
    matrix_file: UploadFile = File(...),
):
    log(f"Saving matrix: {matrix_file.filename} for user login: {login}")

    credentials = UserInput(login=login)
    try:
        user_id = await get_user_id(credentials)
        log(f"User ID {user_id} obtained for login {login}")
    except HTTPException as e:
        log(f"Failed to get user ID for login {login}: {e.detail}", level="error")
        raise HTTPException(status_code=400, detail="Invalid user ID")

    try:
        matrix_content = await matrix_file.read()
        filename = os.path.basename(matrix_file.filename)

        await save_matrix_to_db(user_id=user_id, matrix_name=filename, matrix_content=matrix_content)
        log(f"Matrix '{filename}' saved for user_id {user_id}, login {login}")
        return {"message": "Matrix saved successfully", "user_id": user_id}

    except HTTPException as e:
        log(f"HTTP error during matrix save: {e.detail}", level="error")
        raise
    except Exception as e:
        log(f"Unexpected error during matrix save: {e}", level="error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@app.get("/get_matrix_by_user_id/{user_id}")
async def get_matrices_by_user_id(user_id: int):
    log(f"Fetching matrices for user_id: {user_id}")
    matrices = await find_matrices_by_user_id(user_id)
    if not matrices:
        log(f"No matrices found for user_id: {user_id}", level="error")
        raise HTTPException(status_code=404, detail="No matrices found for this user")
    log(f"Matrices found for user_id {user_id}: {matrices}")
    return {"matrices": matrices}

@app.post("/get_matrix_names_by_user_login")
async def get_matrix_names_by_user_login(credentials: UserInput):
    user_id = await get_user_id(credentials)
    log(f"Fetching matrices for login: {credentials.login}, user_id: {user_id}")
    matrices = await find_matrices_by_user_id(user_id)
    if not matrices:
        log(f"No matrices found for login {credentials.login}, user_id {user_id}", level="error")
        raise HTTPException(status_code=404, detail="No matrices found for this user")
    log(f"Matrices for login {credentials.login}: {matrices}")
    return {"matrices": matrices}

@app.get("/list_files")
async def list_files():
    log("Fetching list of files from database")
    try:
        files = list_files_in_db()
        log(f"Files retrieved: {files}")
        return {"files": files}
    except Exception as e:
        log(f"Error fetching files: {e}", level="error")
        raise HTTPException(status_code=500, detail="Error fetching files.")

@app.get("/get_matrix_by_matrix_id/{file_id}")
async def get_matrix_by_matrix_id(file_id: str):
    log(f"Fetching matrix by file_id: {file_id}")
    matrix_data = await get_matrix_from_db(file_id)
    if not matrix_data:
        log(f"Matrix with file_id {file_id} not found", level="error")
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mtx") as temp_file:
        temp_file.write(matrix_data)
        temp_file_path = temp_file.name
    log(f"Matrix with file_id {file_id} sent as file: {temp_file_path}")
    return FileResponse(temp_file_path, media_type="application/octet-stream", filename=f"{file_id}.mtx")

@app.get("/send_matrix_by_matrix_name")
async def send_matrix_by_matrix_name(matrix_name: str):
    log(f"Fetching matrix by name: {matrix_name}")
    matrix = await find_matrix_by_filename(matrix_name)
    if not matrix:
        log(f"Matrix named {matrix_name} not found", level="error")
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mtx") as temp_file:
        temp_file.write(matrix.read())
        temp_file_path = temp_file.name
    log(f"Matrix {matrix_name} sent as file: {temp_file_path}")
    return FileResponse(temp_file_path, media_type="application/octet-stream", filename=matrix_name)
