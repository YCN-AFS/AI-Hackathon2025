import requests
from datetime import datetime, timedelta



BASE_URL = "http://192.168.224.199:8000/api/v1"

# Dữ liệu request
data = {
    "location": "Đà Nẵng",
    "check_in": datetime.now().isoformat(),
    "check_out": (datetime.now() + timedelta(days=2)).isoformat(),
    "adults": 2
}

def test_connection():
    try:
        base = BASE_URL.replace("/api/v1", "")
        if not base.startswith("http"):
            base = "http://" + base
            
        response = requests.get(base)
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
    response = requests.post(f"{BASE_URL}/generate-url", json=data)
    if response.status_code == 200:
        result = response.json()
        print("URL tìm kiếm:", result["url"])
        print("Các tham số:", result["params"])
    else:
        print("Lỗi khi tạo URL:", response.text)

    print("\n2. Tìm kiếm khách sạn:")
    # 2. Lấy danh sách khách sạn
    response = requests.post(f"{BASE_URL}/search-hotels", json=data)
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