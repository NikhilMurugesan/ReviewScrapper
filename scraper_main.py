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
    dfs = []
    csv_directory = 'outputs'
    for filename in os.listdir(csv_directory):
        if filename.endswith('.csv'):
            filepath = os.path.join(csv_directory, filename)
            try:
                df = pd.read_csv(filepath)
                dfs.append(df)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)

        # Save the combined DataFrame to a new CSV file
        output_filename = 'combined_data.csv'
        output_filepath = os.path.join(csv_directory, output_filename)
        combined_df.to_csv(output_filepath, index=False)
        print(f"Successfully combined CSV files into {output_filepath}")
    else:
        print("No CSV files found to combine.")
    logging.info("✅ Combined CSV saved as combined_data.csv")

if __name__ == "__main__":
    log_file = setup_logger()
    logging.info("🚀 Starting scraper")
    run_scraper("sample_pincode_list.xlsx", batch_size=20, num_processes=20, headless=True, retries=1)
    logging.info("🏁 Scraper finished")