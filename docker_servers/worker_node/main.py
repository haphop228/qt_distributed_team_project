# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os
import tempfile
from logger import log  # Используем кастомный логгер

WORKER_NODE_CONTROL_SERVER_URL = os.getenv("WORKER_NODE_CONTROL_SERVER_URL")
app = FastAPI()

# Function to check server availability
async def check_server_availability(url: str):
    try:
        async with httpx.AsyncClient() as client:
            log(f"Checking server availability for URL: {url}")
            response = await client.get(url)
            if response.status_code == 200:
                log(f"Server {url} is available.")
                return True
            else:
                log(f"Server {url} responded with status code {response.status_code}.")
                return False
    except httpx.RequestError as e:
        log(f"Failed to check server availability for {url}: {e}", level="error")
        return False
    
@app.get("/status")
async def get_status():
    log("Service status checked.")
    return {
        "status": "running",
        "WORKER_CONTROL_URL": WORKER_NODE_CONTROL_SERVER_URL
    }
    
    
#process_task
# 'input_matrix': [ [ 1,2 ] , [3, 4] ],
# 'algorithm': 'lu',
# 'result': [ [ [ 3, 1] , [ 3, 3] ] , [ [1,2],[3,2] ] ]
# 'time_taken": 3.123