from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from web3 import Web3
import json
import uvicorn
from pyngrok import ngrok, conf
import logging

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blockchain Transaction API",
    description="API để tương tác với smart contract giao dịch",
    version="1.0.0"
)

# Cho phép CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kết nối blockchain
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Load contract info
with open('contract_info.json', 'r') as f:
    contract_info = json.load(f)
    CONTRACT_ADDRESS = contract_info['address']
    CONTRACT_ABI = contract_info['abi']

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Sử dụng account đầu tiên từ Ganache
try:
    # Lấy account đầu tiên từ danh sách accounts
    account_address = w3.eth.accounts[0]
    # Đặt account mặc định
    w3.eth.default_account = account_address
    logger.info(f"Using account: {account_address}")
except Exception as e:
    logger.error(f"Error setting up account: {e}")
    exit(1)

# Models
class User(BaseModel):
    fullName: str
    accountNumber: str
    bankName: str

class TransactionCreate(BaseModel):
    sender: User
    receiver: User
    amount: float
    currency: str
    fee: float
    note: Optional[str] = None
    paymentMethod: str

class TransactionResponse(BaseModel):
    transactionId: str
    timestamp: datetime
    sender: User
    receiver: User
    amount: float
    currency: str
    fee: float
    note: Optional[str]
    paymentMethod: str
    status: str

# API Routes
@app.get("/")
async def read_root():
    return {
        "status": "online",
        "blockchain_connected": w3.is_connected(),
        "contract_address": CONTRACT_ADDRESS,
        "current_account": account_address
    }

@app.post("/transactions/")
async def create_transaction(transaction: TransactionCreate):
    try:
        logger.info("Creating new transaction...")
        logger.debug(f"Transaction data: {transaction.dict()}")

        # Tạo giao dịch cơ bản
        create_tx = contract.functions.createTransaction(
            transaction.sender.fullName,
            transaction.sender.accountNumber,
            transaction.sender.bankName,
            transaction.receiver.fullName,
            transaction.receiver.accountNumber,
            transaction.receiver.bankName,
            w3.to_wei(transaction.amount, 'ether')
        ).transact({'from': account_address})

        logger.debug(f"Create transaction hash: {create_tx.hex()}")

        # Đợi transaction được xác nhận
        tx_receipt = w3.eth.wait_for_transaction_receipt(create_tx)
        logger.debug(f"Transaction receipt: {tx_receipt}")

        # Lấy transaction ID từ event
        events = contract.events.NewTransaction().process_receipt(tx_receipt)
        if not events:
            raise Exception("No NewTransaction event found")
        
        tx_id = events[0].args.transactionId
        logger.info(f"Transaction ID: {tx_id.hex()}")

        # Cập nhật thông tin bổ sung
        logger.info("Updating transaction details...")
        update_tx = contract.functions.updateTransactionDetails(
            tx_id,
            transaction.currency,
            w3.to_wei(transaction.fee, 'ether'),
            transaction.note or "",
            transaction.paymentMethod
        ).transact({'from': account_address})

        # Đợi transaction thứ hai được xác nhận
        update_receipt = w3.eth.wait_for_transaction_receipt(update_tx)
        logger.debug(f"Update receipt: {update_receipt}")

        return {
            "status": "success",
            "transactionId": tx_id.hex(),
            "message": "Transaction created and updated successfully"
        }

    except Exception as e:
        logger.error(f"Error in create_transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    try:
        logger.info(f"Getting transaction: {transaction_id}")
        tx_id_bytes = bytes.fromhex(transaction_id.replace('0x', ''))
        
        # Lấy thông tin cơ bản
        basic = contract.functions.getBasicInfo(tx_id_bytes).call()
        # Lấy thông tin chi tiết
        details = contract.functions.getDetails(tx_id_bytes).call()
        
        result = {
            "transactionId": transaction_id,
            "sender": {
                "fullName": basic[0],
                "accountNumber": basic[1],
                "bankName": basic[2]
            },
            "receiver": {
                "fullName": basic[3],
                "accountNumber": basic[4],
                "bankName": basic[5]
            },
            "amount": w3.from_wei(basic[6], 'ether'),
            "timestamp": datetime.fromtimestamp(basic[7]),
            "currency": details[0],
            "fee": w3.from_wei(details[1], 'ether'),
            "note": details[2],
            "paymentMethod": details[3],
            "status": ["PROCESSING", "SUCCESS", "FAILED"][details[4]]
        }
        
        logger.debug(f"Formatted response: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in get_transaction: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/transactions/", response_model=List[TransactionResponse])
async def list_transactions():
    """
    Lấy danh sách tất cả giao dịch
    """
    try:
        # Lấy số lượng giao dịch
        count = contract.functions.getTransactionCount().call()
        transactions = []

        # Lấy thông tin từng giao dịch
        for i in range(count):
            tx_id = contract.functions.getTransactionIdByIndex(i).call()
            tx = contract.functions.getTransaction(tx_id).call()
            
            transactions.append({
                "transactionId": tx_id.hex(),
                "timestamp": datetime.fromtimestamp(tx[9]),
                "sender": {
                    "fullName": tx[0],
                    "accountNumber": tx[1],
                    "bankName": tx[2]
                },
                "receiver": {
                    "fullName": tx[3],
                    "accountNumber": tx[4],
                    "bankName": tx[5]
                },
                "amount": w3.from_wei(tx[6], 'ether'),
                "currency": tx[7],
                "fee": w3.from_wei(tx[8], 'ether'),
                "note": tx[10],
                "paymentMethod": tx[11],
                "status": ["PROCESSING", "SUCCESS", "FAILED"][tx[12]]
            })

        return transactions

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def start_server():
    try:
        # Cấu hình ngrok
        ngrok_token = "2u1qQIoOLe6tloBg3zRir1PvRQI_5KTnVgAfziPjh8xQE3rzw"  # Thay bằng token của bạn
        conf.get_default().auth_token = ngrok_token
        
        # Tạo HTTP tunnel
        public_url = ngrok.connect(8000)
        logger.info(f"\nNgrok tunnel created:")
        logger.info(f"Public URL: {public_url}")
        logger.info(f"Swagger UI: {public_url}/docs")
        
        # Chạy FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        # Đóng tunnel khi kết thúc
        ngrok.kill()

if __name__ == "__main__":
    start_server() 