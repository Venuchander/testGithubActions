import csv
import subprocess
import sys
from datetime import datetime
import os
import shutil
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("rerun_log.log")]
)

def check_and_rerun_if_all_n():
    """
    Check all rows in the specified columns of the CSV file.
    If all values are 'N', rerun the script; otherwise, do not rerun.
    """
    columns_to_check = [
        'Email Confirmed',
        'Experienced Buyer',
        'Complete Order via RFQ',
        'Typical Replies',
        'Interactive User'
    ]

    try:
        # Open the CSV file
        with open('testOutput.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Check if columns exist
            missing_columns = [col for col in columns_to_check if col not in reader.fieldnames]
            if missing_columns:
                logging.error(f"Missing columns in CSV: {missing_columns}")
                return

            # Flag to track if all values are 'N'
            all_n = True

            # Check every row for 'Y'
            for row in reader:
                if any(row.get(column, '').strip().upper() == 'Y' for column in columns_to_check):
                    logging.info(f"Found 'Y' in column(s). No rerun needed.")
                    all_n = False
                    break

            # Decide based on the check
            if all_n:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f'testOutput_{timestamp}.csv'

                logging.info(f"All specified columns are 'N'. Rerunning main.py and saving output as {new_filename}...")

                # Run main.py
                result = subprocess.run([sys.executable, r'E:\Files\Code\Venuchander\Internship\Alibaba\Main1\main.py'], 
                                        capture_output=True, text=True)

                # Check subprocess execution
                if result.returncode == 0:
                    logging.info("main.py executed successfully.")
                    if os.path.exists('testOutput.csv'):
                        shutil.move('testOutput.csv', new_filename)
                        logging.info(f"File saved as {new_filename}")
                    else:
                        logging.warning("No testOutput.csv file was created after rerun.")
                else:
                    logging.error(f"main.py execution failed: {result.stderr}")
            else:
                logging.info("Rerun skipped due to presence of 'Y'.")

    except FileNotFoundError:
        logging.warning("testOutput.csv not found. Rerunning main.py...")
        result = subprocess.run([sys.executable, r'E:\Files\Code\Venuchander\Internship\Alibaba\Main1\main.py'], 
                                capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("main.py executed successfully.")
        else:
            logging.error(f"main.py execution failed: {result.stderr}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    check_and_rerun_if_all_n()
