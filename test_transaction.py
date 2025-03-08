import requests
import json
import logging

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# URL từ ngrok
BASE_URL = "your_ngrok_url"  # Thay thế bằng URL thật

def test_create_transaction():
    transaction_data = {
        "sender": {
            "fullName": "Nguyen Van A",
            "accountNumber": "123456789",
            "bankName": "VietcomBank"
        },
        "receiver": {
            "fullName": "Tran Thi B",
            "accountNumber": "987654321",
            "bankName": "TPBank"
        },
        "amount": 1.0,
        "currency": "VND",
        "fee": 0.001,
        "note": "Test transaction",
        "paymentMethod": "bank_transfer"
    }

    try:
        logger.info("Sending create transaction request...")
        logger.debug(f"Request data: {json.dumps(transaction_data, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/transactions/", json=transaction_data)
        response_data = response.json()
        logger.info("Create transaction response received")
        logger.debug(f"Response: {json.dumps(response_data, indent=2)}")
        
        if "transactionId" in response_data:
            tx_id = response_data["transactionId"]
            logger.info(f"Getting transaction details for ID: {tx_id}")
            
            tx_response = requests.get(f"{BASE_URL}/transactions/{tx_id}")
            tx_data = tx_response.json()
            logger.debug(f"Transaction details: {json.dumps(tx_data, indent=2)}")
        
        return response_data
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_create_transaction()
    print("\nTest result:", json.dumps(result, indent=2)) 