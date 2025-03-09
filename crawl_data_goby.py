# import json
# from urllib.parse import quote
# from urllib.parse import urlencode
# from time import sleep
# import random
# import requests
# from requests.exceptions import HTTPError
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.common.by import By

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# import time
# import csv

# from selenium import webdriver
# from selenium_stealth import stealth
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

# from selenium.webdriver.common.action_chains import ActionChains
# import time
# import random

# # #!/usr/bin/env python
# # print('If you get error "ImportError: No module named \'six\'" install six:\n'+\
# #     '$ sudo pip install six');
# # print('To enable your free eval account and get CUSTOMER, YOURZONE and ' + \
# #     'YOURPASS, please contact sales@brightdata.com')
# # import sys
# # if sys.version_info[0]==2:
# #     import six
# #     from six.moves.urllib import request
# #     opener = request.build_opener(
# #         request.ProxyHandler(
# #             {'http': 'http://brd-customer-hl_24c6f2cf-zone-datacenter_proxy1-country-us:lb4lnwckygqv@brd.superproxy.io:33335',
# #             'https': 'http://brd-customer-hl_24c6f2cf-zone-datacenter_proxy1-country-us:lb4lnwckygqv@brd.superproxy.io:33335'}))
# #     print(opener.open('https://geo.brdtest.com/welcome.txt').read())
# # if sys.version_info[0]==3:
# #     import urllib.request
# #     opener = urllib.request.build_opener(
# #         urllib.request.ProxyHandler(
# #             {'http': 'http://brd-customer-hl_24c6f2cf-zone-datacenter_proxy1-country-us:lb4lnwckygqv@brd.superproxy.io:33335',
# #             'https': 'http://brd-customer-hl_24c6f2cf-zone-datacenter_proxy1-country-us:lb4lnwckygqv@brd.superproxy.io:33335'}))
# #     print(opener.open('https://geo.brdtest.com/welcome.txt').read())

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options

# # Khởi tạo WebDriver
# chrome_driver_path = "/Users/thuyduc/Downloads/chromedriver-mac-arm64/chromedriver"  # Thay bằng đường dẫn thực tế

# # Cấu hình Selenium
# service = Service(chrome_driver_path)
# options = webdriver.ChromeOptions()

# # Khởi tạo trình duyệt
# driver = webdriver.Chrome(service=service, options=options)



# #proxy = '149.28.212.174'

# # Cấu hình Chrome
# #options.add_argument(f"--proxy-server={proxy}")  # Thiết lập proxy cho Chrome
# options.add_argument("--disable-blink-features=AutomationControlled")  # Ẩn dấu vết Selenium
# options.add_argument("--start-maximized")  # Mở trình duyệt toàn màn hình
# options.add_argument("--disable-popup-blocking")  # Tắt chặn popup
# options.add_argument("--disable-infobars")  # Ẩn thông báo "Chrome is being controlled"
# options.add_argument("--disable-notifications")  # Tắt thông báo từ trang web
# options.add_argument("--headless=new")  # Chạy chế độ headless mà không bị phát hiện (tuỳ chọn)


# driver = webdriver.Chrome(service=service, options=options)


# # Kích hoạt Selenium Stealth với Mac Apple Silicon
# stealth(driver,
#         languages=["en-US", "en"],
#         vendor="Apple Inc.",
#         platform="MacARM",  # Dành cho chip M1, M2, M3
#         webgl_vendor="Apple Inc.",
#         renderer="Apple GPU",
#         fix_hairline=True,
# )



# try:
    

#     # Truy cập URL
    
#     url = "https://gody.vn/chau-a/viet-nam/diem-du-lich"
#     driver.get(url)
    
#     # Đợi một chút để trang tải hoàn toàn (vì có nội dung động)
#     #time.sleep(3)
    
    
#     # Lấy tiêu đề trang

#     # title = driver.title
#     # print(f"Tiêu đề trang: {title}")
    
#     # Lấy tất cả các liên kết (tag <a>)
#     links = driver.find_elements(By.TAG_NAME, "a")
    
#     destination_list = {}
    
#     global writer

#     # Lưu dữ liệu vào file CSV
#     with open("crawled_data_completed.csv", "w", newline="", encoding="utf-8") as file:
#         writer = csv.writer(file)
#         writer.writerow(["Large_Destination", "Tourist_Destination", "Reviews", "Location", "Free?"])  # Tiêu đề cột
        
#     # get href link of each destination from VietNam href
#     for link in links:
#         href = link.get_attribute("href")
#         clas = link.get_attribute("class")  # Lấy URL
#         text = link.text.strip()
#         href = href + '/diem-du-lich'  # Lấy nội dung text
#         if href: # Chỉ lưu nếu có href
#             if clas.startswith("fc-white fs-20 fw-700 tt-capitalize"):
#                 destination_list[text] = href


#     # get href link of pages from each destination (like Bình Định,...)
#     for item in destination_list.keys():
#         new_url = destination_list[item]
#         driver.get(new_url)
#         new_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='sort=1&page=']")
#         lis = []
#         for new_link in new_links:
#             href = new_link.get_attribute("href") # lấy href của từng tag a có href chứa sort=1&page=
#             lis.append(href)
#         destination_list[item] = set(lis)
    
    
    
#     # get all info about tourist destination for each large destination (like Bình Định,...)
#     for key, value in destination_list.items():
#         for item in value:
#             driver.get(item)
#             time.sleep(3)
#             name_links = driver.find_elements(By.CSS_SELECTOR, 'a.fc-fourteenth fs-20 fw-600 lh-24 w-fit d-block pb-5') # get name of tourist destination
#             review_links = driver.find_elements(By.CSS_SELECTOR, 'span.w-fit d-block fc-fourteenth fs-14 fw-400 pb-5') # get review of tourist destination
#             location_links = driver.find_elements(By.CSS_SELECTOR, 'span.w-fit d-block fc-fourteenth fs-14 fw-400 ') # get location of tourist destination
#             free_links = driver.find_elements(By.CSS_SELECTOR, 'span.w-fit d-block fc-fourteenth fs-14 fw-400 pb-10') # get free (or not) of tourist destination
#             for a, b, c, d in zip(name_links, review_links, location_links, free_links):
#                 writer.writerow([key, a.text, b.text, c.text, d.text])
#             time.sleep(3)


# except Exception as e:
#     print(f"Đã xảy ra lỗi: {e}")

# finally:
#     # Đóng trình duyệt
#     driver.quit()



import csv
import time
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Khởi tạo WebDriver với cấu hình tối ưu
def init_driver():
    chrome_driver_path = "/Users/thuyduc/Downloads/chromedriver-mac-arm64/chromedriver"  # Đường dẫn đến ChromeDriver
    service = Service(chrome_driver_path)
    options = Options()
    
    # Cấu hình trình duyệt
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--headless=new")  # Chế độ ẩn trình duyệt
    
    driver = webdriver.Chrome(service=service, options=options)
    # Tăng thời gian chờ tải trang
    #driver.set_page_load_timeout(360)  # 300 giây (5 phút)

    
    # Tăng thời gian chờ tìm phần tử
    #driver.implicitly_wait(1)  # 30 giây
    # Kích hoạt Selenium Stealth để tránh bị phát hiện
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Apple Inc.",
            platform="MacARM",
            webgl_vendor="Apple Inc.",
            renderer="Apple GPU",
            fix_hairline=True)
    
    return driver

# Lấy danh sách điểm đến chính từ trang chủ
def get_main_destinations(driver, base_url):
    driver.get(base_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
    links = driver.find_elements(By.TAG_NAME, "a")
    
    destination_list = {}
    for link in links:
        href = link.get_attribute("href")
        clas = link.get_attribute("class")
        text = link.text.strip()
        if href and clas and clas.startswith("fc-white fs-20 fw-700 tt-capitalize"):
            destination_list[text] = href + "/diem-du-lich"
    
    return destination_list

# Lấy danh sách trang phân trang từ mỗi điểm đến lớn
def get_pagination_links(driver, destination_list):
    for item in destination_list.keys():
        driver.get(destination_list[item])
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        new_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='sort=1&page=']")
        destination_list[item] = {link.get_attribute("href") for link in new_links}
    
    return destination_list

# Lấy dữ liệu điểm du lịch từ mỗi trang
def scrape_tourist_data(driver, destination_list, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Large_Destination", "Tourist_Destination", "Reviews", "Location"])  # Tiêu đề cột
        
        for key, pages in destination_list.items():
            for page in pages:
                try:
                    driver.get(page)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                    
                    names = driver.find_elements(By.CSS_SELECTOR, "a.fc-fourteenth.fs-20.fw-600.lh-24.w-fit.d-block.pb-5")
                    reviews = driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400.pb-5")
                    locations = driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400")
                    
                    
                    location_list = []
                    name_list = []
                    review_list = []
                    #only get some locations info and free info that have unique icon
                    for location in locations:
                        icon = location.find_elements(By.CSS_SELECTOR, "i.fa.fa-map-marker.pr-5") 
                        if icon:
                            location_list.append(location.text.strip())
                    
                    for name, review in zip(names, reviews):
                        name_list.append(name.text)
                        review_list.append(review.text)
                    
                    for name, review, location in zip(name_list, review_list, location_list):
                        print("+")
                        writer.writerow([key, name, review, location])
                    
                    time.sleep(2)
                except TimeoutException:
                    print("Timeout! Thử lại...")
                    driver.refresh()
                

# def scrape_tourist_data(driver, destination_list, des_name: str):
#         for page in destination_list[des_name]:
#             driver.get(page)
#             WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
            
#             names = driver.find_elements(By.CSS_SELECTOR, "a.fc-fourteenth.fs-20.fw-600.lh-24.w-fit.d-block.pb-5")
#             reviews = driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400.pb-5")
#             locations = driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400")
            
            
#             location_list = []
#             name_list = []
#             review_list = []
#             #only get some locations info and free info that have unique icon
#             for location in locations:
#                 icon = location.find_elements(By.CSS_SELECTOR, "i.fa.fa-map-marker.pr-5") 
#                 if icon:
#                     location_list.append(location.text.strip())
            
#             for name, review in zip(names, reviews):
#                 name_list.append(name.text)
#                 review_list.append(review.text)
            
#             for name, review, location in zip(name_list, review_list, location_list):
#                 print(f"Name: {name}")
#                 print(f"Review: {review}")
#                 print(f"Location: {location}")
#                 print("=============================")
#             time.sleep(2)



# Chạy chương trình chính
if __name__ == "__main__":
    base_url = "https://gody.vn/chau-a/viet-nam/diem-du-lich"
    output_file = "crawled_data_test.csv"
    
    driver = init_driver()
    try:
        destinations = get_main_destinations(driver, base_url)
        paginated_destinations = get_pagination_links(driver, destinations)
        #scrape_tourist_data(driver, paginated_destinations, "Bình Định")
        scrape_tourist_data(driver, paginated_destinations, output_file)
    except Exception as e:
        print(f"Lỗi xảy ra: {e}")
    finally:
        driver.quit()
        print("Quá trình thu thập dữ liệu hoàn tất!")



# import csv
# import time
# from itertools import zip_longest
# from selenium import webdriver
# from selenium_stealth import stealth
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# def init_driver():
#     chrome_driver_path = "/Users/thuyduc/Downloads/chromedriver-mac-arm64/chromedriver"
#     service = Service(chrome_driver_path)
#     options = Options()
    
#     # Cấu hình trình duyệt tối ưu
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument("--headless=new")
#     options.add_argument("--start-maximized")
#     options.add_argument("--disable-popup-blocking")
#     options.add_argument("--disable-infobars")
#     options.add_argument("--disable-notifications")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    
#     driver = webdriver.Chrome(service=service, options=options)
#     stealth(driver, languages=["en-US", "en"], vendor="Apple Inc.", platform="MacARM", webgl_vendor="Apple Inc.", renderer="Apple GPU", fix_hairline=True)
    
#     return driver

# def get_main_destinations(driver, base_url):
#     driver.get(base_url)
#     try:
#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
#         links = driver.find_elements(By.TAG_NAME, "a")
#         return {link.text.strip(): link.get_attribute("href") + "/diem-du-lich" for link in links if link.get_attribute("class") and link.get_attribute("class").startswith("fc-white fs-20 fw-700 tt-capitalize")}
#     except Exception as e:
#         print(f"Lỗi khi lấy danh sách điểm đến: {e}")
#         return {}

# def get_pagination_links(driver, destination_list):
#     for destination, url in destination_list.items():
#         driver.get(url)
#         try:
#             WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
#             new_links = {link.get_attribute("href") for link in driver.find_elements(By.CSS_SELECTOR, "a[href*='sort=1&page=']")}
#             destination_list[destination] = new_links if new_links else {url}  # Nếu không có phân trang, giữ nguyên URL chính
#         except Exception as e:
#             print(f"Lỗi khi lấy phân trang cho {destination}: {e}")
#             destination_list[destination] = {url}
#     return destination_list

# def scrape_tourist_data(driver, destination_list, output_file):
#     with open(output_file, "w", newline="", encoding="utf-8") as file:
#         writer = csv.writer(file)
#         writer.writerow(["Large_Destination", "Tourist_Destination", "Reviews", "Location", "Free?"])
        
#         for destination, pages in destination_list.items():
#             for page in pages:
#                 driver.get(page)
#                 try:
#                     WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
#                     names = [el.text for el in driver.find_elements(By.CSS_SELECTOR, "a.fc-fourteenth.fs-20.fw-600.lh-24.w-fit.d-block.pb-5")]
#                     reviews = [el.text for el in driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400.pb-5")]
#                     locations = [el.text for el in driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400 i.fa.fa-map-marker.pr-5")]  
#                     free_info = [el.text if el.find_elements(By.CSS_SELECTOR, "i.fa.fa-usd.pr-5") else "None" for el in driver.find_elements(By.CSS_SELECTOR, "span.w-fit.d-block.fc-fourteenth.fs-14.fw-400.pb-10")]
                    
#                     # Đồng bộ danh sách với zip_longest (nếu danh sách có độ dài khác nhau)
#                     for name, review, location, free in zip_longest(names, reviews, locations, free_info, fillvalue="Không rõ"):
#                         writer.writerow([destination, name, review, location, free])
#                         print(f"+ {name} ({location})")
#                 except Exception as e:
#                     print(f"Lỗi khi thu thập dữ liệu từ {page}: {e}")
#                 time.sleep(2)  # Tránh bị khóa IP vì request quá nhanh

# if __name__ == "__main__":
#     base_url = "https://gody.vn/chau-a/viet-nam/diem-du-lich"
#     output_file = "crawled_data_committed.csv"
    
#     driver = init_driver()
#     try:
#         destinations = get_main_destinations(driver, base_url)
#         paginated_destinations = get_pagination_links(driver, destinations)
#         scrape_tourist_data(driver, paginated_destinations, output_file)
#     except Exception as e:
#         print(f"Lỗi tổng quát: {e}")
#     finally:
#         driver.quit()
#         print("Quá trình thu thập dữ liệu hoàn tất!")
