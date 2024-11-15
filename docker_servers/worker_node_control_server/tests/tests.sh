#!/bin/bash

MAIN_SERVER_URL="http://localhost:8002"
WORKER_CONTROL_SERVER="http://localhost:8003"

# Test User Data
# Генерация случайных значений для пользователя
USER_NAME="TestUser_$(uuidgen)"
USER_EMAIL="testuser+$(uuidgen)@example.com"
USER_LOGIN="testlogin_$(uuidgen | cut -c1-8)"
USER_PASSWORD=$(openssl rand -base64 12)

# Выводим сгенерированные значения
echo "Generated user details:"
echo "USER_NAME: $USER_NAME"
echo "USER_EMAIL: $USER_EMAIL"
echo "USER_LOGIN: $USER_LOGIN"
echo "USER_PASSWORD: $USER_PASSWORD"

# Test Matrix File
MATRIX_FILE_PATH="./Matrix_FIDAP005.mtx"
MATRIX_FILE_NAME="Matrix_FIDAP005.mtx"

# 0. Test system status
echo ""
echo ""
echo "0. Testing main server status check..."
curl -s "$MAIN_SERVER_URL/status"

# 1. Test user registration
echo ""
echo ""
echo "1. Testing user registration..."
curl -s -X POST "$MAIN_SERVER_URL/register" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "'"$USER_NAME"'",
        "email": "'"$USER_EMAIL"'",
        "login": "'"$USER_LOGIN"'",
        "password": "'"$USER_PASSWORD"'"
    }' 

# 2. Test user login
echo ""
echo ""
echo "2. Testing user login..."
curl -s -X POST "$MAIN_SERVER_URL/login" \
    -H "Content-Type: application/json" \
    -d '{
        "login": "'"$USER_LOGIN"'",
        "password": "'"$USER_PASSWORD"'"
    }' 

# 3. Test uploading matrix
echo ""
echo ""
echo "3. Testing matrix upload..."
curl -s -X POST "$MAIN_SERVER_URL/save_matrix" \
    -F "login=$USER_LOGIN" \
    -F "matrix_file=@$MATRIX_FILE_NAME"

# 4. Test printing matrix by name
echo ""
echo ""
echo "4. Testing print matrix by matrix name..."
curl -s -X POST "$WORKER_CONTROL_SERVER/print_matrix_by_matrix_name" \
    -H "Content-Type: application/json" \
    -d '{
        "matrix_name": "'"$MATRIX_FILE_NAME"'"
    }'