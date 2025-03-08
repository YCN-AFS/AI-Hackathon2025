import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Any
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from urllib.parse import quote
import pickle
import os

class BaseScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_soup(self, url: str) -> BeautifulSoup:
        response = requests.get(url, headers=self.headers)
        return BeautifulSoup(response.content, 'html.parser')
    
    def get_selenium_driver(self):
        chrome_options = Options()
        
        # Thêm các arguments mới để tránh lỗi shared memory
        chrome_options.add_argument('--headless=new')  # Sử dụng headless mode mới
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Thêm window size cụ thể
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Thêm user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver

class TravelokaScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.traveloka.com/vi-vn"
        self.cookies_file = "traveloka_cookies.pkl"
    
    def save_cookies(self, cookies: List[Dict]):
        """Lưu cookies vào file"""
        with open(self.cookies_file, 'wb') as f:
            pickle.dump(cookies, f)
        print("Đã lưu cookies")
    
    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """Load cookies từ file và áp dụng vào driver"""
        try:
            if not os.path.exists(self.cookies_file):
                return False
                
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                
            # Truy cập trang web trước khi add cookies
            driver.get(self.base_url)
            
            for cookie in cookies:
                driver.add_cookie(cookie)
            
            print("Đã load cookies thành công")
            return True
            
        except Exception as e:
            print(f"Lỗi khi load cookies: {str(e)}")
            return False

    def get_hotels(self, location: str, cookies: List[Dict] = None) -> List[Dict]:
        driver = None
        try:
            # Cấu hình Chrome tối ưu hơn
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # Bật headless mode để tăng tốc
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-images')  # Tắt load hình ảnh
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            chrome_options.add_argument('--disable-javascript')  # Tắt JavaScript không cần thiết
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(5)  # Giảm thời gian chờ xuống
            
            # Tạo URL và truy cập
            search_url = self.build_hotel_search_url(location, datetime.now(), datetime.now() + timedelta(days=2))
            print(f"Đang truy cập URL: {search_url}")
            driver.get(search_url)
            
            # Đợi container với timeout ngắn hơn
            wait = WebDriverWait(driver, 10)
            
            try:
                # Đợi container chính xuất hiện
                hotel_container = wait.until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div[2]/div/div[2]"))
                )
                
                # Lấy tất cả khách sạn
                hotel_elements = hotel_container.find_elements(
                    By.CSS_SELECTOR, 
                    "div[data-testid='tvat-searchListItem-content']"
                )
                
                print(f"Tìm thấy {len(hotel_elements)} khách sạn")
                
                hotels = []
                # Chỉ lấy 10 khách sạn đầu tiên để test
                for element in hotel_elements[:10]:
                    try:
                        hotel = {
                            'name': element.find_element(By.CSS_SELECTOR, "h3").text,
                            'address': element.find_element(By.CSS_SELECTOR, "div[data-testid='tvat-hotelLocation']").text,
                            'rating': element.find_element(By.CSS_SELECTOR, "div[data-testid='tvat-ratingScore']").text,
                            'price': element.find_element(By.CSS_SELECTOR, "div[data-testid='tvat-hotelPrice']").text,
                            'features': [
                                f.text for f in element.find_elements(By.CSS_SELECTOR, "div[id^='hotel-feature-badge-']")
                            ]
                        }
                        hotels.append(hotel)
                        
                    except Exception as e:
                        continue
                
                return hotels
                
            except Exception as e:
                print(f"Lỗi: {str(e)}")
                return []
                
        finally:
            if driver:
                driver.quit()

    def build_hotel_search_url(self, location: str, check_in: datetime, check_out: datetime, adults: int = 1) -> str:
        # Format dates
        check_in_str = check_in.strftime('%d-%m-%Y')
        check_out_str = check_out.strftime('%d-%m-%Y')
        
        # Location code cho Đà Nẵng là 10010083
        location_code = "10010083" if location.lower() == "đà nẵng" else location
        
        # Encode location name
        encoded_location = quote(location)
        
        # Tạo URL format: spec=check_in.check_out.2.adults.HOTEL_GEO.location_code.location_name.1
        url = f"{self.base_url}/hotel/search?spec={check_in_str}.{check_out_str}.2.{adults}.HOTEL_GEO.{location_code}.{encoded_location}.1"
        return url
        
    def build_car_rental_url(self, 
                            pickup_location: str,
                            pickup_date: datetime,
                            return_date: datetime,
                            with_driver: bool = False) -> str:
        # Format dates and times
        sd = pickup_date.strftime('%d-%m-%Y')  # start date
        ed = return_date.strftime('%d-%m-%Y')  # end date
        
        # Format time without leading zeros (9-0 format instead of 09-0)
        st = f"{int(pickup_date.strftime('%H'))}-0"     # start time
        et = f"{int(return_date.strftime('%H'))}-0"     # end time
        
        # Driver type
        driver_type = "WITH_DRIVER" if with_driver else "WITHOUT_DRIVER"
        
        # Encode location
        encoded_city = quote(pickup_location)
        
        # Location format từ ví dụ
        location_format = f"TVLK.91729745225769.POI.OTHER_LANDMARKS.Landmark.{quote(quote(pickup_location))}"
        coordinates = "16x04422617057296+108x22330563112595"  # Tọa độ Đà Nẵng
        
        url = (f"{self.base_url}/car-rental/search"
               f"?sd={sd}&st={st}&ed={ed}&et={et}"
               f"&driverType={driver_type}"
               f"&city={encoded_city}"
               f"&fromLocation={location_format}.%27%27.{coordinates}")
        return url

class GodyScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://gody.vn"
    
    def get_places(self, location: str) -> List[Dict]:
        url = f"{self.base_url}/explore/search?q={location}"
        soup = self.get_soup(url)
        
        places = []
        place_elements = soup.find_all("div", class_="place-item")
        
        for element in place_elements:
            place = {
                'name': element.find("h3", class_="place-name").text.strip(),
                'description': element.find("div", class_="description").text.strip(),
                'image': element.find("img")["src"],
                'rating': element.find("div", class_="rating").text.strip(),
                'link': self.base_url + element.find("a")["href"]
            }
            places.append(place)
            
        return places

class FoodyScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.foody.vn"
    
    def get_restaurants(self, location: str) -> List[Dict]:
        url = f"{self.base_url}/{location}/food"
        soup = self.get_soup(url)
        
        restaurants = []
        restaurant_elements = soup.find_all("div", class_="row-view-item")
        
        for element in restaurant_elements:
            restaurant = {
                'name': element.find("h2", class_="title").text.strip(),
                'address': element.find("div", class_="address").text.strip(),
                'price_range': element.find("div", class_="price-range").text.strip(),
                'rating': element.find("div", class_="point").text.strip(),
                'link': self.base_url + element.find("a")["href"]
            }
            restaurants.append(restaurant)
            
        return restaurants

def main():
    scraper = TravelokaScraper()
    
    print("=== BẮT ĐẦU TÌM KIẾM KHÁCH SẠN TẠI ĐÀ NẴNG ===")
    hotels = scraper.get_hotels(location="Đà Nẵng")
    
    if hotels:
        print(f"\nTìm thấy {len(hotels)} khách sạn:")
        for idx, hotel in enumerate(hotels, 1):
            print(f"\n{idx}. Khách sạn: {hotel['name']}")
            print(f"   Địa chỉ: {hotel['address']}")
            print(f"   Đánh giá: {hotel['rating']}")
            print(f"   Giá gốc: {hotel['price']}")
            print(f"   Tiện ích: {', '.join(hotel['features'])}")
    else:
        print("Không tìm thấy khách sạn nào!")

if __name__ == "__main__":
    main() 
