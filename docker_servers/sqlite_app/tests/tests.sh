#!/bin/bash

# Скрипт завершится при ошибке любой команды
set -e

# Сборка Docker образа
echo "Building Docker image..."
docker build -t my_fastapi_app ..

# Запуск Docker-контейнера в фоновом режиме
echo "Running Docker container..."
docker run -d -v /Users/alicee/Desktop/Work_Main/docker_test/docker_servers/db_sqlite:/app/data -p 8000:8000 --name my_fastapi_container my_fastapi_app
# Делаем паузу, чтобы приложение успело запуститься
sleep 5

# Тест регистрации нового пользователя
echo ""
echo "Testing user registration... (it should already exist because of Docker Volume)"

curl -X POST "http://localhost:8000/register" -H "Content-Type: application/json" -d '{
  "name": "John Doe",
  "email": "john@example.com",
  "login": "johndoe",
  "password": "securepassword"
}'

# Тест логина пользователя
echo ""
echo ""
echo "Testing user login..."

curl -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d '{
  "login": "johndoe",
  "password": "securepassword"
}'

# Тест получения id пользователя
echo ""
echo ""
echo "Testing id request..."

curl -X POST "http://localhost:8000/id_request" -H "Content-Type: application/json" -d '{
  "login": "johndoe"
}'

# Остановка и удаление контейнера
echo ""
echo ""
echo "Stopping and removing Docker container..."
docker stop my_fastapi_container
docker rm my_fastapi_container

echo "All tests completed successfully!"
