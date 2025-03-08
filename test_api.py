import requests
import json

# URL từ ngrok
BASE_URL = "your_ngrok_url"

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
        response = requests.post(f"{BASE_URL}/transactions/", json=transaction_data)
        print("Create Transaction Response:", json.dumps(response.json(), indent=2))
        
        if "transactionId" in response.json():
            # Get transaction details
            tx_id = response.json()["transactionId"]
            tx_details = requests.get(f"{BASE_URL}/transactions/{tx_id}")
            print("\nTransaction Details:", json.dumps(tx_details.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_create_transaction() 