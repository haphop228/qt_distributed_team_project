from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import sql_service as sq # sql_service.py
import bcrypt

app = FastAPI()

# Создаем таблицы при старте приложения
sq.create_db_and_tables()

# Pydantic модель для валидации данных
class UserCredentials(BaseModel):
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
    
# API для входа пользователя
@app.post("/login")
async def login_user(credentials: LoginCredentials, db: Session = Depends(sq.get_db_session)):
    print(f"Attempting login for user: {credentials.login}")
    try:
        # Попытка получить пользователя
        user = sq.get_user_by_login(db, credentials.login)
        print(user.password, credentials.password)  # Отладочная информация о пароле
        # Проверка пароля
        if user.password != credentials.password:
            print("Invalid password")
            raise HTTPException(status_code=400, detail="Invalid password")
    except AttributeError:
        # Обработка ситуации, когда user равен None (отсутствует)
        print("User not found")
        raise HTTPException(status_code=400, detail="Invalid login")
    # Если всё прошло успешно
    print(f"Login successful for user: {user.id}")
    return {"message": "Login successful", "user_id": user.id}

# API для регистрации нового пользователя
@app.post("/register")
async def register_user(credentials: UserCredentials, db: Session = Depends(sq.get_db_session)):
    print(credentials)
    # Проверка, есть ли пользователь с таким логином или email
    email_exists = sq.get_user_by_email(db, credentials.email)
    login_exists = sq.get_user_by_login(db, credentials.login)
    print(f'email, login exists: {email_exists, login_exists}')
    if email_exists:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    elif login_exists:
        print(f'User with this login already exists - {credentials.login}')
        raise HTTPException(status_code=400, detail="User with this login already exists")
    else:
    # Добавляем нового пользователя
        print(f'User registered - {credentials.login}')
        new_user = sq.add_user(db, credentials.name, credentials.email, credentials.login, credentials.password)
        return {"message": "Registration successful", "user_id": new_user.id}

# API для получения id пользователя от MongoDB
@app.post("/id_request")
async def id_request(credentials: IdCredentials, db: Session = Depends(sq.get_db_session)):
    print(f"Attempting login for user: {credentials.login}")
    try:
        # Попытка получить пользователя
        user = sq.get_user_by_login(db, credentials.login)
        print(user.login, user.id)  # Отладочная информация о пароле
    except AttributeError:
        # Обработка ситуации, когда user равен None (отсутствует)
        print("User not found")
        raise HTTPException(status_code=400, detail="Invalid login")
    # Если всё прошло успешно
    print(f"Id request successful for user: {user.id}")
    return {"message": "id request successful", "user_id": user.id}

@app.get("/status")
async def get_status():
    print("status - running")
    return {"status": "running"}