import requests
import json
from datetime import datetime

class TransactionCLI:
    def __init__(self):
        self.BASE_URL = "YOUR_NGROK_URL"  # Thay thế bằng URL ngrok của bạn
        self.last_transaction_id = None

    def print_menu(self):
        print("\n=== BLOCKCHAIN TRANSACTION SYSTEM ===")
        print("1. Tạo giao dịch mới")
        print("2. Xem chi tiết giao dịch")
        print("3. Xem giao dịch gần nhất")
        print("4. Thay đổi URL API")
        print("5. Thoát")
        print("=====================================")

    def create_transaction(self):
        print("\n=== TẠO GIAO DỊCH MỚI ===")
        try:
            # Thông tin người gửi
            print("\nNhập thông tin người gửi:")
            sender = {
                "fullName": input("Họ tên: "),
                "accountNumber": input("Số tài khoản: "),
                "bankName": input("Tên ngân hàng: ")
            }

            # Thông tin người nhận
            print("\nNhập thông tin người nhận:")
            receiver = {
                "fullName": input("Họ tên: "),
                "accountNumber": input("Số tài khoản: "),
                "bankName": input("Tên ngân hàng: ")
            }

            # Thông tin giao dịch
            print("\nNhập thông tin giao dịch:")
            transaction_data = {
                "sender": sender,
                "receiver": receiver,
                "amount": float(input("Số tiền: ")),
                "currency": input("Loại tiền tệ (VND/USD): "),
                "fee": float(input("Phí giao dịch: ")),
                "note": input("Nội dung chuyển tiền: "),
                "paymentMethod": input("Phương thức thanh toán: ")
            }

            response = requests.post(f"{self.BASE_URL}/transactions/", json=transaction_data)
            result = response.json()
            
            if "transactionId" in result:
                self.last_transaction_id = result["transactionId"]
                print("\nGiao dịch đã được tạo thành công!")
                print(f"Transaction ID: {self.last_transaction_id}")
            else:
                print("\nLỗi:", result.get("detail", "Không xác định"))

        except Exception as e:
            print(f"\nLỗi: {str(e)}")

    def get_transaction_details(self):
        try:
            tx_id = input("\nNhập Transaction ID (để trống để xem giao dịch gần nhất): ").strip()
            if not tx_id and self.last_transaction_id:
                tx_id = self.last_transaction_id
            elif not tx_id:
                print("Không có Transaction ID!")
                return

            response = requests.get(f"{self.BASE_URL}/transactions/{tx_id}")
            if response.status_code == 200:
                tx = response.json()
                print("\n=== CHI TIẾT GIAO DỊCH ===")
                print(f"Transaction ID: {tx_id}")
                print(f"\nNGƯỜI GỬI:")
                print(f"Họ tên: {tx['sender']['fullName']}")
                print(f"Số tài khoản: {tx['sender']['accountNumber']}")
                print(f"Ngân hàng: {tx['sender']['bankName']}")
                
                print(f"\nNGƯỜI NHẬN:")
                print(f"Họ tên: {tx['receiver']['fullName']}")
                print(f"Số tài khoản: {tx['receiver']['accountNumber']}")
                print(f"Ngân hàng: {tx['receiver']['bankName']}")
                
                print(f"\nTHÔNG TIN GIAO DỊCH:")
                print(f"Số tiền: {tx['amount']} {tx['currency']}")
                print(f"Phí: {tx['fee']} {tx['currency']}")
                print(f"Thời gian: {tx['timestamp']}")
                print(f"Nội dung: {tx['note']}")
                print(f"Phương thức: {tx['paymentMethod']}")
                print(f"Trạng thái: {tx['status']}")
            else:
                print("\nLỗi:", response.json().get("detail", "Không tìm thấy giao dịch"))

        except Exception as e:
            print(f"\nLỗi: {str(e)}")

    def view_last_transaction(self):
        if self.last_transaction_id:
            print(f"\nGiao dịch gần nhất: {self.last_transaction_id}")
            self.get_transaction_details()
        else:
            print("\nChưa có giao dịch nào được tạo trong phiên này!")

    def change_api_url(self):
        new_url = input("\nNhập URL API mới: ").strip()
        if new_url:
            self.BASE_URL = new_url
            print(f"Đã cập nhật URL API: {self.BASE_URL}")

    def run(self):
        while True:
            self.print_menu()
            choice = input("\nChọn chức năng (1-5): ")

            if choice == "1":
                self.create_transaction()
            elif choice == "2":
                self.get_transaction_details()
            elif choice == "3":
                self.view_last_transaction()
            elif choice == "4":
                self.change_api_url()
            elif choice == "5":
                print("\nTạm biệt!")
                break
            else:
                print("\nLựa chọn không hợp lệ!")

if __name__ == "__main__":
    cli = TransactionCLI()
    cli.run() 