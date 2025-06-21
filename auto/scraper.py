# scraper.py
import time
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from auto.models import Auto

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_URL = "https://auto.ria.com/car/used/"

def get_page(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def parse_listing_links(soup):
    return [
        a["href"] for a in soup.select('a.m-link-ticket')
        if a.get("href", "").startswith("https://auto.ria.com/auto_")
    ]

def parse_next_page(soup):
    nxt = soup.select_one('a.next')
    return nxt["href"] if nxt else None

def parse_details(url):
    soup = get_page(url)
    data = {}
    hidden = soup.find("div", {"data-id": True})
    data["url"] = url
    # data["title"] = soup.select_one(".ticket-title a").get_text(strip=True)
    # data["price_usd"] = int(soup.select_one(".price-ticket [data-main-price]")["data-main-price"])
    # data["odometer"] = int(soup.select_one(".js-race").get_text(strip=True).split()[0].replace(" ", ""))
    # data["car_vin"] = soup.select_one(".label-vin span").get_text(strip=True)
    # data["car_number"] = soup.select_one(".state-num").get_text(strip=True)
    # data["image_url"] = soup.select_one(".ticket-photo img")["src"]
    # data["images_count"] = len(soup.select(".photo-185x120 picture img"))
    # phone = soup.select_one(".seller-phone-selector")
    # data["phone_number"] = phone.get_text(strip=True) if phone else ""
    # data["username"] = soup.select_one(".seller-name-selector").get_text(strip=True)
    data["datetime_found"] = timezone.now()
    return data

def run_scraper():
    url = START_URL
    while url:
        soup = get_page(url)
        links = parse_listing_links(soup)
        for link in links:
            details = parse_details(link)
            Auto.objects.update_or_create(
                url=details["url"],
                defaults=details
            )
            time.sleep(1)
        url = parse_next_page(soup)
        time.sleep(2)
