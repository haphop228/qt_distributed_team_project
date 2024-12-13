# Dockerfile
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы в контейнер
COPY . .

# Устанавливаем утилиты и зависимости системы
RUN apt-get update && apt-get install -y \
    curl \
    less \
    vim \
    bash \
    procps \
    coreutils \
    sudo \
    tree \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
RUN pip install -r requirements.txt 
# --no-cache-dir

# Указываем команду для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
