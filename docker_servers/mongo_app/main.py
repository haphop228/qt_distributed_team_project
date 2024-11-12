# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import os
from mongo_service import save_matrix_to_db, get_matrix_from_db, find_matrices_by_user_id, find_matrix_by_filename,list_files_in_db, check_mongodb_availability  # Импортируем функцию из mongo_service.py

# Получаем URL из переменной окружения
SQLITE_URL = os.getenv("SQLITE_URL_ID_REQUEST", "http://localhost:8000/id_request")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
app = FastAPI()

# Pydantic модель для получения данных
class UserInput(BaseModel):
    login: str

async def get_user_id(credentials: UserInput):
    print(f"Attempting request for user: {credentials.login}")

    # Формируем запрос к серверу SQLite для получения ID пользователя
    login_data = {"login": credentials.login}
    print(f'\nlogin_data = {login_data}\n')
    async with httpx.AsyncClient() as client:
        response = await client.post(SQLITE_URL, json=login_data)
        print(f'\response = {response}\n')
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("user_id")
            print(f"!!! User ID retrieved: {user_id}")
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
    credentials = UserInput(login=login)  # Создаем объект UserInput из переданного login
    try:
        user_id = await get_user_id(credentials)
    except HTTPException:
        print("User with such id not found")
        raise HTTPException(status_code=400, detail="Invalid user id")
    # Сохранение загруженного файла .mtx
    try:
        matrix_content = await matrix_file.read()  # Чтение содержимого файла
        filename = matrix_file.filename
        
        await save_matrix_to_db(user_id=user_id,matrix_name=filename,matrix_content=matrix_content)  # Сохранение матрицы
        
        return {"message": "Matrix saved successfully", "user_id": user_id}
    
    except HTTPException as e:
        # Обработка специфической HTTP ошибки
        print(f"HTTP error occurred while saving matrix: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail="Error saving matrix (HTTP error). Please try again later.")
    
    except Exception as e:
        # Общая обработка всех других исключений
        print(f"An unexpected error occurred while saving matrix: {e}")  # Логируем ошибку
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while saving the matrix (unknown): {e}")

@app.get("/get_matrix_by_matrix_id/{file_id}")
async def get_matrix(file_id: str):
    print('get by user id from main\n')
    matrix_data = await get_matrix_from_db(file_id)
    if not matrix_data:
        print('ERROR : if not matrix_data')
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"matrix_data": matrix_data.decode('utf-8')}  # Или возвращайте в нужном формате

@app.get("/get_matrix_by_user_id/{user_id}")
async def get_matrices_by_user_id(user_id: int):
    matrices = await find_matrices_by_user_id(user_id)
    if not matrices:
        raise HTTPException(status_code=404, detail="No matrices found for this user")
    return {"matrices": matrices}


# Создаем эндпоинт для получения матриц по логину
@app.post("/get_matrix_names_by_user_login")
async def get_matrix_names_by_user_login(credentials: UserInput):
    user_id = await get_user_id(credentials)
    print(f"trying to return matrices by user_login = {credentials.login}, user_id = {user_id}")
    
    matrices = await find_matrices_by_user_id(user_id)
    if not matrices:
        raise HTTPException(status_code=404, detail="No matrices found for this user")
    return {"matrices": matrices}


@app.get("/get_matrix_by_filename/{filename}")
async def get_matrix_by_filename(filename: str):
    matrix = await find_matrix_by_filename(filename)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    matrix_data = matrix.read()  # Получаем содержимое матрицы
    return {"matrix_data": matrix_data.decode('utf-8')}  # Или возвращайте в нужном формате

@app.get("/list_files")
async def list_files():
    try:
        print('trying to list files')
        files = list_files_in_db()  # Убираем await здесь
        return {"files": files}
    except Exception as e:
        print(f"An error occurred while listing files: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while listing files.")

@app.get("/status")
async def get_status():
    # Проверяем доступность MongoDB контейнера
    if not await check_mongodb_availability():
        raise HTTPException(status_code=500, detail="MongoDB server is unavailable")
    
    # Если обе проверки прошли успешно
    print(f"status request, mongo db url - {MONGODB_URL}, sqlite url - {SQLITE_URL}")
    return {"status": "running", "SQLITE_URL": SQLITE_URL, "MONGODB_URL": MONGODB_URL}