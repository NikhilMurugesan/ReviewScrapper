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

def translate_if_needed(text):
    cleaned = re.sub(r"[^A-Za-z]", "", text)
    if cleaned and not cleaned.isascii():
        try:
            return GoogleTranslator(source="auto", target="en").translate(text)
        except:
            return text
    return text

def scrape_google_maps_reviews(pincode, proxy=None, headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    service = Service("chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(f"https://www.google.com/maps/search/courier+services+in+{pincode}")
    time.sleep(5)

    courier_data = []
    actions = ActionChains(driver)
    attempts = 0

    while True:
        actions.send_keys(Keys.END).perform()
        time.sleep(1.5)
        try:
            driver.find_element(By.XPATH, '//span[contains(text(), "You\'ve reached the end of the list.")]')
            break
        except NoSuchElementException:
            attempts += 1
            if attempts > 30:
                break

    listings = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")

    for i in range(len(listings)):
        try:
            listings = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
            driver.execute_script("arguments[0].scrollIntoView();", listings[i])
            ActionChains(driver).move_to_element(listings[i]).click().perform()
            time.sleep(3)

            name = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))).text
            try:
                address = driver.find_element(By.CSS_SELECTOR, "div.Io6YTe.fontBodyMedium.kR99db.fdkmkc").text
            except NoSuchElementException:
                address = "N/A"
            try:
                overall_rating = driver.find_element(By.CSS_SELECTOR, "div.F7nice span").text
            except NoSuchElementException:
                overall_rating = "N/A"
            try:
                total_reviews_text = driver.find_element(By.XPATH, '//span[contains(@aria-label, "reviews")]').get_attribute("aria-label")
                total_reviews_count = int(total_reviews_text.split()[0])
            except:
                total_reviews_count = "N/A"

            try:
                review_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Reviews for')]"))
                )
                review_tab.click()
                time.sleep(2)
            except:
                continue

            try:
                scroll_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde"))
                )
                last_height = 0
                for _ in range(100):
                    reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                    if not reviews:
                        break
                    driver.execute_script("arguments[0].scrollIntoView();", reviews[-1])
                    time.sleep(1)
                    if len(reviews) == last_height:
                        break
                    last_height = len(reviews)
            except:
                continue

            reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
            for review in reviews:
                try:
                    review.find_element(By.CSS_SELECTOR, 'button[aria-label="See more"]').click()
                    time.sleep(0.2)
                except:
                    pass
                try:
                    reviewer_name = translate_if_needed(review.find_element(By.CLASS_NAME, "d4r55").text)
                except:
                    reviewer_name = "N/A"
                try:
                    review_date = review.find_element(By.CLASS_NAME, "rsqaWe").text
                except:
                    review_date = "N/A"
                try:
                    driver.execute_script("let response = arguments[0].querySelector('div.CDe7pd'); if (response) response.remove();", review)
                    review_text = translate_if_needed(review.find_element(By.CLASS_NAME, "wiI7pd").text)
                except:
                    review_text = "N/A"
                try:
                    star_rating = review.find_element(By.CLASS_NAME, "kvMYJc").get_attribute("aria-label")
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
                driver.find_element(By.CSS_SELECTOR, "svg.NMm5M").click()
                time.sleep(1)
            except:
                driver.back()
                time.sleep(2)
        except:
            continue

    driver.quit()
    df = pd.DataFrame(courier_data)
    df.to_csv(f"courier_reviews_full_{pincode}.csv", index=False)