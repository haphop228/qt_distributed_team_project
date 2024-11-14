from fastapi import FastAPI, HTTPException
import httpx
import os
import numpy as np
from scipy.io import mmread
from io import BytesIO,StringIO

app = FastAPI()

# Load configurations from environment variables
SQLITE_URL = os.getenv("SQLITE_URL")
MONGO_SERVER_URL = os.getenv("MONGO_SERVER_URL")
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL")

# Function to check server availability
async def check_server_availability(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.status_code == 200
    except httpx.RequestError:
        return False

@app.get("/status")
async def get_status():
    sqlite_status = await check_server_availability(f"{SQLITE_URL}/status")
    mongo_server_status = await check_server_availability(f"{MONGO_SERVER_URL}/status")
    main_server_status = await check_server_availability(f"{MAIN_SERVER_URL}/status")
    return {
        "status": "running",
        "sqlite_status": sqlite_status,
        "mongo_server_status": mongo_server_status,
        "main_server_status": main_server_status
    }

@app.post("/get_matrix_by_name")
async def get_matrix_by_name(matrix_name: str):
    # Endpoint on Mongo server to fetch matrix by name
    mongo_endpoint = f"{MONGO_SERVER_URL}/send_matrix_by_matrix_name"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(mongo_endpoint, params={"matrix_name": matrix_name})
            if response.status_code == 200:
                # Stream the file directly in the response
                return response  # FastAPI handles streamed responses if returned directly
            else:
                raise HTTPException(status_code=response.status_code, detail="Matrix not found on MongoDB server")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB server") from e

@app.post("/print_matrix_by_matrix_name")
async def print_matrix_by_matrix_name(matrix_name: str):
    # Retrieve the matrix file in binary format
    matrix_data = await get_matrix_by_name(matrix_name)
    
    # Convert the binary matrix data to a NumPy array
    try:
        matrix = mmread(BytesIO(matrix_data)).toarray()  # Load .mtx content to a NumPy array
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to parse the matrix file") from e

    # Print the matrix to the terminal
    print(f"Matrix '{matrix_name}':\n", matrix)
    
    return {"message": f"Matrix '{matrix_name}' printed to the terminal successfully"}