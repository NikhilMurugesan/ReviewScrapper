import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from deep_translator import GoogleTranslator
import time
import re
import os


def translate_if_needed(text):
    try:

        cleaned = re.sub(r'[^A-Za-z]', '', text)
        if cleaned and all(char.isalpha() and char.isascii() for char in cleaned):
            return text
        print(f"NEED Translation... {text} -----------------",GoogleTranslator(source='auto', target='en').translate(text))
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def scrape_google_maps_reviews(pincode, proxy=None):
    print(f"🚀 Starting scraping for PINCODE: {pincode}")
    options = Options()
    options.add_argument("--start-maximized")
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')

    service = Service("D:/LearningPython/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    print("🔎 Navigating to Google Maps...")
    driver.get(f"https://www.google.com/maps/search/courier+services+in+{pincode}")
    time.sleep(5)

    courier_data = []
    scrollable_div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.Nv2PK'))
    )

    actions = ActionChains(driver)
    attempts = 0
    print("🔃 Scrolling to load all listings...")
    while True:
        actions.move_to_element(scrollable_div).click().send_keys(Keys.END).perform()
        time.sleep(1.5)
        try:
            driver.find_element(By.XPATH, '//span[contains(text(), "You\'ve reached the end of the list.")]')
            print("✅ Reached end of listings.")
            break
        except NoSuchElementException:
            attempts += 1
            if attempts > 30:
                print("⚠️ Gave up after 30 scroll attempts.")
                break

    listings = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.Nv2PK'))
    )
    print(f"📦 Found {len(listings)} courier listings.")

    for i in range(len(listings)):
        try:
            print(f"\n➡️ Processing listing #{i + 1}...")
            listings = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            driver.execute_script("arguments[0].scrollIntoView();", listings[i])
            ActionChains(driver).move_to_element(listings[i]).click().perform()
            time.sleep(3)

            name = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'DUwDvf'))
            ).text
            print(f"🏢 Courier: {name}")

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
                print("💬 Opened review tab.")
                time.sleep(2)
            except:
                print(f"❌ Couldn't open reviews for {name}")
                continue

            print("🔃 Scrolling reviews...")
            try:
                scroll_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde'))
                )

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
                print(f"⚠️ Scroll error: {e}")
                continue

            reviews = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
            print(f"📝 Found {len(reviews)} reviews.")

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
                print("✅ Closed review popup.")
                time.sleep(1)
            except:
                print(f"⚠️ Couldn't close popup for {name}, going back...")
                driver.back()
                time.sleep(2)

        except Exception as e:
            print(f"❌ Error with listing #{i + 1}: {e}")
            traceback.print_exc()
            continue

    driver.quit()

    df = pd.DataFrame(courier_data)
    df.to_csv(f"courier_reviews_full_{pincode}.csv", index=False)
    print(f"\n✅ Scraped and saved {len(df)} reviews to courier_reviews_full_{pincode}.csv")


# ✅ Start scraping
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)
df = pd.DataFrame(courier_data)
df.to_csv(os.path.join(output_dir, f"courier_reviews_full_{pincode}.csv"), index=False)
print(f"✅ {pincode}: Saved {len(df)} reviews.")