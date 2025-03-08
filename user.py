import requests
from datetime import datetime, timedelta

# Thay YOUR_NGROK_URL bằng URL ngrok nhận được khi chạy server
# Ví dụ: "https://abcd-xx-xx-xx-xx.ngrok.io/api/v1"
BASE_URL = "https://1547-2401-d800-8d2-d65b-596f-4d2a-c5c9-672d.ngrok-free.app"

# Dữ liệu request
data = {
    "location": "Đà Nẵng",
    "check_in": datetime.now().isoformat(),
    "check_out": (datetime.now() + timedelta(days=2)).isoformat(),
    "adults": 2
}

def test_connection():
    try:
        response = requests.get(BASE_URL)  # Gọi trực tiếp đến BASE_URL
        if response.status_code == 200:
            print("Kết nối thành công đến server!")
            return True
    except requests.exceptions.ConnectionError:
        print("Không thể kết nối đến server!")
        return False

def main():
    if not test_connection():
        return

    # 1. Lấy URL tìm kiếm
    print("\n1. Tạo URL tìm kiếm:")
    url = f"{BASE_URL}/api/v1/generate-url"  # Đường dẫn chính xác
    print(f"Calling endpoint: {url}")
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        print("URL tìm kiếm:", result["url"])
        print("Các tham số:", result["params"])
    else:
        print("Lỗi khi tạo URL:", response.text)

    print("\n2. Tìm kiếm khách sạn:")
    # 2. Lấy danh sách khách sạn
    url = f"{BASE_URL}/api/v1/search-hotels"  # Đường dẫn chính xác
    print(f"Calling endpoint: {url}")
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"Tìm thấy {result['total']} khách sạn:")
        for idx, hotel in enumerate(result['hotels'], 1):
            print(f"\n{idx}. Khách sạn: {hotel['name']}")
            print(f"   Địa chỉ: {hotel['address']}")
            print(f"   Đánh giá: {hotel['rating']}")
            print(f"   Giá: {hotel['price']}")
            if hotel['features']:
                print(f"   Tiện ích: {', '.join(hotel['features'])}")
    else:
        print("Lỗi khi tìm kiếm:", response.text)

if __name__ == "__main__":
    main()