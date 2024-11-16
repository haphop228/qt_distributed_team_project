# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os
import tempfile
from mongo_service import save_matrix_to_db, get_matrix_from_db, find_matrices_by_user_id, find_matrix_by_filename,list_files_in_db, check_mongodb_availability  # Импортируем функцию из mongo_service.py

# Получаем URL из переменной окружения
SQLITE_URL = os.getenv("SQLITE_URL", "http://localhost:8000")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
app = FastAPI()

# Pydantic модель для получения данных
class UserInput(BaseModel):
    login: str
    
# Функция для проверки доступности серверов
async def check_server_availability(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True
    except httpx.RequestError:
        return False
    return False
    
@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_mongodb_availability()
    
    # Проверяем доступность MongoDB контейнера
    if not mongo_server_status:
        print("MongoDB server is unavailable")
        raise HTTPException(status_code=500, detail="MongoDB server is unavailable")
    if not sqlite_status:
        print("SQLite server is unavailable")
        raise HTTPException(status_code=500, detail="SQLite server is unavailable")
    # Если обе проверки прошли успешно
    
    print(f"status request, mongo db url - {MONGODB_URL}, sqlite url - {SQLITE_URL}")
    return {
        "status": "running",
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
    }

async def get_user_id(credentials: UserInput):
    print(f"Attempting request for user: {credentials.login}")
    # Формируем запрос к серверу SQLite для получения ID пользователя
    login_data = {"login": credentials.login}
    async with httpx.AsyncClient() as client:
        response = await client.post(SQLITE_URL + "/id_request", json=login_data)
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("user_id")
            print(f"User ID retrieved: {user_id}")
            return user_id
        else:
            print(f"Failed to retrieve user ID: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to retrieve user ID")

# API для сохранения матрицы от пользователя
@app.post("/save_matrix")
async def save_matrix(
    login: str = Form(...),  # Изменено: принимаем login через Form
    matrix_file: UploadFile = File(...)
):
    print(f'Trying to save matrix with path = {matrix_file.filename}, matrix name = {os.path.basename(matrix_file.filename)}')
    
    credentials = UserInput(login=login)  # Создаем объект UserInput из переданного login
    try:
        print(f"asking user id to save matrix")
        user_id = await get_user_id(credentials)
    except HTTPException:
        print("User with such id not found")
        raise HTTPException(status_code=400, detail="Invalid user id")
    
    # Сохранение загруженного файла .mtx
    try:
        print('trying to read matrix file')
        matrix_content = await matrix_file.read()  # Чтение содержимого файла
        
        # Извлечение имени файла из полного пути
        filename = os.path.basename(matrix_file.filename)  # Здесь отсекается путь, оставляя только имя файла
        
        await save_matrix_to_db(user_id=user_id, matrix_name=filename, matrix_content=matrix_content)  # Сохранение матрицы
        print(f"matrix = {filename} saved, user_id = {user_id}, user_login = {login}")
        return {"message": "Matrix saved successfully", "user_id": user_id}
    
    except HTTPException as e:
        # Обработка специфической HTTP ошибки
        print(f"HTTP error occurred while saving matrix: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail="Error saving matrix (HTTP error). Please try again later.")
    
    except Exception as e:
        # Общая обработка всех других исключений
        print(f"An unexpected error occurred while saving matrix: {e}")  # Логируем ошибку
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while saving the matrix (unknown): {e}")
    
    
# Создаем эндпоинт для получения имен и id матриц по id пользователя
@app.get("/get_matrix_by_user_id/{user_id}")
async def get_matrices_by_user_id(user_id: int):
    print(f"getting list of matrices by user_id = {user_id}")
    matrices = await find_matrices_by_user_id(user_id)
    if not matrices:
        print("ERROR: in getting list of matrices by user_id = {user_id}: No matrices found for this user")
        raise HTTPException(status_code=404, detail="No matrices found for this user")
    return {"matrices": matrices}

# Создаем эндпоинт для получения имен и id матриц по логину
@app.post("/get_matrix_names_by_user_login")
async def get_matrix_names_by_user_login(credentials: UserInput):
    user_id = await get_user_id(credentials)
    print(f"trying to return matrices by user_login = {credentials.login}, user_id = {user_id}")
    
    matrices = await find_matrices_by_user_id(user_id)
    if not matrices:
        raise HTTPException(status_code=404, detail="No matrices found for this user")
    
    print(f"List of matrices for user = {credentials.login} : {matrices}")
    return {"matrices": matrices}

@app.get("/list_files")
async def list_files():
    try:
        print('trying to list files')
        files = list_files_in_db()  # Убираем await здесь
        print(f'All listed files:\n {files}')
        return {"files": files}
    except Exception as e:
        print(f"An error occurred while listing files: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while listing files.")
    
@app.get("/get_matrix_by_matrix_id/{file_id}")
async def get_matrix_by_matrix_id(file_id: str):
    print(f'trying to get by matrix id = {file_id} from main server\n')
    matrix_data = await get_matrix_from_db(file_id)
    if not matrix_data:
        print('ERROR : if not matrix_data (get_matrix_by_matrix_id)')
        raise HTTPException(status_code=404, detail="Matrix not found (get_matrix_by_matrix_id)")
    
    # Создаем временный файл для матрицы
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mtx") as temp_file:
        temp_file.write(matrix_data)
        temp_file_path = temp_file.name
    print(f"sending matrix with if = {file_id}, name = {temp_file_path} to main server")
    # Возвращаем файл матрицы клиенту
    return FileResponse(temp_file_path, media_type="application/octet-stream", filename=f"{file_id}.mtx")
    
    
# Новый эндпоинт для получения файла матрицы по имени файла
# Возвращает матрицу как бинарный файл с использованием FileResponse
@app.get("/send_matrix_by_matrix_name")
async def send_matrix_by_matrix_name(matrix_name: str):
    # Ищем матрицу в базе данных по имени файла
    print(f'trying to get by matrix name = {matrix_name}\n')
    matrix = await find_matrix_by_filename(matrix_name)
    if not matrix:
        print(f"matrix named {matrix_name} not found!")
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    print("trying to save mtx data to temp file")
    # Сохраняем содержимое матрицы во временный файл для отправки
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mtx") as temp_file:
        temp_file.write(matrix.read())
        temp_file_path = temp_file.name

    print("sending response with matrix data - {matrix_name}")
    # Возвращаем файл в ответе
    return FileResponse(temp_file_path, media_type='application/octet-stream', filename=matrix_name)

