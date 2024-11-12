from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Настройка базы данных SQLite
DATABASE_URL = "sqlite:///data/users.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель базы данных для пользователей
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String) # hashed

# Функция для создания таблиц
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

# Функция для добавления пользователя
def add_user(db, name: str, email: str, login: str, password: str):
    new_user = User(name=name, email=email, login=login, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Функция для проверки существования пользователя
def get_user_by_login(db, login: str):
    return db.query(User).filter(User.login == login).first()

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()


# Функция для получения сессии базы данных
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
