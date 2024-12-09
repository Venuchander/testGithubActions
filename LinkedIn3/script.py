#python script.py --input testOutput.csv --email vc2178@srmist.edu.in --password selenium
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re
import logging
import os
import urllib.parse
from selenium.common.exceptions import TimeoutException, WebDriverException

class LinkedInScraper:
    def __init__(self, email, password):
        logging.basicConfig(filename='error_log.txt', level=logging.INFO)
        self.email = email
        self.password = password
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def login(self):
        try:
            self.driver.get('https://www.linkedin.com/login')
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(self.email)
            
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(5)
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            raise

    def generate_search_url(self, name):
        """
        Generate LinkedIn search URL for a given name
        
        Args:
            name (str): Name to search on LinkedIn
        
        Returns:
            str: Encoded LinkedIn search URL
        """
        base_url = 'https://www.linkedin.com/search/results/people/'
        params = {
            'geoUrn': '["104305776"]',
            'keywords': name,
            'origin': 'FACETED_SEARCH',
            'sid': 'H0L'
        }
        
        # URL encode the name and other parameters
        encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"{base_url}?{encoded_params}"

    def get_result_count(self, name):
        try:
            # Generate and use the search URL
            search_url = self.generate_search_url(name)
            self.driver.get(search_url)
            time.sleep(3)  

            # Wait for and extract results count
            results_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.pb2.t-black--light.t-14"))
            )

            # Extract numeric results
            results_text = results_elem.text.strip()
            if results_text:
                match = re.search(r'\d+', results_text)
                if match:
                    return int(match.group()), search_url
                else:
                    logging.warning(f"No numeric results found for {name} in text: '{results_text}'")
                    return 0, search_url
            else:
                logging.warning(f"Empty results element for {name}.")
                return 0, search_url

        except Exception as e:
            logging.error(f"Error processing {name}: {str(e)}")
            return 0, self.generate_search_url(name)

    def process_file(self, input_file):
        try:
            self.login()
        except Exception:
            print("Login failed. Please check credentials.")
            return
        
        # Read the input file
        df = pd.read_csv(input_file)
        
        # Add new columns if they don't exist
        if 'Number of Results' not in df.columns:
            df['Number of Results'] = 0
        if 'LinkedIn URL' not in df.columns:
            df['LinkedIn URL'] = ''
        
        # Process each row
        for index, row in df.iterrows():
            name = row['Buyer Name']
            try:
                # Get result count and search URL
                count, search_url = self.get_result_count(name)
                
                # Update DataFrame
                df.at[index, 'Number of Results'] = count
                df.at[index, 'LinkedIn URL'] = search_url
                
                print(f"Processing {index+1}/{len(df)}: {name} - {count} results")
                
                # Add a small delay between searches
                time.sleep(2)
            
            except Exception as e:
                print(f"Error processing {name}: {str(e)}")
                logging.error(f"Error processing {name}: {str(e)}")
                
                # Even if there's an error, set results to 0
                df.at[index, 'Number of Results'] = 0
                df.at[index, 'LinkedIn URL'] = self.generate_search_url(name)
        
        # Save results back to the same input file
        df.to_csv(input_file, index=False)
        print(f"Results saved back to {input_file}")

    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--email', required=True, help='LinkedIn email')
    parser.add_argument('--password', required=True, help='LinkedIn password')
    args = parser.parse_args()
    
    scraper = LinkedInScraper(args.email, args.password)
    scraper.process_file(args.input)