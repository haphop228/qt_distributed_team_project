from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging
import sql_service as sq  # sql_service.py
import bcrypt
from datetime import datetime

# Настройка логирования
log_file = "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler(log_file, encoding="utf-8")  # Запись в файл
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Создаем таблицы при старте приложения
logger.info("Initializing database...")
sq.create_db_and_tables()

# Pydantic модели
class UserCredentials(BaseModel):
    name: str
    email: str
    login: str
    password: str

class LoginCredentials(BaseModel):
    login: str
    password: str

class IdCredentials(BaseModel):
    login: str

# API для входа пользователя
@app.post("/login")
async def login_user(credentials: LoginCredentials, db: Session = Depends(sq.get_db_session)):
    logger.info(f"Login attempt for user: {credentials.login}")
    try:
        user = sq.get_user_by_login(db, credentials.login)
        if credentials.password == user.password:
            logger.info(f"Login successful for user ID: {user.id}")
            return {"message": "Login successful", "user_id": user.id}
        else:
            logger.warning(f"Invalid login attempt for user: {credentials.login}")
            raise HTTPException(status_code=400, detail="Invalid login or password")
    except Exception as e:
        logger.error(f"Error during login for user {credentials.login}: {e}")
        raise HTTPException(status_code=400, detail="An error occurred")

# API для регистрации нового пользователя
@app.post("/register")
async def register_user(credentials: UserCredentials, db: Session = Depends(sq.get_db_session)):
    logger.info(f"Registration attempt for user: {credentials.login}")
    email_exists = sq.get_user_by_email(db, credentials.email)
    login_exists = sq.get_user_by_login(db, credentials.login)
    if email_exists or login_exists:
        logger.warning(f"User already exists: email={credentials.email}, login={credentials.login}")
        raise HTTPException(
            status_code=400,
            detail="User with this email or login already exists"
        )
    try:
        new_user = sq.add_user(db, credentials.name, credentials.email, credentials.login, credentials.password)
        logger.info(f"User successfully registered: {credentials.login}, ID: {new_user.id}")
        return {"message": "Registration successful", "user_id": new_user.id}
    except Exception as e:
        logger.error(f"Error during registration for user {credentials.login}: {e}")
        raise HTTPException(status_code=400, detail="An error occurred during registration")

# API для получения id пользователя
@app.post("/id_request")
async def id_request(credentials: IdCredentials, db: Session = Depends(sq.get_db_session)):
    logger.info(f"ID request for user: {credentials.login}")
    try:
        user = sq.get_user_by_login(db, credentials.login)
        logger.info(f"ID request successful for user: {credentials.login}, ID: {user.id}")
        return {"message": "ID request successful", "user_id": user.id}
    except Exception as e:
        logger.error(f"Error during ID request for user {credentials.login}: {e}")
        raise HTTPException(status_code=400, detail="Invalid login")

# API для проверки статуса
@app.get("/status")
async def get_status():
    logger.info("Status check requested")
    return {"status": "running"}
