#!/bin/bash

# Переменные
DOCKER_USERNAME="alice3e"
#DOCKER_PASSWORD="your_dockerhub_password"  # Замените на свой пароль или используйте Docker Secrets для безопасности
IMAGE_TAG="latest"

# Массив с именами сервисов
SERVERS=("main_server" "mongo_app" "sqlite_app" "worker_node_control_server")

# Логин в Docker Hub
echo "Logging in to Docker Hub..."
#echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Функция для сборки и пуша образов
build_and_push_image() {
    local server_name=$1
    echo "Building Docker image for $server_name..."
    docker build -t "$DOCKER_USERNAME/$server_name:$IMAGE_TAG" ./$server_name
    if [ $? -eq 0 ]; then
        echo "Successfully built $server_name image."
        echo "Pushing $server_name image to Docker Hub..."
        docker push "$DOCKER_USERNAME/$server_name:$IMAGE_TAG"
        if [ $? -eq 0 ]; then
            echo "$server_name image successfully pushed to Docker Hub."
        else
            echo "Failed to push $server_name image."
        fi
    else
        echo "Failed to build $server_name image."
    fi
}

# Цикл для всех серверов
for server in "${SERVERS[@]}"; do
    build_and_push_image "$server"
done

echo "All images have been processed."
