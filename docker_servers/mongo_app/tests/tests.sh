#!/bin/bash
# cd docker_servers/mongo_app/tests
MONGO_VOLUME_PATH="/Users/alicee/Desktop/Work_Main/docker_test/docker_servers/db_mongo"
SQLITE_VOLUME_PATH="/Users/alicee/Desktop/Work_Main/docker_test/docker_servers/db_sqlite"
DOCKER_IMAGE_NAME="my_fastapi_app"
MONGO_IMAGE_NAME="mongo_server"
DOCKER_CONTAINER_NAME="fastapi_app_container"
MONGO_CONTAINER_NAME="mongo_container"
NETWORK_NAME="my_app_network"
MATRIX_FILE="Matrix_JGL009.mtx" 

# # 1. Создаем пользовательскую сеть для взаимодействия контейнеров
# echo "Создаем сеть $NETWORK_NAME..."
# docker network create $NETWORK_NAME

# 2. Сборка Docker образов
echo "Building Docker image for FastAPI..."
docker build -t $DOCKER_IMAGE_NAME ../../sqlite_app/.

echo "Building Docker image for MongoDB SERVER..."
docker build -t $MONGO_IMAGE_NAME ..

# 3. Запуск контейнера с MongoDB
echo "Запуск MongoDB контейнера..."
docker run -d \
    --name $MONGO_CONTAINER_NAME \
    --network $NETWORK_NAME \
    -v "$MONGO_VOLUME_PATH:/data/db" \
    -p 27017:27017 mongo:latest  # Открываем порт MongoDB (если нужно) 

# 4. Запуск контейнера с SQLite
echo "Запуск SQLite контейнера..."
docker run -d \
    -v "$SQLITE_VOLUME_PATH:/app/data" \
    -p 8000:8000 \
    --network $NETWORK_NAME \
    --name $DOCKER_CONTAINER_NAME \
    $DOCKER_IMAGE_NAME

# 5. Запуск контейнера с Mongo_Server
echo "Запуск контейнера с Mongo_Server..."
docker run -d \
    -e MONGODB_URL="mongodb://$MONGO_CONTAINER_NAME:27017" \
    -e SQLITE_URL_ID_REQUEST="http://$DOCKER_CONTAINER_NAME:8000/id_request" \
    -p 8001:8000 \
    --network $NETWORK_NAME \
    --name mongo_server_container \
    $MONGO_IMAGE_NAME

# Делаем паузу, чтобы приложение успело запуститься
sleep 3

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


# 6. Запускаем контейнер MongoDB с монтированием volume

# Тестирование API с помощью curl
echo ""
echo ""
echo "Testing API endpoints using curl..."

# Тест /ping
echo -e "\nTest: /ping"
curl -X GET "http://localhost:8001/ping"

echo -e "\n\nTest: testing connection from Mongo_server to Mongo_db"
curl -X GET "http://localhost:8001/list_files"

# Тест /save_matrix (замените путь к файлу на существующий файл .mtx)
echo -e "\n\nTest: /save_matrix"
curl -X POST "http://localhost:8001/save_matrix" \
    -F "login=johndoe" \
    -F "matrix_file=@$MATRIX_FILE"  # Замените /path/to/your/sample_matrix.mtx на реальный путь к файлу

echo -e "\n\nTest: testing connection from Mongo_server to Mongo_db"
curl -X GET "http://localhost:8001/list_files"

# Тест /get_matrix_by_user_id
echo -e "\n\nTest: /get_matrix_by_user_id"
curl -X GET "http://localhost:8001/get_matrix_by_user_id/1"

# Тест /get_matrix_by_filename
echo -e "\n\nTest: /get_matrix_by_filename"
curl -X GET "http://localhost:8001/get_matrix_by_filename/Matrix_JGL009.mtx"

# # # Очищаем ресурсы после тестов
echo ""
echo "Cleaning up resources..."

docker stop fastapi_app_container
docker rm fastapi_app_container

docker stop mongo_server_container
docker rm mongo_server_container

docker stop mongo_container
docker rm mongo_container

docker image rm my_fastapi_app
docker image rm mongo_server

echo ""
echo "Tests completed."
