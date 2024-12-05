#!/bin/bash

# 1. Построить Docker образ
echo "Building Docker image..."
docker build -t fastapi-matrix-decomposition ../

# 2. Запустить Docker контейнер
echo "Starting Docker container..."
docker run -d --name fastapi-matrix-container -p 8000:8000 fastapi-matrix-decomposition

# 3. Подождать, чтобы сервер успел запуститься
echo "Waiting for the server to start..."
sleep 5

# 4. Выполнить тесты с использованием curl (можно использовать httpx или pytest, но curl для простоты)
echo "Running tests..."

# Пример теста на разложение LU
curl -s -X 'POST' \
'http://127.0.0.1:8000/decompose_matrix' \
-H 'Content-Type: application/json' \
-d '{
"input_matrix": [[4, 3], [6, 3]],
"algorithm": "lu"
}'


# Тестирование другого разложения (например QR)
curl -s -X 'POST' \
'http://127.0.0.1:8000/decompose_matrix' \
-H 'Content-Type: application/json' \
-d '{
"input_matrix": [[12, -51, 4], [6, 167, -68], [-4, 24, -41]],
"algorithm": "qr"
}'


# # 5. Остановить и удалить Docker контейнер
# echo "Stopping and removing the container..."
# docker stop fastapi-matrix-container
# docker rm fastapi-matrix-container

# # 6. Очистить все Docker ресурсы
# echo "Cleaning up Docker resources..."
# docker rmi fastapi-matrix-decomposition
