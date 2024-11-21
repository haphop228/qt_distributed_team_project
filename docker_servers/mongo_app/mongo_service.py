import os
from pymongo import MongoClient
from gridfs import GridFS
from logger import log  # Импортируем логгер
import hashlib


# Получаем URL MongoDB из переменной окружения
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
log(f"Connecting to MongoDB at {MONGODB_URL}")
client = MongoClient(MONGODB_URL)

# Создаем базу данных и GridFS
db = client["mydatabase"]  # Имя базы данных
grid_fs = GridFS(db)  # GridFS для работы с файлами

def calculate_matrix_hash(matrix_content: bytes) -> str:
    """
    Вычисляет SHA-256 хэш для содержимого матрицы.
    """
    return hashlib.sha256(matrix_content).hexdigest()

async def find_matrix_by_hash(matrix_hash: str):
    """
    Ищет матрицу в базе данных по хэшу.
    """
    log(f"Searching for matrix with hash '{matrix_hash}'")
    try:
        matrix = grid_fs.find_one({"hash": matrix_hash})
        if matrix:
            log(f"Matrix with hash '{matrix_hash}' found")
        else:
            log(f"Matrix with hash '{matrix_hash}' not found")
        return matrix
    except Exception as e:
        log(f"Error searching for matrix with hash '{matrix_hash}': {e}", level="error")
        raise
    
async def find_matrix_by_name(matrix_name: str):
    """
    Ищет матрицу в базе данных по хэшу.
    """
    log(f"Searching for matrix with name '{matrix_name}'")
    try:
        matrix = grid_fs.find_one({"filename": matrix_name})
        if matrix:
            log(f"Matrix with name '{matrix_name}' found")
        else:
            log(f"Matrix with name '{matrix_name}' not found")
        return matrix
    except Exception as e:
        log(f"Error searching for matrix with name '{matrix_name}': {e}", level="error")
        raise

async def save_matrix_to_db(user_id: int, matrix_name: str, matrix_content: bytes):
    """
    Сохраняет матрицу в базу данных только в случае отсутствия её хэша.
    Если матрица с таким именем уже существует, линкует новый user_id и имя без повторного сохранения содержимого.
    """
    log(f"Saving matrix '{matrix_name}' for user_id {user_id}")
    matrix_hash = calculate_matrix_hash(matrix_content)

    # Проверяем, существует ли уже матрица с таким именем
    existing_matrix = await find_matrix_by_hash(matrix_name)
    if existing_matrix:
        
        log(f"Matrix with the same hash already exists '{existing_matrix.filename}', linking user_id {user_id}, matrix name '{matrix_name}")
        # Линкуем новое имя и user_id, не записывая данные заново
        try:
            # Привязка нового user_id и имени к существующему хэшу
            # TODO : не работает (создается новый чанк в любом случае)
            grid_fs.put(matrix_content, user_id=user_id, filename=matrix_name, hash=matrix_hash)

            log(f"Matrix '{matrix_name}' linked to existing matrix with hash '{matrix_hash}' successfully")
            return {
                "message": "Matrix already exists, linked with new user_id and filename",
                "user_id": user_id,
                "existing_filename": existing_matrix.filename,
                "matrix_name": matrix_name,
                "existing_matrix_hash": existing_matrix.matrix_hash,
                "current_matrix_hash": matrix_hash,
            }
        except Exception as e:
            log(f"Error linking matrix '{matrix_name}' to existing matrix: {e}", level="error")
            raise


    # Если матрица с таким именем и хэшем не найдена, сохраняем новую матрицу
    try:
        matrix_record = {
            "user_id": user_id,
            "filename": matrix_name,  # Уникальное имя файла
            "hash": matrix_hash,      # Сохраняем хэш
        }
        grid_fs.put(matrix_content, **matrix_record)
        log(f"Matrix '{matrix_name}' saved successfully for user_id {user_id}")
        return {"message": "Matrix saved successfully", "user_id": user_id, "matrix_name": matrix_name}
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
