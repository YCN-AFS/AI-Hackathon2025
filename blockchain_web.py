from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from web3 import Web3
import json
import uvicorn
from pyngrok import ngrok, conf
import logging
from functools import lru_cache
import os
from Coppy_tourrecommendagent import graph
import uuid

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='transactions.log'
)
logger = logging.getLogger(__name__)

# Lấy đường dẫn tuyệt đối của thư mục hiện tại
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Tạo thư mục static và templates nếu chưa tồn tại
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Tạo file CSS
CSS_CONTENT = """
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #f5f5f5;
    }
    .container {
        max-width: 1200px;
        margin: 0 auto;
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .nav {
        background-color: #2c3e50;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    .nav a {
        color: white;
        text-decoration: none;
        margin-right: 20px;
        padding: 5px 10px;
        border-radius: 4px;
    }
    .nav a:hover {
        background-color: #34495e;
    }
    .form-group {
        margin-bottom: 15px;
    }
    .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .form-group input, .form-group select {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .btn {
        background-color: #3498db;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .btn:hover {
        background-color: #2980b9;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    th {
        background-color: #f8f9fa;
    }
    .alert {
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    .alert-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .alert-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .loading {
        display: none;
        text-align: center;
        margin: 20px 0;
    }
    .loading.active {
        display: block;
    }
    .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 600px;
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
    }
    .chat-messages {
        flex-grow: 1;
        overflow-y: auto;
        padding: 20px;
        background-color: #f9f9f9;
    }
    .message {
        margin-bottom: 15px;
        max-width: 80%;
    }
    .message.user {
        margin-left: auto;
    }
    .message.assistant {
        margin-right: auto;
    }
    .message-content {
        padding: 10px 15px;
        border-radius: 15px;
        display: inline-block;
    }
    .user .message-content {
        background-color: #007bff;
        color: white;
    }
    .assistant .message-content {
        background-color: #e9ecef;
        color: #212529;
    }
    .error .message-content {
        background-color: #dc3545;
        color: white;
    }
    .chat-form {
        display: flex;
        padding: 20px;
        background-color: white;
        border-top: 1px solid #ddd;
    }
    .chat-form input {
        flex-grow: 1;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-right: 10px;
    }
"""

# Tạo templates HTML
TEMPLATES = {
    "index.html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="nav">
                <a href="/">Trang chủ</a>
                <a href="/transactions">Danh sách giao dịch</a>
                <a href="/create">Tạo giao dịch mới</a>
            </div>
            <div class="container">
                <h1>Hệ thống Giao dịch Blockchain</h1>
                <p>Chào mừng đến với hệ thống giao dịch blockchain. Vui lòng chọn một tùy chọn từ menu trên.</p>
                <div class="features">
                    <h2>Tính năng chính:</h2>
                    <ul>
                        <li>Tạo giao dịch mới</li>
                        <li>Xem danh sách giao dịch</li>
                        <li>Theo dõi trạng thái giao dịch</li>
                        <li>Quản lý thông tin người dùng</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
    """,
    "transactions.html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="nav">
                <a href="/">Trang chủ</a>
                <a href="/transactions">Danh sách giao dịch</a>
                <a href="/create">Tạo giao dịch mới</a>
            </div>
            <div class="container">
                <h1>Danh sách giao dịch</h1>
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Đang tải dữ liệu...</p>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Người gửi</th>
                            <th>Người nhận</th>
                            <th>Số tiền</th>
                            <th>Trạng thái</th>
                            <th>Thời gian</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for tx in transactions %}
                        <tr>
                            <td>{{ tx.transactionId }}</td>
                            <td>{{ tx.sender.fullName }}</td>
                            <td>{{ tx.receiver.fullName }}</td>
                            <td>{{ tx.amount }} {{ tx.currency }}</td>
                            <td>{{ tx.status }}</td>
                            <td>{{ tx.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const loading = document.querySelector('.loading');
                    loading.classList.add('active');
                    setTimeout(() => {
                        loading.classList.remove('active');
                    }, 1000);
                });
            </script>
        </body>
        </html>
    """,
    "create.html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="nav">
                <a href="/">Trang chủ</a>
                <a href="/transactions">Danh sách giao dịch</a>
                <a href="/create">Tạo giao dịch mới</a>
            </div>
            <div class="container">
                <h1>Tạo giao dịch mới</h1>
                <form id="transactionForm">
                    <h3>Thông tin người gửi</h3>
                    <div class="form-group">
                        <label>Họ tên:</label>
                        <input type="text" name="sender.fullName" required>
                    </div>
                    <div class="form-group">
                        <label>Số tài khoản:</label>
                        <input type="text" name="sender.accountNumber" required>
                    </div>
                    <div class="form-group">
                        <label>Ngân hàng:</label>
                        <input type="text" name="sender.bankName" required>
                    </div>

                    <h3>Thông tin người nhận</h3>
                    <div class="form-group">
                        <label>Họ tên:</label>
                        <input type="text" name="receiver.fullName" required>
                    </div>
                    <div class="form-group">
                        <label>Số tài khoản:</label>
                        <input type="text" name="receiver.accountNumber" required>
                    </div>
                    <div class="form-group">
                        <label>Ngân hàng:</label>
                        <input type="text" name="receiver.bankName" required>
                    </div>

                    <h3>Thông tin giao dịch</h3>
                    <div class="form-group">
                        <label>Số tiền:</label>
                        <input type="number" name="amount" required>
                    </div>
                    <div class="form-group">
                        <label>Loại tiền:</label>
                        <select name="currency">
                            <option value="VND">VND</option>
                            <option value="USD">USD</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Phí giao dịch:</label>
                        <input type="number" name="fee" value="0">
                    </div>
                    <div class="form-group">
                        <label>Ghi chú:</label>
                        <input type="text" name="note">
                    </div>
                    <div class="form-group">
                        <label>Phương thức thanh toán:</label>
                        <select name="paymentMethod">
                            <option value="bank_transfer">Chuyển khoản</option>
                            <option value="cash">Tiền mặt</option>
                        </select>
                    </div>

                    <button type="submit" class="btn">Tạo giao dịch</button>
                </form>
            </div>

            <script>
                document.getElementById('transactionForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    const data = {
                        sender: {
                            fullName: formData.get('sender.fullName'),
                            accountNumber: formData.get('sender.accountNumber'),
                            bankName: formData.get('sender.bankName')
                        },
                        receiver: {
                            fullName: formData.get('receiver.fullName'),
                            accountNumber: formData.get('receiver.accountNumber'),
                            bankName: formData.get('receiver.bankName')
                        },
                        amount: parseFloat(formData.get('amount')),
                        currency: formData.get('currency'),
                        fee: parseFloat(formData.get('fee')),
                        note: formData.get('note'),
                        paymentMethod: formData.get('paymentMethod')
                    };

                    try {
                        const response = await fetch('/api/transactions/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(data)
                        });
                        const result = await response.json();
                        if (response.ok) {
                            alert('Giao dịch được tạo thành công!');
                            window.location.href = '/transactions';
                        } else {
                            alert('Lỗi: ' + result.detail.error);
                        }
                    } catch (error) {
                        alert('Lỗi: ' + error.message);
                    }
                });
            </script>
        </body>
        </html>
    """,
    "error.html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="nav">
                <a href="/">Trang chủ</a>
                <a href="/transactions">Danh sách giao dịch</a>
                <a href="/create">Tạo giao dịch mới</a>
            </div>
            <div class="container">
                <div class="alert alert-error">
                    <h2>Đã xảy ra lỗi</h2>
                    <p>{{ error }}</p>
                </div>
            </div>
        </body>
        </html>
    """,
    "chat.html": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="nav">
                <a href="/">Trang chủ</a>
                <a href="/transactions">Danh sách giao dịch</a>
                <a href="/create">Tạo giao dịch mới</a>
                <a href="/chat">Chat</a>
            </div>
            <div class="container">
                <h1>Chat với Trợ lý Du lịch</h1>
                <div class="chat-container">
                    <div id="chat-messages" class="chat-messages">
                        {% for message in messages %}
                        <div class="message {{ message.type }}">
                            <div class="message-content">{{ message.content }}</div>
                        </div>
                        {% endfor %}
                    </div>
                    <form id="chat-form" class="chat-form">
                        <input type="text" id="user-input" placeholder="Nhập tin nhắn của bạn..." required>
                        <button type="submit" class="btn">Gửi</button>
                    </form>
                </div>
            </div>

            <script>
                const chatMessages = document.getElementById('chat-messages');
                const chatForm = document.getElementById('chat-form');
                const userInput = document.getElementById('user-input');

                // Scroll to bottom of chat
                function scrollToBottom() {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }

                // Add message to chat
                function addMessage(content, type) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${type}`;
                    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
                    chatMessages.appendChild(messageDiv);
                    scrollToBottom();
                }

                // Handle form submission
                chatForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const message = userInput.value.trim();
                    if (!message) return;

                    // Add user message
                    addMessage(message, 'user');
                    userInput.value = '';

                    try {
                        const response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ message })
                        });

                        const data = await response.json();
                        if (response.ok) {
                            addMessage(data.response, 'assistant');
                        } else {
                            addMessage('Xin lỗi, đã có lỗi xảy ra.', 'error');
                        }
                    } catch (error) {
                        addMessage('Xin lỗi, đã có lỗi xảy ra.', 'error');
                    }
                });

                // Initial scroll
                scrollToBottom();
            </script>
        </body>
        </html>
    """
}

# Tạo file CSS
with open(os.path.join(STATIC_DIR, "style.css"), "w", encoding="utf-8") as f:
    f.write(CSS_CONTENT)

# Tạo các file template
for filename, content in TEMPLATES.items():
    with open(os.path.join(TEMPLATES_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)

app = FastAPI(
    title="Blockchain Transaction Web Interface",
    description="Giao diện web để tương tác với smart contract giao dịch",
    version="1.0.0"
)

# Mount static files và templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Cho phép CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Preferences(BaseModel):
    name: Optional[str] = "Vô Danh"
    number_member: Optional[str] = "2"
    total_expense: Optional[str] = "2 triệu"

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

class ChatMessage(BaseModel):
    message: str

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

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Trang chủ"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Blockchain Transaction System"}
    )

@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    """Trang danh sách giao dịch"""
    try:
        transactions = await list_transactions()
        return templates.TemplateResponse(
            "transactions.html",
            {
                "request": request,
                "title": "Danh sách giao dịch",
                "transactions": transactions
            }
        )
    except Exception as e:
        logger.error(f"Error loading transactions page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Lỗi",
                "error": str(e)
            }
        )

@app.get("/create", response_class=HTMLResponse)
async def create_transaction_page(request: Request):
    """Trang tạo giao dịch mới"""
    return templates.TemplateResponse(
        "create.html",
        {"request": request, "title": "Tạo giao dịch mới"}
    )

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Trang chat"""
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "title": "Chat với Trợ lý Du lịch",
            "messages": []
        }
    )

# API Routes
@app.get("/api/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "account": account_address
    }

@app.post("/api/transactions/")
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

@app.get("/api/transactions/{transaction_id}")
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

@app.get("/api/transactions/", response_model=List[TransactionResponse])
async def list_transactions():
    """Lấy danh sách tất cả giao dịch"""
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

@app.post("/api/chat")
async def chat(chat_message: ChatMessage):
    """Xử lý tin nhắn chat"""
    try:
        # Tạo state mới cho mỗi tin nhắn
        state = {
            "messages": [("user", chat_message.message)],
            "preferences": Preferences(),
            "Recommended_Tour": {},
            "dialog_state": []
        }

        # Chạy graph với tin nhắn mới
        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
            }
        }
        
        events = graph.stream(state, config)
        
        # Lấy response từ event cuối cùng
        response = ""
        for event in events:
            if "messages" in event:
                messages = event["messages"]
                if isinstance(messages, list):
                    messages = messages[-1]
                if hasattr(messages, "content"):
                    response = messages.content

        return {"response": response}

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )

def start_server():
    try:
        # Cấu hình ngrok
        ngrok_token = "2u1qQIoOLe6tloBg3zRir1PvRQI_5KTnVgAfziPjh8xQE3rzw"
        conf.get_default().auth_token = ngrok_token
        
        # Tạo HTTP tunnel
        public_url = ngrok.connect(8000)
        logger.info(f"\nNgrok tunnel created:")
        logger.info(f"Public URL: {public_url}")
        logger.info(f"Swagger UI: {public_url}/docs")
        
        # Chạy FastAPI server
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        ngrok.kill()

if __name__ == "__main__":
    start_server() 