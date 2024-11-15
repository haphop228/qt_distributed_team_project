# Используем официальный образ Python
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /app
RUN mkdir data

# Копируем файл с зависимостями
COPY ./requirements.txt .

RUN pip install --upgrade pip
# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем код приложения
COPY . .

# Открываем порт 8000 для приложения
EXPOSE 8000

# Запускаем приложение с uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
