from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .blockchain import BlockchainManager
from .models import Transaction
from datetime import datetime

app = FastAPI()

# Phục vụ các file static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Khởi tạo blockchain manager
blockchain = BlockchainManager()

@app.get("/")
async def read_root():
    return FileResponse("app/static/index.html")

@app.post("/api/transactions")
async def create_transaction(transaction: Transaction):
    transaction.timestamp = datetime.now()
    result = blockchain.create_transaction(transaction)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    return result

@app.get("/api/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    result = blockchain.get_transaction(transaction_id)
    if result.get('status') == 'error':
        raise HTTPException(status_code=404, detail=result['message'])
    return result

@app.get("/api/transactions")
async def get_all_transactions():
    result = blockchain.get_all_transactions()
    if isinstance(result, dict) and result.get('status') == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    return result 