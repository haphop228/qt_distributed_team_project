import os
from pymongo import MongoClient
from gridfs import GridFS
from logger import log  # Импортируем логгер

# Получаем URL MongoDB из переменной окружения
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
log(f"Connecting to MongoDB at {MONGODB_URL}")
client = MongoClient(MONGODB_URL)

# Создаем базу данных и GridFS
db = client["mydatabase"]  # Имя базы данных
grid_fs = GridFS(db)  # GridFS для работы с файлами

async def save_matrix_to_db(user_id: int, matrix_name: str, matrix_content: bytes):
    log(f"Saving matrix '{matrix_name}' for user_id {user_id}")
    try:
        matrix_record = {
            "user_id": user_id,
            "filename": f"{matrix_name}"  # Уникальное имя файла
        }
        grid_fs.put(matrix_content, **matrix_record)
        log(f"Matrix '{matrix_name}' saved successfully for user_id {user_id}")
        return {"message": "Matrix saved to GridFS successfully", "user_id": user_id, "matrix_name": matrix_name}
    except Exception as e:
        log(f"Error saving matrix '{matrix_name}' for user_id {user_id}: {e}", level="error")
        raise

async def get_matrix_from_db(file_id):
    log(f"Retrieving matrix with file_id {file_id}")
    try:
        matrix_data = grid_fs.get(file_id).read()
        log(f"Matrix with file_id {file_id} retrieved successfully")
        return matrix_data
    except Exception as e:
        log(f"Error retrieving matrix with file_id {file_id}: {e}", level="error")
        raise

async def find_matrices_by_user_id(user_id: int):
    log(f"Fetching matrices for user_id {user_id}")
    try:
        matrices = [
            {"file_id": str(matrix._id), "filename": matrix.filename}
            for matrix in grid_fs.find({"user_id": user_id})
        ]
        if matrices:
            log(f"Matrices for user_id {user_id}: {matrices}")
        else:
            log(f"No matrices found for user_id {user_id}")
        return matrices
    except Exception as e:
        log(f"Error fetching matrices for user_id {user_id}: {e}", level="error")
        raise

async def find_matrix_by_filename(filename: str):
    log(f"Searching for matrix with filename '{filename}'")
    try:
        matrix = grid_fs.find_one({"filename": filename})
        if matrix:
            log(f"Matrix '{filename}' found")
        else:
            log(f"Matrix '{filename}' not found")
        return matrix
    except Exception as e:
        log(f"Error searching for matrix with filename '{filename}': {e}", level="error")
        raise

def list_files_in_db():
    log("Listing all files in MongoDB")
    try:
        files = db.fs.files.distinct("filename")
        log(f"Files in database: {files}")
        return files
    except Exception as e:
        log(f"Error listing files in MongoDB: {e}", level="error")
        raise

async def check_mongodb_availability():
    log("Checking MongoDB availability")
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.server_info()  # Проверка соединения
        log("MongoDB is available")
        return True
    except Exception as e:
        log(f"MongoDB is unavailable: {e}", level="error")
        return False
