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
curl -s -X 'POST' \
'http://127.0.0.1:8000/process_task' \
-H 'Content-Type: application/json' \
-d '{
"input_matrix": [[  12,  -51,    4,   32,  -18,   22,  -15,   47,  -23,    5],
 [   6,  167,  -68,  -25,   38,  -44,   12,  -36,   10,  -16],
 [  -4,   24,  -41,   12,  -50,   33,   17,  -11,   19,   -7],
 [  20,  -13,   55,   45,   16,  -35,  -22,   40,  -48,   14],
 [  -8,   29,   -7,  -12,   72,   18,   23,  -21,    8,   -5],
 [  14,  -33,   27,   13,   19,  -61,   31,   17,  -25,   10],
 [ -17,   11,   34,  -24,   20,   22,   65,  -18,   27,  -13],
 [  25,  -47,   15,   38,  -42,  -12,   14,   73,  -28,   21],
 [ -12,   37,  -19,  -28,   30,  -27,   35,  -33,   90,  -14],
 [   8,  -22,   11,   15,  -17,   20,  -12,   19,  -23,   54]]
,
"algorithm": "qr"
}'

# 5. Подождать 0.2 секунду, чтобы убедиться, что задача выполняется
echo "Waiting for the task to process..."
sleep 0.1

# 6. Отправить запрос на /status во время выполнения задачи
echo "Checking server status during the task execution..."
curl -s -X 'GET' \
'http://127.0.0.1:8000/status'

sleep 0.4

# 6. Отправить запрос на /status во время выполнения задачи
echo "Checking server status during the task execution..."
curl -s -X 'GET' \
'http://127.0.0.1:8000/status'

sleep 1

# 6. Отправить запрос на /status во время выполнения задачи
echo "Checking server status during the task execution..."
curl -s -X 'GET' \
'http://127.0.0.1:8000/status'

# 7. Ожидание завершения фоновой задачи
wait


# # 5. Остановить и удалить Docker контейнер
# echo "Stopping and removing the container..."
# docker stop fastapi-matrix-container
# docker rm fastapi-matrix-container

# # 6. Очистить все Docker ресурсы
# echo "Cleaning up Docker resources..."
# docker rmi fastapi-matrix-decomposition
