# run_parallel.py
import pandas as pd
from multiprocessing import Pool
import os
from scraper import scrape_google_maps_reviews

def run_batch(pin):
    try:
        scrape_google_maps_reviews(pin)
    except Exception as e:
        print(f"❌ Failed for PIN {pin}: {e}")

def combine_outputs():
    import glob
    all_files = glob.glob("outputs/courier_reviews_full_*.csv")
    df_list = [pd.read_csv(f) for f in all_files if os.path.getsize(f) > 0]
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        combined_df.to_csv("combined_output.csv", index=False)
        print(f"✅ Combined CSV created with {len(combined_df)} reviews.")
    else:
        print("⚠️ No review files found to combine.")

if __name__ == "__main__":
    excel_file = "sample_pincode_list.xlsx"
    df = pd.read_excel(excel_file)
    pin_codes = df.iloc[:, 0].astype(str).tolist()

    process_count = 4  # Adjust based on your CPU
    print(f"🔥 Starting multiprocessing with {process_count} workers...")

    with Pool(process_count) as pool:
        pool.map(run_batch, pin_codes)

    combine_outputs()
