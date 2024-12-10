import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WebScraper:
    def __init__(self, base_url, output_dir='page_data'):
        """
        Initialize the web scraper with base URL and output directory
        
        :param base_url: The base URL to scrape
        :param output_dir: Directory to save scraped data
        """
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        
        self.base_url = base_url
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        
        chrome_options = Options()
        
        chrome_options.add_argument("--headless")
        
        
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        
        self.driver.set_page_load_timeout(30)
    
    
    
    def extract_page_data(self, page_url):
        """
        Extract window.PAGE_DATA from a given URL using Selenium
        
        :param page_url: URL to scrape
        :return: Extracted PAGE_DATA or None
        """
        try:
            
            self.driver.get(page_url)
            
            
            time.sleep(10)
            
            
            page_data = self.driver.execute_script("""
                // Check if window.PAGE_DATA exists
                if (window.PAGE_DATA) {
                    // Convert to JSON string to safely transfer
                    return JSON.stringify(window.PAGE_DATA);
                }
                return null;
            """)
            
            if page_data and page_data != 'null':
                return json.loads(page_data)
            
            return None
        
        except Exception as e:
            print(f"Error extracting page data from {page_url}: {e}")
            return None
    
    def get_total_pages(self):
        """
        Determine the total number of pages to scrape using requests and BeautifulSoup
        
        :return: Total number of pages
        """
        print("Checking total number of pages...")
        try:
            response = requests.get(
                self.base_url, 
                headers=self.headers,
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
               
                
                pagination_links = soup.find_all("a", href=True)
               
                
                page_numbers = []
                for link in pagination_links:
                    try:
                        
                        page_numbers.append(int(link.text.strip()))
                    except ValueError:
                        continue  
               
                if page_numbers:
                    total_pages = max(page_numbers)
                    print(f"Total pages found: {total_pages}")
                    return total_pages
                else:
                    print("Could not find any valid page numbers.")
                    return 1
            else:
                print(f"Failed to fetch the page to determine total count. Status code: {response.status_code}")
                return 1
        except Exception as e:
            print(f"Error determining total pages: {e}")
            return 1

    
    
    def scrape_all_pages(self):
        """
        Scrape all pages and save their PAGE_DATA
        """
        
        total_pages = self.get_total_pages()
        print(f"Total pages to scrape: {total_pages}")
        
        
        for page in range(1, total_pages + 1):
            try:
                print(f"\nProcessing page {page}")
                
                
                page_url = f"{self.base_url}?page={page}"
                
                
                page_data = self.extract_page_data(page_url)
                
                if page_data:
                    
                    output_file = os.path.join(self.output_dir, f"page_data_{page}.js")
                    with open(output_file, "w", encoding="utf-8") as file:
                        
                        file.write(f"(function(){{\n    window.PAGE_DATA = {json.dumps(page_data, indent=2)};\n}})();")
                    print(f"Saved PAGE_DATA for page {page} to {output_file}")
                else:
                    print(f"No PAGE_DATA found on page {page}")
            
            except Exception as e:
                print(f"Error processing page {page}: {e}")
                continue
    
    def __del__(self):
        """
        Cleanup method to close the WebDriver
        """
        if hasattr(self, 'driver'):
            self.driver.quit()


def main():
    base_url = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm?country=AE&recently=Y&quantityMin=49"
    scraper = WebScraper(base_url)
    scraper.scrape_all_pages()

if __name__ == "__main__":
    main()