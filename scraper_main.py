import os
import pandas as pd
import logging
import multiprocessing
from scrape_module import scrape_google_maps_reviews
from datetime import datetime
from tqdm import tqdm

def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f"scraper_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    return log_filename

def process_batch(pin_batch, headless, retries):
    for pincode in pin_batch:
        success = False
        for attempt in range(retries):
            try:
                logging.info(f"📦 Scraping {pincode} | Attempt {attempt + 1}")
                scrape_google_maps_reviews(pincode, headless=headless)
                success = True
                break
            except Exception as e:
                logging.error(f"❌ Error on {pincode}, attempt {attempt + 1}: {e}")
        if not success:
            logging.error(f"⚠️ Failed all retries for {pincode}")

def run_scraper(excel_file, batch_size, num_processes, headless=True, retries=2):
    df = pd.read_excel(excel_file)
    pin_list = df.iloc[:, 0].dropna().astype(str).tolist()

    logging.info(f"Total PINs: {len(pin_list)} | Batch Size: {batch_size} | Processes: {num_processes}")
    pin_batches = [pin_list[i:i + batch_size] for i in range(0, len(pin_list), batch_size)]

    with multiprocessing.Pool(num_processes) as pool:
        pool.starmap(process_batch, [(batch, headless, retries) for batch in pin_batches])

    # Combine individual CSVs
    combined = pd.DataFrame()
    for pincode in pin_list:
        file_path = f"courier_reviews_full_{pincode}.csv"
        if os.path.exists(file_path):
            if file_path.endswith(".csv"):
                df_pin = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx"):
                df_pin = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use .csv or .xlsx")
            combined = pd.concat([combined, df_pin], ignore_index=True)
    combined.to_csv("courier_reviews_combined.csv", index=False)
    logging.info("✅ Combined CSV saved as courier_reviews_combined.csv")

if __name__ == "__main__":
    log_file = setup_logger()
    logging.info("🚀 Starting scraper")
    run_scraper("sample_pincode_list.xlsx", batch_size=10, num_processes=4, headless=True, retries=3)
    logging.info("🏁 Scraper finished")