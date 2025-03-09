from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from web3 import Web3
import json
import uvicorn
from pyngrok import ngrok, conf
import logging
from functools import lru_cache

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='transactions.log'
)
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

# Models
class User(BaseModel):
    fullName: str
    accountNumber: str
    bankName: str

class TransactionCreate(BaseModel):
    sender: User
    receiver: User
    amount: float
    currency: str = "VND"
    fee: float = 0.0
    note: str = ""
    paymentMethod: str = "bank_transfer"

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

# Cache cho contract info
@lru_cache(maxsize=1)
def load_contract_info() -> Dict[str, Any]:
    try:
        with open('contract_info.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading contract info: {e}")
        raise Exception("Could not load contract information")

# Khởi tạo Web3 và contract
def setup_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    if not w3.is_connected():
        raise Exception("Could not connect to blockchain")
    return w3

def setup_contract(w3: Web3) -> Any:
    contract_info = load_contract_info()
    contract_address = Web3.to_checksum_address(contract_info['address'])
    contract = w3.eth.contract(
        address=contract_address,
        abi=contract_info['abi']
    )
    return contract

# Khởi tạo các biến global
try:
    w3 = setup_web3()
    contract = setup_contract(w3)
    account_address = w3.eth.accounts[0]
    logger.info(f"Connected to blockchain. Using account: {account_address}")
except Exception as e:
    logger.error(f"Setup error: {e}")
    raise

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "account": account_address
    }

@app.post("/transactions/")
async def create_transaction(transaction: TransactionCreate):
    """Create a new transaction"""
    try:
        # Validate input
        if not all([
            transaction.sender.fullName,
            transaction.sender.accountNumber,
            transaction.sender.bankName,
            transaction.receiver.fullName,
            transaction.receiver.accountNumber,
            transaction.receiver.bankName
        ]):
            raise ValueError("All fields must be non-empty")
        
        if transaction.amount <= 0:
            raise ValueError("Amount must be positive")

        # Check account balance
        balance = w3.eth.get_balance(account_address)
        if balance < w3.to_wei(0.1, 'ether'):
            raise Exception(f"Account balance too low: {w3.from_wei(balance, 'ether')} ETH")

        # Estimate gas
        gas_estimate = contract.functions.createTransaction(
            transaction.sender.fullName,
            transaction.sender.accountNumber,
            transaction.sender.bankName,
            transaction.receiver.fullName,
            transaction.receiver.accountNumber,
            transaction.receiver.bankName,
            w3.to_wei(transaction.amount, 'ether')
        ).estimate_gas({'from': account_address})

        # Create transaction with 20% higher gas limit
        gas_limit = int(gas_estimate * 1.2)
        create_tx = contract.functions.createTransaction(
            transaction.sender.fullName,
            transaction.sender.accountNumber,
            transaction.sender.bankName,
            transaction.receiver.fullName,
            transaction.receiver.accountNumber,
            transaction.receiver.bankName,
            w3.to_wei(transaction.amount, 'ether')
        ).transact({
            'from': account_address,
            'gas': gas_limit
        })

        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(create_tx)
        if tx_receipt['status'] == 0:
            raise Exception(f"Transaction failed. Gas used: {tx_receipt['gasUsed']}")

        # Get transaction ID from event
        events = contract.events.NewTransaction().process_receipt(tx_receipt)
        if not events:
            raise Exception("No NewTransaction event found")
        
        tx_id = events[0].args.transactionId

        # Update transaction details
        update_tx = contract.functions.updateTransactionDetails(
            tx_id,
            transaction.currency,
            w3.to_wei(transaction.fee, 'ether'),
            transaction.note,
            transaction.paymentMethod
        ).transact({
            'from': account_address,
            'gas': 300000
        })

        # Wait for update transaction
        update_receipt = w3.eth.wait_for_transaction_receipt(update_tx)
        if update_receipt['status'] == 0:
            raise Exception("Update transaction failed")

        return {
            "status": "success",
            "transactionId": tx_id.hex(),
            "blockNumber": tx_receipt['blockNumber'],
            "gasUsed": tx_receipt['gasUsed']
        }

    except Exception as e:
        logger.error(f"Error in create_transaction: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail={"error": str(e), "message": "Transaction failed"}
        )

@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Get transaction details"""
    try:
        tx_id_bytes = bytes.fromhex(transaction_id.replace('0x', ''))
        
        # Get basic info
        basic = contract.functions.getBasicInfo(tx_id_bytes).call()
        # Get details
        details = contract.functions.getDetails(tx_id_bytes).call()
        
        return {
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