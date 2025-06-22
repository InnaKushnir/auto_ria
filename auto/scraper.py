import os
import time
import datetime
import subprocess
import requests
import json
import re
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.utils import timezone
from auto.models import Auto

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_URL = "https://auto.ria.com/car/used"


def get_page(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_image_info(driver):
    image_url = ""
    images_count = 0

    try:
        photo_block = driver.find_element(By.ID, "photosBlock")

        try:
            first_img = photo_block.find_element(By.CSS_SELECTOR, "img.outline")
            image_url = first_img.get_attribute("src")
        except Exception as e:
            print(f"Exception {e}")
        try:
            all_photos_link = photo_block.find_element(By.CSS_SELECTOR, "a.show-all")
            text = all_photos_link.text
            match = re.search(r"(\d+)", text)
            if match:
                images_count = int(match.group(1))
        except:
            pass

    except Exception as e:
        print(f"❌ Exception {e}")
    if images_count == 0 and image_url != "":
        images_count = 1

    return image_url, images_count


def get_full_phone_and_username(url):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import time

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    username = ""
    phone = 0
    image_url = ""
    images_count = 0

    try:
        driver.get(url)
        time.sleep(2)

        try:
            overlay = driver.find_element(By.CLASS_NAME, "fc-dialog-overlay")
            if overlay.is_displayed():
                driver.execute_script(
                    "document.querySelector('.fc-dialog-overlay').remove()"
                )
        except:
            pass
        try:
            consent = driver.find_element(By.CLASS_NAME, "fc-consent-root")
            if consent.is_displayed():
                driver.execute_script(
                    "document.querySelector('.fc-consent-root').remove()"
                )
        except:
            pass
        try:
            img_el = driver.find_element(
                By.CSS_SELECTOR, "#showLeftBarView .seller_info_img img"
            )
            username = img_el.get_attribute("alt").strip()

        except Exception as e:
            print(f"❌ Exception {e}")

        try:
            show_btn = driver.find_element(
                By.CSS_SELECTOR, "#showLeftBarView .phone_show_link"
            )
            driver.execute_script("arguments[0].scrollIntoView();", show_btn)
            show_btn.click()
            time.sleep(2)
        except Exception as e:
            print(f"❌ Exception {e}")

        try:
            phone_span = driver.find_element(
                By.CSS_SELECTOR, "#showLeftBarView .phone.bold"
            )
            phone = phone_span.get_attribute("data-phone-number").strip()
            phone = clean_phone_number(phone)
        except Exception as e:
            print(f"❌ Exception {e}")

        image_url, images_count = get_image_info(driver)

    except Exception as e:
        print(f"⚠️Exception {e}")
    finally:
        driver.quit()

    return username, phone, image_url, images_count


def clean_phone_number(raw):
    digits = re.sub(r"\D", "", raw)

    if digits.startswith("0"):
        digits = "38" + digits

    return f"{digits}"


def parse_listing_links(soup):
    return list(
        set(
            a["href"]
            for a in soup.select("a.m-link-ticket")
            if a.get("href", "").startswith("https://auto.ria.com/auto_")
        )
    )


def parse_next_page(soup):
    nxt = soup.select_one("a.next")
    return nxt["href"] if nxt else None


def parse_details(url):
    soup = get_page(url)
    data = {"url": url}

    for dd in soup.select("dd"):
        label = dd.select_one("span.label")
        arg = dd.select_one("span.argument")
        if not label or not arg:
            continue
        key = label.get_text(strip=True)
        value = arg.get_text(" ", strip=True)
        if key == "Марка, модель, год":
            data["title"] = value

    vin_tag = soup.select_one(".label-vin")
    data["car_vin"] = vin_tag.get_text(strip=True) if vin_tag else ""

    car_number_tag = soup.select_one("span.state-num.ua")
    data["car_number"] = ""
    if car_number_tag:
        car_number = car_number_tag.contents[0].strip()
        data["car_number"] = car_number

    price_tag = soup.select_one("section.price .price_value strong")
    if price_tag:
        price_text = price_tag.get_text(strip=True)
        price_clean = (
            price_text.replace(" ", "")
            .replace("\xa0", "")
            .replace("$", "")
            .replace("грн", "")
            .replace("€", "")
            .replace("договірна", "")
            .replace("договорная", "")
            .replace("не вказано", "")
            .strip()
        )
        try:
            data["price_usd"] = int(price_clean)
        except ValueError:
            data["price_usd"] = 0
    else:
        data["price_usd"] = 0

    odometer_tag = soup.select_one("div.base-information span.size18")
    if odometer_tag:
        try:
            odometer_text = (
                odometer_tag.get_text(strip=True).replace(" ", "").replace(" ", "")
            )
            data["odometer"] = int(odometer_text) * 1000
        except ValueError:
            data["odometer"] = 0
    else:
        data["odometer"] = 0

    username, phone, image_url, images_count = get_full_phone_and_username(url)
    data["username"] = username
    data["phone_number"] = phone
    data["image_url"] = image_url
    data["images_count"] = images_count

    return data


def is_valid_listing_page(soup):
    return bool(soup.select("a.m-link-ticket"))


def run_scraper():
    page = 1
    seen = set()

    while True:
        url = START_URL if page == 1 else f"{START_URL}/?page={page}"

        try:
            soup = get_page(url)
        except Exception as e:
            print(f"❌ Error loading page {url}: {e}")
            break

        if not is_valid_listing_page(soup):
            print("ℹ️ No more listings found.")
            break

        links = parse_listing_links(soup)
        new_links = [
            link for link in links if link.startswith("https://") and link not in seen
        ]
        seen.update(new_links)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(parse_details, link): link for link in new_links}

            for future in as_completed(futures):
                link = futures[future]
                try:
                    details = future.result()
                    Auto.objects.create(**details)
                    print(f"✅ Parsed and saved: {link}")
                except Exception as e:
                    print(f"⚠️ Error parsing {link}: {e}")

        page += 1


def create_postgres_dump():
    dump_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dumps")
    os.makedirs(dump_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dump_file = os.path.join(dump_dir, f"db_dump_{timestamp}.sql")

    db_name = os.environ["POSTGRES_DB"]
    db_user = os.environ["POSTGRES_USER"]
    db_password = os.environ["POSTGRES_PASSWORD"]
    db_host = os.environ["POSTGRES_HOST"]
    db_port = os.environ["POSTGRES_PORT"]

    try:
        subprocess.run(
            [
                "pg_dump",
                "-U",
                db_user,
                "-h",
                db_host,
                "-p",
                db_port,
                db_name,
            ],
            env={**os.environ, "PGPASSWORD": db_password},
            stdout=open(dump_file, "w"),
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")
