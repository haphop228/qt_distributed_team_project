from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import os
from logger import log  # Используем кастомный логгер

app = FastAPI()

# Загрузка конфигураций
SQLITE_URL = os.getenv("SQLITE_URL")
MONGO_SERVER_URL = os.getenv("MONGO_SERVER_URL")
WORKER_CONTROL_SERVER_URL = os.getenv("WORKER_CONTROL_SERVER_URL", default="http://worker-node-control-server:8003")
# Pydantic модель для регистрации пользователя
class RegisterCredentials(BaseModel):
    name: str
    email: str
    login: str
    password: str

# Pydantic модель для входа
class LoginCredentials(BaseModel):
    login: str
    password: str

# Pydantic модель для получения id
class IdCredentials(BaseModel):
    login: str

class MatrixName(BaseModel):
    matrix_name: str

# Функция для проверки доступности серверов
async def check_server_availability(url: str):
    try:
        log(f"Checking server availability: {url}")
        async with httpx.AsyncClient() as client:
            print(f" checking server availability for url:{url}")
            response = await client.get(url)
            if response.status_code == 200:
                log(f"Server available: {url}")
                return True
    except httpx.RequestError as e:
        log(f"Request error while checking {url}: {e}", level="error")
    return False

# Корневой маршрут, добавьте его
@app.get("/")
async def read_root():
    return {"message": "Welcome to the main server"}

# API для входа пользователя
@app.post("/login")
async def login_user(credentials: LoginCredentials):
    log(f"User login attempt: {credentials.login}")
    if not await check_server_availability(f"{SQLITE_URL}/status"):
        log(f"SQLite server unavailable: {SQLITE_URL}/status", level="error")
        raise HTTPException(status_code=503, detail="SQLite сервер недоступен")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SQLITE_URL}/login", json=credentials.dict())

    if response.status_code != 200:
        log(f"Login failed for user {credentials.login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка входа")

    log(f"User {credentials.login} logged in successfully.")
    return response.json()

# API для регистрации пользователя
@app.post("/register")
async def register(credentials: RegisterCredentials):
    log(f"User registration attempt: {credentials.login}")
    if not await check_server_availability(f"{SQLITE_URL}/status"):
        log(f"SQLite server unavailable: {SQLITE_URL}/status", level="error")
        raise HTTPException(status_code=503, detail="SQLite сервер недоступен")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SQLITE_URL}/register", json=credentials.model_dump())

    if response.status_code != 200:
        log(f"Registration failed for user {credentials.login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка регистрации")

    log(f"User {credentials.login} registered successfully.")
    return response.json()

# API для сохранения матрицы
@app.post("/save_matrix")
async def save_matrix(login: str = Form(...), matrix_file: UploadFile = File(...)):
    log(f"Saving matrix {matrix_file.filename} for user {login}")
    if not await check_server_availability(f"{MONGO_SERVER_URL}/status"):
        log(f"MongoDB server unavailable: {MONGO_SERVER_URL}/status", level="error")
        raise HTTPException(status_code=503, detail="MongoDB сервер недоступен")

    async with httpx.AsyncClient() as client:
        files = {'matrix_file': (matrix_file.filename, await matrix_file.read())}
        data = {'login': login}
        response = await client.post(f"{MONGO_SERVER_URL}/save_matrix", data=data, files=files)

    if response.status_code != 200:
        log(f"Matrix save failed for user {login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка при сохранении матрицы")

    log(f"Matrix {matrix_file.filename} saved successfully for user {login}.")
    return response.json()

# API для получения списка матриц
@app.post("/get_matrices_by_user_login")
async def get_matrices_by_user_login(credentials: IdCredentials):
    log(f"Fetching matrix list for user {credentials.login}")
    if not await check_server_availability(f"{MONGO_SERVER_URL}/status") or not await check_server_availability(f"{SQLITE_URL}/status"):
        log(f"One or more servers unavailable: {MONGO_SERVER_URL}, {SQLITE_URL}", level="error")
        raise HTTPException(status_code=503, detail="Один из серверов недоступен")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MONGO_SERVER_URL}/get_matrices_by_user_login", json=credentials.model_dump())

    if response.status_code != 200:
        log(f"Failed to fetch matrices for user {credentials.login}: {response.text}", level="error")
        raise HTTPException(status_code=response.status_code, detail="Ошибка при получении списка матриц")

    log(f"Matrices for user {credentials.login} fetched successfully.")
    return response.json()

# API для разложений матрицы
@app.post("/calculate_all_decompositions_of_matrix_by_matrix_name")
async def calculate_all_decompositions_of_matrix_by_matrix_name(credentials: MatrixName):
    matrix_name = credentials.matrix_name
    log(f"Calculating all decompositions matrix for {matrix_name}")

    if not await check_server_availability(f"{MONGO_SERVER_URL}/status") or not await check_server_availability(f"{WORKER_CONTROL_SERVER_URL}/status"):
        log(f"Required servers unavailable: {MONGO_SERVER_URL}, {WORKER_CONTROL_SERVER_URL}", level="error")
        raise HTTPException(status_code=503, detail="Необходимые серверы недоступны")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{WORKER_CONTROL_SERVER_URL}/calculate_all_decompositions_of_matrix_by_matrix_name", json=credentials.model_dump())

    if response.status_code != 200:
        error_details = response.json() if response.headers.get("content-type") == "application/json" else response.text
        log(f"Calculation failed for {matrix_name}: {error_details}", level="error")
        raise HTTPException(status_code=response.status_code, detail=error_details)

    log(f"all decompositions matrix for {matrix_name} calculated successfully.")
    return response.json()

#example answer from calculate_all_decompositions_of_matrix_by_matrix_name
#{"WORKER_NODE_1":{"status":"success","algorithm":"lu","time_taken":0.0,"result":[[[1.0,0.0,0.0,0.0,0.0,0.0],[1.6,1.0,0.0,0.0,0.0,0.0],[1.6,0.8518518518518519,1.0,0.0,0.0,0.0],[1.5,0.9259259259259259,-0.5893987341772154,1.0,0.0,0.0],[2.0,0.5555555555555556,1.590189873417722,-1.1733472149921917,1.0,0.0],[1.0,0.5555555555555556,-1.6139240506329118,2.0419920180461566,-0.37986155115314263,1.0]],[[10.0,20.0,1.0,1.0,16.0,23.0],[0.0,-27.0,22.4,0.3999999999999999,-0.6000000000000014,-31.800000000000004],[0.0,0.0,-4.68148148148148,12.05925925925926,-5.088888888888889,-6.711111111111112],[0.0,0.0,0.0,18.2373417721519,-9.44382911392405,-1.0110759493670862],[0.0,0.0,0.0,0.0,-32.65525767829256,3.1522644456012614],[0.0,0.0,0.0,0.0,0.0,3.097476118171711]]]},"WORKER_NODE_2":{"status":"success","algorithm":"qr","time_taken":0.001,"result":[[[0.2734854943722097,0.6423964457395935,0.3777439141993703,-0.10425804798928753,0.5453729258564354,-0.2480738948916626],[0.43757679099553554,-0.399234566493794,-0.06504016501671826,-0.67270442579348,0.3089116774706245,0.3113686253836512],[0.43757679099553554,-0.18781695468977272,-0.41340983853951624,0.6473330921750493,0.4268712713026235,0.03293075194115841],[0.4102282415583146,-0.35776540516574273,0.21055507491822562,-0.022669929097835665,-0.2808844351393964,-0.7615597635982859],[0.5469709887444194,0.4919768472141074,-0.3280987788137077,-0.07721669816405131,-0.5588627476390515,0.18122560923926254],[0.2734854943722097,-0.15041959852548625,0.7281410367406866,0.33329047175363097,-0.18357349590643482,0.4770833180908202]],[[36.56501059756444,28.6886283596448,37.604255476178835,17.803905683630852,36.783798993062206,29.48173629332421],[0.0,18.91989965201148,-20.603413192827865,-10.294432692043712,-11.114051492629494,17.77014837644899],[0.0,0.0,10.460369729979927,11.031821516622662,11.45133807155569,13.239203739178562],[0.0,0.0,0.0,13.65080627592158,-0.41296174034417893,-0.366937200529571],[0.0,0.0,0.0,0.0,15.972673853463816,-2.1104823677182503],[0.0,0.0,0.0,0.0,0.0,1.477754184164444]]]},"WORKER_NODE_3":{"status":"error","message":"HTTP 500: {\"detail\":\"Error during decomposition: Matrix must be symmetric for LDL decomposition.\"}"}}

# API для вычисления обратимой матрицы
@app.post("/calculate_invertible_matrix_by_matrix_name")
async def calculate_invertible_matrix_by_matrix_name(credentials: MatrixName):
    matrix_name = credentials.matrix_name
    log(f"Calculating invertible matrix for {matrix_name}")

    if not await check_server_availability(f"{MONGO_SERVER_URL}/status") or not await check_server_availability(f"{WORKER_CONTROL_SERVER_URL}/status"):
        log(f"Required servers unavailable: {MONGO_SERVER_URL}, {WORKER_CONTROL_SERVER_URL}", level="error")
        raise HTTPException(status_code=503, detail="Необходимые серверы недоступны")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{WORKER_CONTROL_SERVER_URL}/calculate_invertible_matrix_by_matrix_name", json=credentials.model_dump())

    if response.status_code != 200:
        error_details = response.json() if response.headers.get("content-type") == "application/json" else response.text
        log(f"Calculation failed for {matrix_name}: {error_details}", level="error")
        raise HTTPException(status_code=response.status_code, detail=error_details)

    log(f"Invertible matrix for {matrix_name} calculated successfully.")
    return response.json()

# API для получения статуса
@app.get("/status")
async def get_status():
    log("Fetching server status")
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    worker_control_server_status = await check_server_availability(f"{WORKER_CONTROL_SERVER_URL}/status")
    log(f"Server statuses: SQLite={sqlite_status}, MongoDB={mongo_server_status}, WorkerControl={worker_control_server_status}")
    return {
        "status": "running",
        "SQLITE_URL": SQLITE_URL,
        "MONGO_SERVER_URL": MONGO_SERVER_URL,
        "WORKER_CONTROL_SERVER_URL": WORKER_CONTROL_SERVER_URL,
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
        "worker_control_server_status": worker_control_server_status
    }
