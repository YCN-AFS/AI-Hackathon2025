import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class TravelDataCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_accommodation_data(self, location, criteria):
        """Thu thập dữ liệu về nơi ở từ Booking.com và Agoda"""
        accommodations = []
        
        # Crawl từ Booking.com
        booking_url = f"https://www.booking.com/search.html?ss={location}"
        response = requests.get(booking_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Logic xử lý dữ liệu từ Booking.com
        hotels = soup.find_all('div', class_='hotel_card')
        for hotel in hotels:
            hotel_data = {
                'name': hotel.find('h3').text.strip(),
                'address': hotel.find('address').text.strip(),
                'price': hotel.find('price').text.strip(),
                'rating': hotel.find('rating').text.strip(),
                'amenities': [a.text for a in hotel.find_all('amenity')]
            }
            accommodations.append(hotel_data)
            
        return accommodations

    def get_flight_data(self, destination, criteria):
        """Thu thập dữ liệu chuyến bay từ Skyscanner/Google Flights"""
        flights = []
        
        try:
            # Cập nhật ChromeOptions với nhiều tùy chọn hơn
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-extensions')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')
            options.add_argument('--disable-popup-blocking')
            options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            
            # Thêm preferences để tránh thông báo upgrade
            prefs = {
                'profile.default_content_setting_values.notifications': 2,
                'profile.default_content_settings.popups': 0,
                'profile.password_manager_enabled': False,
                'credentials_enable_service': False
            }
            options.add_experimental_option('prefs', prefs)
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Khởi tạo service với path đến ChromeDriver mới nhất
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Thêm JavaScript để tránh phát hiện automation
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Truy cập trang web
            driver.get(f"https://www.google.com/travel/flights?q=flights+to+{destination}")
            
            # Tăng thời gian chờ và thêm retry logic
            wait = WebDriverWait(driver, 20)
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    main_container = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[role="main"]')))
                    
                    # Scroll để load thêm content
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    flight_elements = driver.find_elements(
                        By.XPATH, '//div[contains(@aria-label, "flight")]')
                    
                    if flight_elements:
                        break
                        
                    retry_count += 1
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Lần thử {retry_count + 1} thất bại: {str(e)}")
                    retry_count += 1
                    time.sleep(2)
            
            # Xử lý dữ liệu chuyến bay
            for flight in flight_elements:
                try:
                    flight_data = {
                        'airline': flight.find_element(
                            By.XPATH, './/div[contains(@aria-label, "Airline")]').text,
                        'departure_time': flight.find_element(
                            By.XPATH, './/div[contains(@aria-label, "Departure")]').text,
                        'arrival_time': flight.find_element(
                            By.XPATH, './/div[contains(@aria-label, "Arrival")]').text,
                        'price': flight.find_element(
                            By.XPATH, './/div[contains(@aria-label, "Price")]').text
                    }
                    flights.append(flight_data)
                except Exception as e:
                    print(f"Lỗi khi xử lý chuyến bay: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Lỗi khi crawl dữ liệu chuyến bay: {str(e)}")
        
        finally:
            try:
                driver.quit()
            except:
                pass
            
        return flights

    def get_attractions(self, location, preferences):
        """Thu thập dữ liệu địa điểm du lịch từ TripAdvisor"""
        attractions = []
        
        tripadvisor_url = f"https://www.tripadvisor.com/Search?q={location}"
        response = requests.get(tripadvisor_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Logic xử lý dữ liệu từ TripAdvisor
        places = soup.find_all('div', class_='attraction_card')
        for place in places:
            place_data = {
                'name': place.find('h3').text.strip(),
                'description': place.find('description').text.strip(),
                'address': place.find('address').text.strip(),
                'rating': place.find('rating').text.strip(),
                'opening_hours': place.find('hours').text.strip()
            }
            attractions.append(place_data)
            
        return attractions

    def get_transportation_data(self, origin, destination):
        """Thu thập dữ liệu về giá taxi và thuê xe"""
        transport_data = {
            'taxi': [],
            'car_rental': []
        }
        
        # Logic crawl dữ liệu từ Grab/Uber API
        # Logic crawl dữ liệu từ các trang cho thuê xe
        
        return transport_data

    def get_restaurants(self, location, cuisine_type):
        """Thu thập dữ liệu về nhà hàng từ Foody/TripAdvisor"""
        restaurants = []
        
        # Logic crawl dữ liệu nhà hàng
        
        return restaurants

    def save_to_json(self, data, filename):
        """Lưu dữ liệu vào file JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    crawler = TravelDataCrawler()
    
    # Ví dụ sử dụng
    location = "Da Nang"
    accommodation_data = crawler.get_accommodation_data(location, {'price_range': '0-100'})
    flight_data = crawler.get_flight_data(location, {'airline': 'Vietnam Airlines'})
    attraction_data = crawler.get_attractions(location, {'type': 'beach'})
    
    # Lưu dữ liệu
    crawler.save_to_json(accommodation_data, 'accommodations.json')
    crawler.save_to_json(flight_data, 'flights.json')
    crawler.save_to_json(attraction_data, 'attractions.json')

if __name__ == "__main__":
    main()
