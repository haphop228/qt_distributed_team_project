# Проект FastAPI, SQLite и MongoDB в Docker

Этот проект содержит два основных компонента:

1. **Сервер SQLite**: Хранит информацию о пользователях, такую как учетные данные и идентификаторы пользователей.
2. **Сервер FastAPI с MongoDB**: Обрабатывает операции с матрицами, хранит матрицы в MongoDB с использованием GridFS и взаимодействует с сервером SQLite для получения идентификаторов пользователей.

---

## Структура проекта

- `docker-compose.yml`: Конфигурация для контейнеров Docker.
- `main.py`: Реализация сервера FastAPI.
- `mongo_service.py`: Вспомогательные функции для работы с MongoDB с использованием `pymongo` и `GridFS`.
- `tests/test.sh`: Скрипт на Shell для сборки образов, запуска контейнеров и тестирования API.

---

## Требования

- Docker: Убедитесь, что Docker установлен на вашей системе.
- MongoDB: Используется в качестве основной базы данных для хранения матриц.
- FastAPI: Современный веб-фреймворк для построения API на Python.

---

## Инструкции по настройке

### 1. Сборка образов Docker

Перейдите в каталог, содержащий ваши файлы Dockerfile, и выполните следующие команды:

```bash
# Сборка образа Docker для сервера SQLite
docker build -t my_fastapi_app ./path_to_sqlite_app

# Сборка образа Docker для сервера MongoDB
docker build -t mongo_server ./path_to_mongo_server
```

### 2. Создание пользовательской сети Docker

```bash
docker network create my_app_network
```

Эта сеть позволяет контейнерам обмениваться данными между собой.

### 3. Запуск контейнеров

#### a) Запуск контейнера MongoDB

```bash
docker run -d \
  --name mongo_container \
  --network my_app_network \
  -v /path/to/mongo/volume:/data/db \
  -p 27017:27017 \
  mongo:latest
```

#### b) Запуск контейнера FastAPI (Сервер SQLite)

```bash
docker run -d \
  -v /path/to/sqlite/volume:/app/data \
  -p 8000:8000 \
  --network my_app_network \
  --name fastapi_app_container \
  my_fastapi_app
```

#### c) Запуск контейнера сервера MongoDB

```bash
docker run -d \
  -e MONGODB_URL="mongodb://mongo_container:27017" \
  -e SQLITE_URL_ID_REQUEST="http://fastapi_app_container:8000/id_request" \
  -p 8001:8000 \
  --network my_app_network \
  --name mongo_server_container \
  mongo_server
```

### 4. Тестирование настройки

Вы можете протестировать настройку с помощью `curl` или запустив предоставленный скрипт:

```bash
bash tests/test.sh
```

---

## Конечные точки API

### 1. Проверка работоспособности

```http
GET /ping
```

- **Ответ**: `{"status": "running", "port": "8001:8000"}`

### 2. Сохранение матрицы

```http
POST /save_matrix
```

- **Параметры формы**:
  - `login`: Логин пользователя (строка)
  - `matrix_file`: Загруженный файл матрицы (файл)
- **Ответ**: `{"message": "Matrix saved successfully", "user_id": <user_id>}`

### 3. Получение матрицы по идентификатору файла

```http
GET /get_matrix_by_matrix_id/{file_id}
```

- **Ответ**: `{"matrix_data": "<matrix_content>"}`

### 4. Получение матриц по идентификатору пользователя

```http
GET /get_matrix_by_user_id/{user_id}
```

- **Ответ**: Список матриц, связанных с пользователем.

### 5. Получение матрицы по имени файла

```http
GET /get_matrix_by_filename/{filename}
```

- **Ответ**: `{"matrix_data": "<matrix_content>"}`

### 6. Список всех файлов

```http
GET /list_files
```

- **Ответ**: Список уникальных имен файлов, хранящихся в базе данных.

---

## Переменные окружения

- `MONGODB_URL`: URL для подключения к серверу MongoDB. Пример: `mongodb://localhost:27017`
- `SQLITE_URL_ID_REQUEST`: URL для конечной точки сервера SQLite. Пример: `http://localhost:8000/id_request`

---

## Тестирование

Проверьте, что **docker Volumes** монтируется правильно

Вы можете запустить тесты с помощью предоставленного скрипта `test.sh`:

```bash
cd tests # обязательно перейдите в папку
bash test.sh
```

Скрипт выполняет следующие тесты:

1. Регистрация и вход пользователя.
2. Получение идентификатора пользователя.
3. Проверка состояния API.
4. Сохранение и получение матриц.

---

## Примечания

- **Тома Docker**: Убедитесь, что пути томов, указанные в командах `docker run`, существуют на вашей системе.
- **Конфигурация сети**: Контейнеры подключены с использованием пользовательской сети (`my_app_network`), чтобы обеспечить их взаимодействие.

---

## Устранение неполадок

- Если контейнеры не обмениваются данными, убедитесь, что они находятся в одной сети Docker.
- Проверьте, что переменные окружения корректно настроены и доступны внутри контейнеров.

---

https://math.nist.gov/MatrixMarket/data/Harwell-Boeing/counterx/jgl009.html
