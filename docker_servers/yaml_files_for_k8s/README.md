# Kubernetes YAML Files for Local Setup

Этот репозиторий содержит набор YAML файлов, используемых для настройки и запуска приложения в Kubernetes, настроенного локально с использованием Minikube. Все сервисы и поды находятся в изолированной сети, и только один сервис (main-server) имеет доступ к интернету. 

## Описание

В этих YAML файлах описаны следующие компоненты:

- **Persistent Volumes (PV) и Persistent Volume Claims (PVC)**: Используются для управления хранением данных в Kubernetes.
- **Deployments**: Описания подов и контейнеров, которые запускаются в кластере.
- **Services**: Определяют, как поды взаимодействуют друг с другом, а также с внешним миром.
- **NetworkPolicy**: Ограничивает коммуникацию между подами, чтобы обеспечить изоляцию сети и дать доступ к интернету только для определенных сервисов.

### Компоненты:

1. **main-server**: Основной сервер, которому разрешен доступ к интернету.
2. **worker-node-control-server**: Сервисы, которые должны быть доступны только внутри локальной сети Kubernetes.
3. **mongo-fastapi-server, sqlite-fastapi-server**: Подсистемы для работы с базами данных, ограниченные только внутренним доступом.
4. **MongoDB и SQLite**: Базы данных с сохранением данных в Persistent Volumes.

## Список файлов

### Сетевые политики и настройки безопасности

- **`app-network.yaml`**: Описание сетевой политики (NetworkPolicy), ограничивающей доступ к интернету для всех подов, кроме `main-server`.

### Деплойменты

- **`main-server-deployment.yaml`**: Описание деплоймента для основного сервера, который имеет доступ к интернету.
- **`mongodb-deployment.yaml`**: Деплоймент для сервиса MongoDB, который использует Persistent Volume и подключается к базе данных.
- **`mongo-fastapi-server-deployment.yaml`**: Деплоймент для сервиса, работающего с MongoDB через FastAPI.
- **`sqlite-fastapi-server-deployment.yaml`**: Деплоймент для сервиса, работающего с SQLite через FastAPI.
- **`worker-node-control-server-deployment.yaml`**: Деплоймент для контроллера рабочих узлов, доступный только внутри локальной сети.

### Persistent Volumes и Persistent Volume Claims

- **`mongo-pv.yaml`**: Описание Persistent Volume для MongoDB, используемого для хранения данных.
- **`mongo-pvc.yaml`**: Persistent Volume Claim для MongoDB, привязывающийся к соответствующему Persistent Volume.
- **`sqlite-pv.yaml`**: Описание Persistent Volume для SQLite.
- **`sqlite-pvc.yaml`**: Persistent Volume Claim для SQLite.

## Настройка локальной сети и доступ к интернету

Для обеспечения изоляции подов с доступом только внутри сети, мы используем **NetworkPolicy**. 

### Шаги настройки:

1. **Настройка Persistent Volumes (PV)**:
    - Для работы с базами данных (MongoDB и SQLite) создаются Persistent Volumes, которые привязаны к хосту через `hostPath` в локальной файловой системе.
    - Убедитесь, что пути в `mongo-pv.yaml` и `sqlite-pv.yaml` указывают на правильные директории на вашей локальной машине.

2. **Создание Persistent Volume Claims (PVC)**:
    - Для каждого сервиса (например, MongoDB) создается PVC, который автоматически привязывается к PV.

3. **NetworkPolicy**:
    - В `app-network.yaml` настроены политики, ограничивающие доступ к интернету для всех подов, кроме `main-server`.
    - Эта политика запрещает выход в интернет для всех подов, кроме `main-server`, который получает доступ к портам 80 и 443 для коммуникации с внешним миром.

4. **Deployment и Service**:
    - В `main-server-deployment.yaml` и `worker-node-control-server-deployment.yaml` настроены поды для серверов, а также соответствующие сервисы для обеспечения внутренней коммуникации.
    - Каждый под связан с определенным PVC и Persistent Volume для хранения данных.

## Локальные настройки

Чтобы правильно настроить кластер локально, следуйте этим шагам:

1. Убедитесь, что Minikube настроен и работает на вашем компьютере:
    ```bash
    minikube start
    ```

2. Примените все YAML файлы:
    ```bash
    kubectl apply -f path/to/mongo-pv.yaml
    kubectl apply -f path/to/sqlite-pv.yaml
    kubectl apply -f path/to/app-network.yaml
    kubectl apply -f path/to/main-server-deployment.yaml
    kubectl apply -f path/to/worker-node-control-server-deployment.yaml
    kubectl apply -f path/to/mongo-fastapi-server-deployment.yaml
    kubectl apply -f path/to/sqlite-fastapi-server-deployment.yaml
    kubectl apply -f path/to/mongo-pvc.yaml
    kubectl apply -f path/to/sqlite-pvc.yaml
    ```

3. Проверьте статус подов:
    ```bash
    kubectl get pods
    ```

4. Проверьте сетевые политики:
    ```bash
    kubectl get networkpolicy
    ```

5. Для доступа к сервисам в Kubernetes можно использовать `kubectl port-forward` или NodePort. Например, для доступа к `main-server`:
    ```bash
    kubectl port-forward service/main-server 8002:8000
    ```

6. Для проверки связи между подами используйте команду `kubectl exec`:
    ```bash
    kubectl exec -it <pod_name> -- curl <target_ip_or_url>
    ```

### Примечания

- В данном проекте предполагается, что все сервисы, кроме `main-server`, могут общаться друг с другом, но не могут выходить в интернет.
- Использование Minikube и Kubernetes в локальной среде подразумевает, что ваши ресурсы (например, дисковое пространство) будут использоваться локально.
- Если вам нужно изменить пути для `hostPath`, вы можете сделать это в соответствующих YAML файлах (`mongo-pv.yaml`, `sqlite-pv.yaml`).

## Troubleshooting

1. **Проблемы с сетью**: Если поды не могут подключиться друг к другу, убедитесь, что сетевые политики корректно применяются.
2. **Ошибки с Persistent Volumes**: Проверьте логи Minikube и убедитесь, что ваш локальный путь для `hostPath` существует.

---
kubectl create configmap config-mongo-db --from-env-file=./configs/config_mongo_db.env
kubectl create configmap config-sqlite --from-env-file=./configs/config_sqlite.env
kubectl create configmap config-mongo-server --from-env-file=./configs/config_mongo_server.env
kubectl create configmap config-main-server --from-env-file=./configs/config_main_server.env
kubectl create configmap config-worker-node --from-env-file=./configs/config_worker_node_control_server.env


kubectl create configmap config-mongo-db --from-env-file="C:\Users\User\projects_c++\qt_distributed_team_project\docker_servers\configs\config_mongo_db.env"
kubectl create configmap config-sqlite --from-env-file="C:\Users\User\projects_c++\qt_distributed_team_project\docker_servers\configs\config_sqlite.env"
kubectl create configmap config-mongo-server --from-env-file="C:\Users\User\projects_c++\qt_distributed_team_project\docker_servers\configs\config_mongo_server.env"
kubectl create configmap config-main-server --from-env-file="C:\Users\User\projects_c++\qt_distributed_team_project\docker_servers\configs\config_main_server.env"
kubectl create configmap config-worker-node --from-env-file="C:\Users\User\projects_c++\qt_distributed_team_project\docker_servers\configs\config_worker_node_control_server.env"

