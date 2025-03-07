from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from typing import Dict, List, Optional, Union

class WebScraper:
    def __init__(self, headless: bool = True):
        """
        Khởi tạo WebScraper với các tham số cơ bản
        
        Args:
            headless (bool): Chạy trình duyệt ở chế độ headless hay không
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Thiết lập logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Khởi tạo Playwright và trình duyệt"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.logger.info("Đã khởi tạo Playwright thành công")
        except Exception as e:
            self.logger.error(f"Lỗi khi khởi tạo Playwright: {str(e)}")
            raise

    def stop(self):
        """Dừng Playwright và đóng trình duyệt"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Đã dừng Playwright thành công")
        except Exception as e:
            self.logger.error(f"Lỗi khi dừng Playwright: {str(e)}")
            raise

    def navigate(self, url: str, wait_until: str = "networkidle"):
        """
        Điều hướng đến URL được chỉ định
        
        Args:
            url (str): URL cần truy cập
            wait_until (str): Điều kiện chờ để trang load xong
        """
        try:
            self.page.goto(url, wait_until=wait_until)
            self.logger.info(f"Đã truy cập URL: {url}")
        except Exception as e:
            self.logger.error(f"Lỗi khi truy cập URL {url}: {str(e)}")
            raise

    def get_page_content(self) -> str:
        """Lấy nội dung HTML của trang"""
        return self.page.content()

    def extract_data(self, selector: str, attribute: Optional[str] = None) -> List[str]:
        """
        Trích xuất dữ liệu từ trang web sử dụng CSS selector
        
        Args:
            selector (str): CSS selector để chọn phần tử
            attribute (str, optional): Thuộc tính cần lấy (nếu có)
            
        Returns:
            List[str]: Danh sách các giá trị được trích xuất
        """
        try:
            elements = self.page.query_selector_all(selector)
            if attribute:
                return [element.get_attribute(attribute) for element in elements]
            return [element.inner_text() for element in elements]
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất dữ liệu: {str(e)}")
            return []

    def save_to_csv(self, data: List[Dict], filename: str):
        """
        Lưu dữ liệu vào file CSV
        
        Args:
            data (List[Dict]): Dữ liệu cần lưu
            filename (str): Tên file CSV
        """
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.logger.info(f"Đã lưu dữ liệu vào file {filename}")
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu file CSV: {str(e)}")
            raise

    def wait_for_selector(self, selector: str, timeout: int = 30000):
        """
        Chờ cho đến khi phần tử xuất hiện trên trang
        
        Args:
            selector (str): CSS selector
            timeout (int): Thời gian chờ tối đa (ms)
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            self.logger.error(f"Lỗi khi chờ phần tử {selector}: {str(e)}")
            raise

    def scroll_to_bottom(self, wait_time: float = 1.0):
        """
        Cuộn trang xuống cuối
        
        Args:
            wait_time (float): Thời gian chờ giữa mỗi lần cuộn
        """
        try:
            self.page.evaluate("""() => {
                window.scrollTo(0, document.body.scrollHeight);
            }""")
            time.sleep(wait_time)
        except Exception as e:
            self.logger.error(f"Lỗi khi cuộn trang: {str(e)}")
            raise 