from web3 import Web3
from eth_account import Account
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class BlockchainManager:
    def __init__(self):
        # Kết nối đến blockchain (ví dụ: local Ganache)
        self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        
        # Load contract ABI và address
        with open('contracts/TransactionHistory.json') as f:
            contract_json = json.load(f)
        
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=contract_json['abi']
        )
        
        # Tài khoản để thực hiện giao dịch
        self.account = Account.from_key(os.getenv('PRIVATE_KEY'))

    def create_transaction(self, transaction_data):
        try:
            # Tạo giao dịch
            tx = self.contract.functions.createTransaction(
                transaction_data.sender.fullName,
                transaction_data.sender.accountNumber,
                transaction_data.sender.bankName,
                transaction_data.receiver.fullName,
                transaction_data.receiver.accountNumber,
                transaction_data.receiver.bankName,
                self.w3.to_wei(transaction_data.amount, 'ether'),
                transaction_data.currency,
                self.w3.to_wei(transaction_data.fee, 'ether'),
                transaction_data.note or "",
                transaction_data.paymentMethod,
                "signature",  # Có thể thêm logic tạo chữ ký
                "qrcode"     # Có thể thêm logic tạo QR
            ).build_transaction({
                'from': self.account.address,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })

            # Ký và gửi giao dịch
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return {'status': 'success', 'transaction_hash': receipt['transactionHash'].hex()}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_transaction(self, transaction_id):
        try:
            tx = self.contract.functions.getTransaction(transaction_id).call()
            return {
                'sender': {
                    'fullName': tx[0][0],
                    'accountNumber': tx[0][1],
                    'bankName': tx[0][2]
                },
                'receiver': {
                    'fullName': tx[1][0],
                    'accountNumber': tx[1][1],
                    'bankName': tx[1][2]
                },
                'amount': self.w3.from_wei(tx[2], 'ether'),
                'currency': tx[3],
                'fee': self.w3.from_wei(tx[4], 'ether'),
                'timestamp': datetime.fromtimestamp(tx[5]),
                'note': tx[6],
                'paymentMethod': tx[7],
                'status': ['PROCESSING', 'SUCCESS', 'FAILED'][tx[8]]
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_all_transactions(self):
        try:
            count = self.contract.functions.getTransactionCount().call()
            transactions = []
            
            for i in range(count):
                tx_id = self.contract.functions.getTransactionIdByIndex(i).call()
                tx = self.get_transaction(tx_id)
                transactions.append({
                    'id': tx_id,
                    **tx
                })
                
            return transactions
        except Exception as e:
            return {'status': 'error', 'message': str(e)} 