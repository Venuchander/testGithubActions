import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time
import re
from collections import defaultdict
from tqdm import trange

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class AlibabaRFQScraper:
    def __init__(self, headless=False):
        self.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("Scraper initialized successfully")
        
    def setup_driver(self, headless):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        if headless:
            options.add_argument('--headless')
        
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-notifications')
        options.add_argument("--disable-software-rasterizer") 
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise

    def get_buyer_image(self, item):
        try:
            img_element = item.find_element(By.XPATH, ".//div[contains(@class, 'img-con')]//img")
            return img_element.get_attribute('src') or ''
        except NoSuchElementException:
            return ''

    def safe_extract(self, parent, xpath, attribute=None):
        try:
            element = parent.find_element(By.XPATH, xpath)
            return element.get_attribute(attribute) if attribute else element.text.strip()
        except Exception as e:
            
            return ""

    def get_quantity_required(self, item):
        try:
            quantity_num = item.find_element(By.XPATH, ".//span[contains(@class, 'brh-rfq-item__quantity-num')]").text
            unit_element = item.find_element(By.XPATH, ".//span[contains(@class, 'brh-rfq-item__quantity')]/following-sibling::span")
            unit_text = unit_element.text if unit_element else "Units"
            return f"{quantity_num} {unit_text}"
        except Exception as e:
            
            return "Not specified"

    def get_description_and_attach(self, url):

        desc, image, time1 = "", "", ""
        try:
            self.driver.get(url)
            time.sleep(3)
            script_element = self.driver.find_element(By.XPATH, "//script[contains(text(), 'enDescription')]")
            script_text = script_element.get_attribute('innerHTML')
            match = re.search(r"enDescription\s*:\s*\"(.*?)\"", script_text)
            if match:
                description = match.group(1)
                description = bytes(description, "utf-8").decode("unicode_escape")
                description = description.replace('\n', ' ').replace('\r', ' ')
                desc =  description.strip()
        except Exception as e:
            
            pass

        try:
           
            label_element = self.driver.find_element(
                By.XPATH, 
                "//div[@class='label' and text()='Attachments']"
            )
            
            
            if label_element:
                image_elements = self.driver.find_elements(
                By.XPATH, 
                "//div[@class='brh-at-item-pic-wrap']//img"
            )
                
            for image_element in image_elements:
                image_link = image_element.get_attribute("src")
                if image_link:
                    if image:
                        image += " " + image_link  
                    else:
                        image = image_link
            if image:
                image = image.strip()
                
        except Exception as e:
            
            pass
            
        try:
            
            datetime_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'datetime')]")
            date_text = datetime_element.find_element(By.XPATH, "./span").text.strip()
            timezone_text = datetime_element.text.strip()
            time1 =  f"{date_text} {timezone_text}"
        except Exception as e:
            
            pass
        
        def clean_category_name(name):
            return re.sub(r'\d+|Results', '', name).strip()


        categories = {'Main Category': '', 'Subcategory': '', 'Subsubcategory': '', 'Fourth Category': ''}
        try:
            breadcrumb_items = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'next-breadcrumb-item')]/a")
            
            if len(breadcrumb_items) >= 3:
                categories['Main Category'] = clean_category_name(breadcrumb_items[2].text.strip())
            if len(breadcrumb_items) >= 4:
                categories['Subcategory'] = clean_category_name(breadcrumb_items[3].text.strip())
            if len(breadcrumb_items) >= 5:
                categories['Subsubcategory'] = clean_category_name(breadcrumb_items[4].text.strip())
            if len(breadcrumb_items) >= 6:
                categories['Fourth Category'] = clean_category_name(breadcrumb_items[5].text.strip())
        except Exception as e:
            
            pass

        return desc, image, time1, categories
        

    def extract_unique_rfq_data(self, items):
        rfq_dict = defaultdict(lambda: defaultdict(set))
        processed_count = 0

        for item in items:
            try:
                inquiry_id = self.safe_extract(item, ".//a[contains(@href, 'rfq_detail')]", 'href')
                if not inquiry_id:
                    continue
                
                match = re.search(r'p=([^&]+)', inquiry_id)
                if not match:
                    continue
                
                id_key = match.group(1)
                
                rfq_dict[id_key]['title'].add(self.safe_extract(item, ".//a[contains(@href, 'rfq_detail')]", 'title'))
                rfq_dict[id_key]['buyer_name'].add(self.safe_extract(item, ".//div[contains(@class, 'buyer-name') or contains(@class, 'text')]"))
                rfq_dict[id_key]['buyer_image'].add(self.get_buyer_image(item))
                rfq_dict[id_key]['inquiry_time'].add(self.safe_extract(item, ".//div[contains(@class, 'publishtime')]").replace('Date Posted:', '').strip())
                rfq_dict[id_key]['quotes_left'].add(self.safe_extract(item, ".//div[contains(@class, 'quote-left')]/span"))
                rfq_dict[id_key]['quantity_required'].add(self.get_quantity_required(item))
                
                
                country = self.safe_extract(item, ".//div[contains(@class, 'country')]")
                country = country.replace('Posted in:', '').strip()
                
                rfq_dict[id_key]['country'].add(country)
                rfq_dict[id_key]['url'].add(inquiry_id)         

                tag_elements = item.find_elements(By.XPATH, ".//div[contains(@class, 'next-tag-body')]")
                tag_texts = [tag.text.strip().lower() for tag in tag_elements]  

                rfq_dict[id_key]['email_confirmed'].add('Y' if 'email confirmed' in tag_texts else 'N')
                rfq_dict[id_key]['experienced_buyer'].add('Y' if 'experienced buyer' in tag_texts else 'N')
                rfq_dict[id_key]['complete_order_via_rfq'].add('Y' if 'complete order via rfq' in tag_texts else 'N')               
                rfq_dict[id_key]['typical_replies'].add('Y' if 'typically replies' in tag_texts else 'N')                
                rfq_dict[id_key]['interactive_user'].add('Y' if any('interactive' in tag for tag in tag_texts) else 'N')
                                
                processed_count += 1
            except Exception as e:
                
                pass

        logging.info(f"Processed {processed_count} items successfully")
        return rfq_dict

    def scrape_rfqs(self, url, max_retries=3):
        retry_count = 0
        while retry_count < max_retries:
            try:
                logging.info(f"Attempting to scrape URL: {url} (Attempt {retry_count + 1}/{max_retries})")
                self.driver.get(url)
                time.sleep(5)
                
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'rfq-item')]")))
                items = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'rfq-item')]")
                logging.info(f"Found {len(items)} RFQ items")
                return self.extract_unique_rfq_data(items)
            except TimeoutException:
                logging.warning("Timeout waiting for RFQ items to load")
                retry_count += 1
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error scraping RFQs: {str(e)}")
                retry_count += 1
                time.sleep(5)
        return []

    def save_to_csv(self, data, filename='alibaba_rfqs.csv'):
        if not data:
            logging.warning("No data to save")
            return

        headers = [
            'Inquiry ID', 'Title', 'Buyer Name', 'Buyer Image',
            'Inquiry Time', 'Quotes Left', 'Country', 'Quantity Required',
            'Image_Attachments', 'Main Category', 'Subcategory', 'Subsubcategory',
            'Fourth Category', 'Email Confirmed', 'Experienced Buyer',
            'Complete Order via RFQ', 'Typical Replies', 'Interactive User',
            'Inquiry URL', 'Description', 'Inquiry Date'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for rfq in data:
                writer.writerow(rfq)
        
        logging.info(f"Data successfully saved to {filename}")


    def close(self):
        try:
            self.driver.quit()
            logging.info("Browser closed successfully")
        except Exception as e:
            logging.error(f"Error closing browser: {str(e)}")

def main():
    start_time = time.time()
    url = 'https://sourcing.alibaba.com/rfq/rfq_search_list.htm?country=AE&recently=Y&quantityMin=49'
    scraper = None
    pages = int(input("Enter the number of pages to scrape: "))
    try:
        logging.info("Starting scraper...")
        processed_rfqs = []

        for i in trange(1, pages+1):
            url1 = url+"&page="+str(i)
            scraper = AlibabaRFQScraper(headless=True)
            rfq_data_dict = scraper.scrape_rfqs(url1)
                        
            for id_key, data in rfq_data_dict.items():
                try:
                    rfq = {
                        'Inquiry ID': id_key,
                        'Title': next(iter(data['title'] - {''}), ''),
                        'Buyer Name': next(iter(data['buyer_name'] - {''}), ''),
                        'Buyer Image': next(iter(data['buyer_image'] - {''}), ''),
                        'Inquiry Time': next(iter(data['inquiry_time'] - {''}), ''),
                        'Quotes Left': next(iter(data['quotes_left'] - {''}), ''),
                        'Country': next(iter(data['country'] - {''}), ''),
                        'Quantity Required': next(iter(data['quantity_required'] - {''}), ''),
                        'Email Confirmed': next(iter(data['email_confirmed'] - {''}), 'N'),
                        'Experienced Buyer': next(iter(data['experienced_buyer'] - {''}), 'N'),
                        'Complete Order via RFQ': next(iter(data['complete_order_via_rfq'] - {''}), 'N'),
                        'Typical Replies': next(iter(data['typical_replies'] - {''}), 'N'),
                        'Interactive User': next(iter(data['interactive_user'] - {''}), 'N'),
                        'Inquiry URL': next(iter(data['url'] - {''}), ''),
                        'Description': next(iter(data.get('description', {'Nil'})), 'Nil')
                    }
                    
                    rfq['Description'], rfq['Image_Attachments'], rfq['Inquiry Date'], categories = scraper.get_description_and_attach(rfq['Inquiry URL'])
                    rfq.update(categories)
                    rfq['Inquiry Date'] = rfq['Inquiry Date'].replace('(U.S. PST)', '').strip()
                    processed_rfqs.append(rfq)

                except Exception as e:                    
                    pass
        
            if scraper:
                scraper.close()
        
        if processed_rfqs:
            
            scraper.save_to_csv(processed_rfqs, filename='Govind.csv')
        else:
            logging.warning("No valid RFQ data to save")
        
        end_time = time.time()

        elapsed_time = end_time - start_time
        print("Elapsed time:", elapsed_time)
    except:
        logging.error(f"Error Processing")

if __name__ == "__main__":
    main()