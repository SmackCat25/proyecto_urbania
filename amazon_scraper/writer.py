import os
import csv
from amazon_scraper.config import OUTPUT_FILE_NAME

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def write_to_csv(data):
    if not data:
        print("No hay datos disponibles.")
        return

    fieldnames = data[0].keys()
    output_file = os.path.join(DATA_DIR, OUTPUT_FILE_NAME)
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
