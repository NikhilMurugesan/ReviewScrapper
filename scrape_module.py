import os
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from deep_translator import GoogleTranslator
import time
import re
import logging
import threading

def translate_if_needed(text):
    try:
        cleaned = re.sub(r'[^A-Za-z]', '', text)
        if cleaned and all(char.isalpha() and char.isascii() for char in cleaned):
            return text
        print(f"NEED Translation... {text} -----------------", GoogleTranslator(source='auto', target='en').translate(text))
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def scrape_google_maps_reviews(pincode, proxy=None, headless=False):
    thread_id = threading.get_ident()
    print(f"🚀 Thread-{thread_id}: Starting scraping for PINCODE: {pincode}")
    options = Options()
    if False:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')

    service = Service("D:/LearningPython/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"🔎 Thread-{thread_id}: Navigating to Google Maps...")
        driver.get(f"https://www.google.com/maps/search/courier+services+in+{pincode}")
        time.sleep(5)

        courier_data = []

        print(f"🔃 Thread-{thread_id}: Scrolling to load all listings...")
        last_height = 0
        for _ in range(100):
            listings = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            if not listings:
                break
            driver.execute_script("arguments[0].scrollIntoView();", listings[-1])
            time.sleep(1)
            if len(listings) == last_height:
                break
            last_height = len(listings)

        listings = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
        print(f"📦 Thread-{thread_id}: Found {len(listings)} courier listings.")

        i = 0
        while True:
            listings = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            if i >= len(listings):
                break  # no more listings to process

            try:
                print(f"\n➡️ Thread-{os.getpid()}: Processing listing #{i + 1} of {len(listings)}")
                driver.execute_script("arguments[0].scrollIntoView();", listings[i])
                ActionChains(driver).move_to_element(listings[i]).click().perform()
                time.sleep(3)
                try:
                    name = translate_if_needed(WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'DUwDvf'))
                    ).text)
                except:
                    name = "N/A"
                print(f"🏢 Thread-{thread_id}: Courier: {name}")

                try:
                    address = driver.find_element(By.CSS_SELECTOR, 'div.Io6YTe.fontBodyMedium.kR99db.fdkmkc').text
                except NoSuchElementException:
                    address = "N/A"

                try:
                    overall_rating = driver.find_element(By.CSS_SELECTOR, "div.F7nice span").text
                except NoSuchElementException:
                    overall_rating = "N/A"

                try:
                    total_reviews_element = driver.find_element(By.XPATH, '//span[contains(@aria-label, "reviews")]')
                    total_reviews_text = total_reviews_element.get_attribute("aria-label")
                    total_reviews_count = int(total_reviews_text.split()[0])
                except Exception:
                    total_reviews_count = "N/A"

                try:
                    review_tab = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Reviews for')]"))
                    )
                    review_tab.click()
                    print(f"💬 Thread-{thread_id}: Opened review tab.")
                    time.sleep(2)
                except:
                    print(f"❌ Thread-{thread_id}: Couldn't open reviews for {name}")
                    i=i+1
                    continue

                print(f"🔃 Thread-{thread_id}: Scrolling reviews...")
                try:
                    last_height = 0
                    for _ in range(100):
                        reviews = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
                        if not reviews:
                            break
                        driver.execute_script("arguments[0].scrollIntoView();", reviews[-1])
                        time.sleep(1)
                        if len(reviews) == last_height:
                            break
                        last_height = len(reviews)
                except Exception as e:
                    print(f"⚠️ Thread-{thread_id}: Scroll error: {e}")
                    continue

                reviews = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
                print(f"📝 Thread-{thread_id}: Found {len(reviews)} reviews.")

                for review in reviews:
                    try:
                        more_button = review.find_element(By.CSS_SELECTOR, 'button[aria-label="See more"]')
                        more_button.click()
                        time.sleep(0.2)
                    except:
                        pass
                    try:
                        reviewer_name = translate_if_needed(review.find_element(By.CLASS_NAME, 'd4r55').text)
                    except:
                        reviewer_name = "N/A"
                    try:
                        review_date = review.find_element(By.CLASS_NAME, 'rsqaWe').text
                    except:
                        review_date = "N/A"
                    try:
                        driver.execute_script("""
                            let response = arguments[0].querySelector('div.CDe7pd');
                            if (response) response.remove();
                        """, review)
                        review_text = translate_if_needed(review.find_element(By.CLASS_NAME, 'wiI7pd').text)
                    except:
                        review_text = "N/A"
                    try:
                        star_rating = review.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute("aria-label")
                    except:
                        star_rating = "N/A"

                    courier_data.append({
                        "Courier Name": name,
                        "Address": address,
                        "Pincode": pincode,
                        "Overall Rating": overall_rating,
                        "Review Count": total_reviews_count,
                        "Reviewer Name": reviewer_name,
                        "Review Date": review_date,
                        "Review": review_text,
                        "Reviewer Rating": star_rating
                    })

                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR, 'svg.NMm5M')
                    close_btn.click()
                    print(f"✅ Thread-{thread_id}: Closed review popup.")
                    time.sleep(1)
                except:
                    print(f"⚠️ Thread-{thread_id}: Couldn't close popup for {name}, going back...")
                    driver.back()
                    time.sleep(2)

            except Exception as e:
                print(f"❌ Thread-{thread_id}: Error with listing #{i + 1}: {e}")
                traceback.print_exc()
                continue
            i += 1

        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(courier_data)
        df.to_csv(os.path.join(output_dir, f"courier_reviews_full_{pincode}.csv"), index=False)
        print(f"✅ Thread-{thread_id}: {pincode}: Saved {len(df)} reviews.")
        print(f"\n✅ Thread-{thread_id}: Scraped and saved {len(df)} reviews to courier_reviews_full_{pincode}.csv")

    except Exception as top_level:
        print(f"🔥 Thread-{thread_id}: Failed to scrape for PINCODE {pincode}: {top_level}")
        traceback.print_exc()
    finally:
        try:
            print("🧹 Clearing cache and quitting driver...")
            driver.delete_all_cookies()  # Clear session cookies
            driver.quit()  # Close the browser and kill chromedriver
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
