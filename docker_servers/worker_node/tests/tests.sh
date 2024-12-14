#!/bin/bash

# 1. Построить Docker образ
echo "Building Docker image..."
docker build -t fastapi-matrix-decomposition ../

# 2. Запустить Docker контейнер
echo "Starting Docker container..."
docker run -d --name fastapi-matrix-container -p 8000:8000 fastapi-matrix-decomposition

# 3. Подождать, чтобы сервер успел запуститься
echo "Waiting for the server to start..."
sleep 2
echo "Started."
# # 4. Отправить большую задачу на сервер (тяжелая матрица)
# echo "Sending a heavy task to the server..."
# {
#   curl -s -X 'POST' \
#   'http://127.0.0.1:8000/process_task' \
#   -H 'Content-Type: application/json' \
#   -d '{
#     "input_matrix": '$(python3 -c "import numpy as np; print(np.random.randint(1, 100, (10, 10)).tolist())")',
#     "algorithm": "lu"
#   }' &
# } > /dev/null &



# Тестирование другого разложения (например QR)
curl -s  -X 'POST' \
'http://127.0.0.1:8000/process_task' \
-H 'Content-Type: application/json' \
-d '{
"input_matrix": [[ 1,2 ], [3, 4]]
,
"algorithm": "qr"
}'

echo -e "\n"

# 5. Подождать 0.2 секунду, чтобы убедиться, что задача выполняется
echo "Waiting for the task to process..."
sleep 1


# 6. Отправить запрос на /status во время выполнения задачи
echo "Checking server status during the task execution..."
curl -s  -X 'GET' \
'http://127.0.0.1:8000/status'

echo -e "\n"


curl -s  -X 'GET' \
'http://127.0.0.1:8000/get_result' 

echo -e "\n"

sleep 2

# 6. Отправить запрос на /status во время выполнения задачи
echo "Checking server status during the task execution..."
curl -s -X 'GET' \
'http://127.0.0.1:8000/status'

echo -e "\n"

sleep 4

curl -s  -X 'GET' \
'http://127.0.0.1:8000/get_result' 

# 6. Отправить запрос на /status во время выполнения задачи
echo "Checking server status during the task execution..."

curl -s  -X 'GET' \
'http://127.0.0.1:8000/get_result' 

echo -e "\n"

curl -s -X 'GET' \
'http://127.0.0.1:8000/status'







# # 5. Остановить и удалить Docker контейнер
# echo "Stopping and removing the container..."
# docker stop fastapi-matrix-container
# docker rm fastapi-matrix-container

# # 6. Очистить все Docker ресурсы
# echo "Cleaning up Docker resources..."
# docker rmi fastapi-matrix-decomposition
