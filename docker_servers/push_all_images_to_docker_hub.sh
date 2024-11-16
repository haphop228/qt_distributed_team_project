#!/bin/bash

# Переменные
DOCKER_USERNAME="alice3e"
IMAGE_TAG="latest"

# Массив с именами сервисов
SERVERS=("main_server" "mongo_app" "sqlite_app" "worker_node_control_server")

# Логин в Docker Hub
#echo "Logging in to Docker Hub..."
#docker login -u "$DOCKER_USERNAME" || { echo "Failed to log in to Docker Hub"; exit 1; }

# Проверяем, включён ли buildx
if ! docker buildx version >/dev/null 2>&1; then
    echo "Docker Buildx не установлен. Пожалуйста, установите Buildx и попробуйте снова."
    exit 1
fi

# Проверяем, есть ли активный builder
if docker buildx inspect multiarch_builder > /dev/null 2>&1; thenx
    echo "Using existing multiarch_builder..."
    docker buildx use multiarch_builder
else
    echo "Creating and using new multiarch_builder..."
    docker buildx create --name multiarch_builder --use --bootstrap
fi
docker buildx inspect --bootstrap

# Убедимся, что buildx используется
docker buildx create --use --name multiarch_builder --bootstrap || echo "Buildx builder already exists and is in use."

# Функция для сборки и пуша образов
build_and_push_image() {
    local server_name=$1
    echo "Building multi-architecture Docker image for $server_name..."

    # Сборка и публикация образа для нескольких архитектур
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        -t "$DOCKER_USERNAME/$server_name:$IMAGE_TAG" \
        "./$server_name" \
        --push

    if [ $? -eq 0 ]; then
        echo "Successfully built and pushed $server_name image for multi-architecture."
    else
        echo "Failed to build or push $server_name image."
    fi
}

# Цикл для всех серверов
for server in "${SERVERS[@]}"; do
    build_and_push_image "$server"
done

echo "All images have been successfully built and pushed for multi-architecture."
