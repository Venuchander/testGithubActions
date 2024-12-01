import csv


def read_csv(file_path):
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)


def write_csv(file_path, rows, fieldnames):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compare_and_remove_rows(yesterday_file, today_file):
    
    yesterday_data = read_csv(yesterday_file)
    today_data = read_csv(today_file)

    
    yesterday_inquiry_ids = set(row['Inquiry ID'] for row in yesterday_data)

    
    duplicates = [row for row in today_data if row['Inquiry ID'] in yesterday_inquiry_ids]

    
    updated_today_data = [row for row in today_data if row['Inquiry ID'] not in yesterday_inquiry_ids]

    
    if duplicates:
        print("Duplicates found:")
        for duplicate in duplicates:
            print(duplicate)
    else:
        print("No duplicates found.")

    
    if today_data:
        fieldnames = today_data[0].keys()

        
        write_csv(today_file, updated_today_data, fieldnames)

    print(f"Updated today's CSV with {len(updated_today_data)} rows remaining.")


yesterday_file = 'yesterday.csv'
today_file = 'today.csv'


compare_and_remove_rows(yesterday_file, today_file)
