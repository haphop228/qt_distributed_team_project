import os
from pymongo import MongoClient
from gridfs import GridFS
from logger import log  # Импортируем логгер
import hashlib
from datetime import datetime, timezone
from bson.objectid import ObjectId  # Импорт для работы с ObjectId

# Получаем URL MongoDB из переменной окружения
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
log(f"Connecting to MongoDB at {MONGODB_URL}")
client = MongoClient(MONGODB_URL)

# Создаем базу данных и GridFS
db = client["mydatabase"]  # Имя базы данных
grid_fs = GridFS(db)  # GridFS для работы с файлами


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


def calculate_matrix_hash(matrix_content: bytes) -> str:
    """
    Вычисляет SHA-256 хэш для содержимого матрицы.
    """
    return hashlib.sha256(matrix_content).hexdigest()

async def find_matrix_by_hash(matrix_hash: str):
    """
    Ищет матрицу в базе данных по хэшу и возвращает содержимое файла.
    """
    log(f"Searching for matrix with hash '{matrix_hash}'")
    try:
        # Ищем документ по хэшу
        matrix = grid_fs.find_one({"hash": matrix_hash})
        if matrix:
            log(f"Matrix with hash '{matrix_hash}' found")
            return matrix  # Возвращаем содержимое файла
        else:
            log(f"Matrix with hash '{matrix_hash}' not found")
            return None
    except Exception as e:
        log(f"Error searching for matrix with hash '{matrix_hash}': {e}", level="error")
        raise
    
async def find_matrix_by_name(matrix_name: str):
    """
    Ищет матрицу в базе данных по имени и возвращает содержимое файла.
    """
    log(f"Searching for matrix with name '{matrix_name}'")
    try:
        # Ищем документ по имени файла
        matrix = grid_fs.find_one({"filename": matrix_name})
        if matrix:
            log(f"Matrix with name '{matrix_name}' found")
            # Получаем корректное содержимое документа через get_correct_document
            file_data = await get_correct_document(matrix)
            return file_data  # Возвращаем содержимое файла
        else:
            log(f"Matrix with name '{matrix_name}' not found")
            return None
    except Exception as e:
        log(f"Error searching for matrix with name '{matrix_name}': {e}", level="error")
        raise

async def get_correct_document(document):
    """
    Функция получает документ и возвращает содержимое файла.
    Если документ является оригиналом (is_original=True), возвращаем его содержимое.
    Если документ является ссылкой на оригинальный файл (is_original=False), 
    ищем оригинальный файл по id_of_original_matrix и возвращаем его содержимое.
    """
    
    try:
        log(f"document : {document}, type : {type(document)}")
        log(f"Getting correct document for filename '{document['filename']}'")
        
        # Если это оригинальный файл
        if document['is_original']:
            log(f"Document '{document['filename']}' is the original file.")
            file_id = document['_id']  # ID файла текущего документа
            file_data = grid_fs.get(file_id).read()  # Чтение содержимого файла
            log(f"File with ID {file_id} successfully retrieved from GridFS.")
            return file_data
        
        # Если это ссылка на оригинальный файл
        else:
            log(f"Document '{document['filename']}' is a reference to another file.")
            original_file_id = document['id_of_original_matrix']  # Получаем ID оригинальной матрицы
            log(f"Searching for original file with ID {original_file_id}. type : {original_file_id}")
            
            original_document = db.fs.files.find_one({"_id": ObjectId(original_file_id)})
            if original_document:
                log(f"Original file with ID {original_file_id} found. Fetching it from GridFS.")
                # Получаем содержимое оригинального файла
                file_data = grid_fs.get(original_file_id).read()
                log(f"Original file with ID {original_file_id} successfully retrieved from GridFS.")
                return file_data
            else:
                log(f"Original file with ID {original_file_id} not found.", level="error")
                raise ValueError(f"Original file with ID {original_file_id} not found.")
    
    except Exception as e:
        log(f"Error in get_correct_document for document '{document['filename']}': {e}", level="error")
        raise


    
async def save_matrix_to_db(user_id: int, matrix_name: str, matrix_content: bytes):
    """
    Сохраняет матрицу в базу данных только в случае отсутствия её хэша.
    Если матрица с таким же хэшем уже существует, добавляет новую запись,
    указывающую на уже существующие данные.
    """
    log(f"Saving matrix '{matrix_name}' for user_id {user_id}")
    matrix_hash = calculate_matrix_hash(matrix_content)

    # Проверяем, существует ли уже матрица с таким хэшем
    existing_matrix = await find_matrix_by_hash(matrix_hash)
    
    if existing_matrix:
        log(f"Matrix with the same hash already exists '{existing_matrix.filename}', linking user_id {user_id} with matrix name '{matrix_name}'")
        
        # Добавляем новую запись, привязанную к существующему чанку
        new_metadata = {
            "is_original": False,  # Новая матрица не оригинальная
            "id_of_original_matrix": existing_matrix._id,  # ID оригинальной матрицы
            "user_id": user_id,
            "filename": matrix_name,  # Новое имя файла
            "hash": matrix_hash,      # Существующий хэш
            "chunkSize": existing_matrix.chunkSize,  # Размер чанка
            "length": existing_matrix.length,  # Длина данных
            "uploadDate": datetime.now(timezone.utc),  # Новая дата загрузки
        }

        # Привязываем новый документ к существующему чанку
        db.fs.files.insert_one(new_metadata)
        log(f"Matrix '{matrix_name}' linked to existing data with hash '{matrix_hash}' successfully")
        
        return {
            "message": "Matrix already exists, linked with new metadata",
            "user_id": user_id,
            "existing_filename": existing_matrix.filename,
            "matrix_name": matrix_name,
            "existing_matrix_hash": existing_matrix.hash,
        }

    # Если матрица с таким хэшем не найдена, сохраняем новую матрицу
    try:
        matrix_record = {
            "is_original": True,  # Это оригинальная матрица
            "id_of_original_matrix": "",  # Оригинальная матрица не существует
            "user_id": user_id,
            "filename": matrix_name,  # Уникальное имя файла
            "hash": matrix_hash,      # Новый хэш
        }
        # Сохраняем данные в GridFS
        grid_fs.put(matrix_content, **matrix_record)

        log(f"Matrix '{matrix_name}' saved successfully for user_id {user_id}")
        return {"message": "Matrix saved successfully", "user_id": user_id, "matrix_name": matrix_name}
    
    except Exception as e:
        log(f"Error saving matrix '{matrix_name}' for user_id {user_id}: {e}", level="error")
        raise


async def get_matrix_from_db(file_id):
    """
    Получает матрицу по file_id и возвращает её содержимое.
    Используется функция get_correct_document для получения правильного документа.
    """
    log(f"Retrieving matrix with file_id {file_id}")
    try:
        matrix = await db.fs.files.find_one({"_id": file_id})
        if matrix:
            matrix_data = await get_correct_document(matrix)
            log(f"Matrix with file_id {file_id} retrieved successfully")
            return matrix_data
        else:
            log(f"Matrix with file_id {file_id} not found", level="error")
            raise ValueError(f"Matrix with file_id {file_id} not found")
    except Exception as e:
        log(f"Error retrieving matrix with file_id {file_id}: {e}", level="error")
        raise

async def find_matrices_by_user_id(user_id: int):
    """
    Получает все матрицы пользователя по user_id и возвращает их содержимое.
    Использует функцию get_correct_document для извлечения данных.
    """
    log(f"Fetching matrices for user_id {user_id}")
    try:
        # Получаем все матрицы для данного user_id
        matrices_cursor = db.fs.files.find({"user_id": user_id})
        matrices_list = matrices_cursor.to_list(length=None)  # Преобразуем курсор в список
        
        matrices = []
        for matrix in matrices_list:
            matrix_data = await get_correct_document(matrix)
            matrices.append({
                "file_id": str(matrix["_id"]),
                "filename": matrix["filename"],
                #"matrix_data": matrix_data
            })
        
        if matrices:
            log(f"Matrices for user_id {user_id}: {matrices}")
        else:
            log(f"No matrices found for user_id {user_id}")
        
        return matrices
    except Exception as e:
        log(f"Error fetching matrices for user_id {user_id}: {e}", level="error")
        raise


async def find_matrix_by_filename(filename: str):
    """
    Ищет матрицу по имени файла и возвращает её содержимое.
    Использует функцию get_correct_document для извлечения данных.
    """
    log(f"Searching for matrix with filename '{filename}'")
    try:
        # find_one() уже асинхронный
        matrix = db.fs.files.find_one({"filename": filename})
        if matrix:
            matrix_data = await get_correct_document(matrix)
            log(f"Matrix '{filename}' found")
            return matrix_data
        else:
            log(f"Matrix '{filename}' not found", level="error")
            raise ValueError(f"Matrix '{filename}' not found")
    except Exception as e:
        log(f"Error searching for matrix with filename '{filename}': {e}", level="error")
        raise
