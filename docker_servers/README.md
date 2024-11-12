# Docker Compose Project with Main, SQLite, and MongoDB Servers

## Overview

This project consists of multiple Docker containers that work together to provide a distributed service for user authentication, data storage, and matrix management. The entry point for clients is the **Main Server**, which routes requests to the **SQLite Server** and **MongoDB Server** for user and matrix operations.

## Project Structure

```plaintext
.
├── configs/                     # Environment configurations for each service
├── db_mongo/                    # MongoDB data volume
├── db_sqlite/                   # SQLite data volume
├── docker-compose.yml           # Docker Compose configuration file
├── main_server/                 # Main Server FastAPI application
├── mongo_app/                   # MongoDB Server FastAPI application
└── sqlite_app/                  # SQLite Server FastAPI application
```

## Docker Compose Services

### 1. SQLite FastAPI Server

- **Purpose**: Handles user registration and authentication.
- **Port**: 8000 (mapped to host 8000).
- **Environment**: `./configs/config_sqlite.env`.
- **Data Volume**: SQLite database stored in `db_sqlite/users.db`.

#### Endpoints

| Method   | Endpoint        | Description                              |
| -------- | --------------- | ---------------------------------------- |
| `POST` | `/login`      | Authenticates a user with login details. |
| `POST` | `/register`   | Registers a new user.                    |
| `POST` | `/id_request` | Retrieves a user ID by login.            |
| `GET`  | `/status`     | Returns the status of the SQLite server. |

##### Example Requests

- **Login**

  ```bash
  curl -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d '{"login": "user1", "password": "pass123"}'
  ```
- **Register**

  ```bash
  curl -X POST "http://localhost:8000/register" -H "Content-Type: application/json" -d '{"name": "Alice", "email": "alice@example.com", "login": "user1", "password": "pass123"}'
  ```

### 2. MongoDB Server

- **Purpose**: Stores matrix files associated with users.
- **Port**: 8001 (mapped to host 8001).
- **Environment**: `./configs/config_mongo_server.env`.
- **Dependencies**: Requires MongoDB database (container `mongodb`) and SQLite for user ID verification.

#### Endpoints

| Method   | Endpoint                               | Description                                     |
| -------- | -------------------------------------- | ----------------------------------------------- |
| `POST` | `/save_matrix`                       | Saves a matrix file uploaded by the user.       |
| `GET`  | `/get_matrix_by_matrix_id/{file_id}` | Retrieves a matrix by its unique ID.            |
| `GET`  | `/get_matrix_by_user_id/{user_id}`   | Lists matrices saved by a specific user.        |
| `POST` | `/get_matrix_names_by_user_login`    | Retrieves names of matrices by user login.      |
| `GET`  | `/get_matrix_by_filename/{filename}` | Retrieves a matrix by filename.                 |
| `GET`  | `/list_files`                        | Lists all stored files in the MongoDB database. |
| `GET`  | `/status`                            | Returns the status of the MongoDB server.       |

##### Example Requests

- **Save Matrix**

  ```bash
  curl -X POST "http://localhost:8001/save_matrix" -F "login=user1" -F "matrix_file=@Matrix_JGL009.mtx"
  ```
- **Get Matrix by User ID**

  ```bash
  curl -X GET "http://localhost:8001/get_matrix_by_user_id/1"
  ```

### 3. Main Server

- **Purpose**: Routes all incoming client requests to appropriate servers (SQLite or MongoDB).
- **Port**: 8002 (mapped to host 8002).
- **Environment**: `./configs/config_main_server.env`.
- **Dependencies**: Depends on both SQLite and MongoDB FastAPI servers.

#### Endpoints

| Method   | Endpoint                            | Description                                                                       |
| -------- | ----------------------------------- | --------------------------------------------------------------------------------- |
| `POST` | `/login`                          | Routes user login request to SQLite server.                                       |
| `POST` | `/register`                       | Routes user registration request to SQLite server.                                |
| `POST` | `/save_matrix`                    | Uploads a matrix file for saving to MongoDB server.                               |
| `POST` | `/get_matrix_names_by_user_login` | Retrieves matrix names associated with a user login.                              |
| `GET`  | `/status`                         | Returns the status of Main Server and availability of SQLite and MongoDB servers. |

##### Example Requests

- **Login**

  ```bash
  curl -X POST "http://localhost:8002/login" -H "Content-Type: application/json" -d '{"login": "user1", "password": "pass123"}'
  ```
- **Save Matrix**

  ```bash
  curl -X POST "http://localhost:8002/save_matrix" -F "login=user1" -F "matrix_file=@Matrix_JGL009.mtx"
  ```

## MongoDB Database

- **Container Name**: `mongodb`
- **Image**: `mongo:latest`
- **Port**: 27017 (mapped to host 27017).
- **Environment**: `./configs/config_mongo_db.env`.
- **Data Volume**: MongoDB database stored in `db_mongo`.

## How to Start the Application

To run all services, navigate to the project directory and execute:

```bash
docker-compose up --build
```

Each service will be built and started based on the configuration in `docker-compose.yml`.

## Troubleshooting

- Check each service's status endpoint (`/status`) to ensure that it is running correctly.
- Use Docker logs to debug individual containers if any issues arise:

  ```bash
  docker-compose logs <service_name>
  ```
