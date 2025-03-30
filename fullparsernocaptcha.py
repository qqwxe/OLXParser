import time
import random
import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import os

CHROME_BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PROFILE_PATH = r"C:\Users\ВАШЕ НАЗВАНИЕ ПОЛЬЗОВАТЕЛЯ ЛОЛ\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE_NAME = "Default"

def get_catalog_links(base_url, pages):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/112.0.0.0 Safari/537.36"
    }
    ad_links = set()
    for page in range(1, pages + 1):
        url = f"{base_url}&page={page}" if "?" in base_url else f"{base_url}?page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка загрузки страницы {page}")
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/obyavlenie/" in href:
                if not href.startswith("http"):
                    href = "https://www.olx.ua" + href
                ad_links.add(href)
    return list(ad_links)

def get_phone_number_from_ad(ad_url, driver=None, delay_range=(2, 4)):
    phone = None
    title = None
    created_driver = False
    if driver is None:
        options = uc.ChromeOptions()
        options.binary_location = CHROME_BINARY_PATH
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
        options.add_argument(f"--profile-directory={CHROME_PROFILE_NAME}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Safari/537.36")
        driver = uc.Chrome(options=options)
        created_driver = True
    try:
        driver.get(ad_url)
        wait = WebDriverWait(driver, 20)
        time.sleep(random.uniform(1, 3))
        try:
            title_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
            title = title_elem.text.strip()
        except:
            title = "Название не найдено"
        button_selectors = [
            "button[data-cy='ad-contact-phone']",
            "button[data-testid='ad-contact-phone']",
            "button"
        ]
        show_btn = None
        for selector in button_selectors:
            try:
                show_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except:
                continue
        if show_btn:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_btn)
            time.sleep(random.uniform(1, 2))
            try:
                show_btn.click()
            except:
                driver.execute_script("arguments[0].click();", show_btn)
            time.sleep(random.uniform(*delay_range))
            phone_selectors = [
                "a[data-testid='contact-phone']",
                "span[data-testid='phone-number']"
            ]
            for selector in phone_selectors:
                try:
                    phone_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    phone = phone_elem.get_attribute("textContent").strip()
                    if phone:
                        break
                except:
                    continue
        else:
            print("Кнопка 'Показать номер' не найдена.")
    except Exception as e:
        print(f"Ошибка при обработке объявления {ad_url}: {e}")
    finally:
        if created_driver:
            driver.quit()
    return phone, title

def process_catalog(catalog_url, pages, filename="results.csv"):
    ad_links = get_catalog_links(catalog_url, pages)
    print(f"Найдено {len(ad_links)} объявлений.")
    results = []
    if filename:
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
    else:
        filename = "results.csv"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "phone", "title"])
        if not file_exists:
            writer.writeheader()
        
        driver = None
        for link in ad_links:
            print(f"Обработка: {link}")
            phone, title = get_phone_number_from_ad(link, driver)
            results.append({"url": link, "phone": phone, "title": title})
            writer.writerow({"url": link, "phone": phone, "title": title})
            f.flush()
            print(f"Данные сохранены в {filename}")
            time.sleep(random.uniform(3, 6))
        if driver:
            driver.quit()
    return results

if __name__ == "__main__":
    catalog_url = input("Введите URL каталога OLX: ").strip()
    pages = int(input("Введите количество страниц для парсинга: ").strip())
    filename = input("Введите имя файла для сохранения (например, results.csv): ").strip() or "results.csv"
    results = process_catalog(catalog_url, pages, filename)
    print("Обработка завершена.")
