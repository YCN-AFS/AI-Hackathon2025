# 🌐 Blockchain Transaction Database System

A powerful and flexible blockchain-based transaction database system for secure financial record keeping. Built with Solidity smart contracts and Python FastAPI.

## ✨ Features

- 🔗 **Blockchain-Powered**: Immutable and transparent transaction records
- 🌍 **Accessible Anywhere**: RESTful API with ngrok tunneling
- 🔒 **Secure**: Cryptographic verification of all transactions
- 📱 **Easy Integration**: Simple client library for other applications
- ⚡ **Real-time**: Instant transaction processing and verification

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python 3.8+ and pip
python -v  # Should be 3.8 or higher

# Install required packages
pip install -r requirements.txt
```

### 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/blockchain-transaction-db.git
cd blockchain-transaction-db
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install fastapi uvicorn web3 pyngrok solcx
```

### 🛠️ Configuration

1. **Deploy Smart Contract**
```bash
python deploy_contract.py
```

2. **Start the API Server**
```bash
python blockchain_api.py
```

## 💡 Usage

### Using the Client Library

```python
from blockchain_client import BlockchainClient

# Initialize client
client = BlockchainClient("your-ngrok-url")

# Create a new transaction
result = client.create_transaction(
    sender_name="John Doe",
    sender_account="123456789",
    sender_bank="ExampleBank",
    receiver_name="Jane Smith",
    receiver_account="987654321",
    receiver_bank="TestBank",
    amount=1000.00,
    currency="USD",
    fee=1.00,
    note="Payment for services",
    payment_method="bank_transfer"
)

# Get transaction details
tx_details = client.get_transaction_details(result["transactionId"])
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transactions/` | POST | Create new transaction |
| `/transactions/{id}` | GET | Get transaction details |
| `/transactions/` | GET | List all transactions |

## 📊 Data Structure

### Transaction Schema
```json
{
    "sender": {
        "fullName": "string",
        "accountNumber": "string",
        "bankName": "string"
    },
    "receiver": {
        "fullName": "string",
        "accountNumber": "string",
        "bankName": "string"
    },
    "amount": "float",
    "currency": "string",
    "fee": "float",
    "note": "string",
    "paymentMethod": "string",
    "status": "string"
}
```

## 🔐 Security

- All transactions are stored on blockchain
- Each transaction has a unique identifier
- Cryptographic verification of all operations
- Immutable transaction history

## 📚 Project Structure
