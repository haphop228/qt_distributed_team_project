import os
from pymongo import MongoClient
from gridfs import GridFS

# Получаем URL MongoDB из переменной окружения
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)

# Создаем базу данных и GridFS
db = client["mydatabase"]  # Замените на имя вашей базы данных
grid_fs = GridFS(db)  # Создаем экземпляр GridFS

async def save_matrix_to_db(user_id: int, matrix_name: str, matrix_content: bytes):
    # Сохранение матрицы в GridFS 
    matrix_record = {
        "user_id": user_id,
        "filename": f"{matrix_name}"  # Уникальное имя файла
    }

    # Запись матрицы в GridFS
    grid_fs.put(matrix_content, **matrix_record)  # Используем метод put для сохранения

    return {"message": "Matrix saved to GridFS successfully", "user_id": user_id, "matrix_name": matrix_name}

async def get_matrix_from_db(file_id):
    # Извлечение матрицы из GridFS по ID
    matrix_data = grid_fs.get(file_id).read()
    return matrix_data

async def find_matrices_by_user_id(user_id: int):
    print(f'\n\ntrying to get matrix by id {user_id}\n')
    # Поиск всех матриц для конкретного пользователя
    matrices = []
    for matrix in grid_fs.find({"user_id": user_id}):
        matrices.append({"file_id": str(matrix._id), "filename": matrix.filename})
    print(f'\n\nmatrix by id {matrices}\n')
    return matrices

async def find_matrix_by_filename(filename: str):
    # Поиск матрицы по имени файла
    matrix = grid_fs.find_one({"filename": filename})
    return matrix

def list_files_in_db():
    # Извлечение всех уникальных имен файлов из GridFS
    print(f'list files from mongo {MONGODB_URL}')
    files = db.fs.files.distinct("filename")  # Используем коллекцию fs.files для distinct-запроса
    print(f'files {files}')
    return files

async def check_mongodb_availability():
    try:
        # Подключаемся к MongoDB с помощью pymongo
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.server_info()  # Это вызывает ошибку, если MongoDB недоступен
        return True
    except Exception as e:
        print(f"MongoDB доступен: {e}")
        return False