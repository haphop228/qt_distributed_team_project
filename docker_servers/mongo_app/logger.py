import logging
from datetime import datetime

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат: timestamp + уровень + сообщение
    handlers=[
        logging.FileHandler("container.log", mode="a", encoding="utf-8"),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль
    ]
)

# Функция для форматирования времени и записи логов
def log(message: str, level: str = "info"):
    if level.lower() == "info":
        logging.info(message)
    elif level.lower() == "warning":
        logging.warning(message)
    elif level.lower() == "error":
        logging.error(message)
    elif level.lower() == "debug":
        logging.debug(message)
    else:
        logging.info(message)
