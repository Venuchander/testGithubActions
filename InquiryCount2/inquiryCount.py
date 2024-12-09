import csv
from collections import defaultdict


def count_inquiries_and_update(file_path):
    
    user_inquiries = defaultdict(int)

    
    with open(file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        rows = list(csv_reader)
        
        
        for row in rows:
            user_name = row['Buyer Name']
            user_inquiries[user_name] += 1

    
    for row in rows:
        user_name = row['Buyer Name']
        row['Inquiry Count'] = user_inquiries[user_name]

    
    header = csv_reader.fieldnames + ['Inquiry Count']

    
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.DictWriter(file, fieldnames=header)
        
        
        csv_writer.writeheader()

        
        csv_writer.writerows(rows)

    print(f"Inquiry count has been added to {file_path}")


input_file_path = r'InquiryCount2\testOutput.csv'   


count_inquiries_and_update(input_file_path)
