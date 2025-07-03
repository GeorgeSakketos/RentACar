import os
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from bs4 import BeautifulSoup
import time
import re

class BaseScraper:
    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)

    def scrape(self):
        """Override in subclasses. Should return a list of dict vehicle data."""
        raise NotImplementedError

    def close(self):
        self.driver.quit()

class HertzScraper(BaseScraper):
    BASE_URL = "https://www.hertz.gr/el/car-rental/autokinita/"

    def clean_name(self, name):
        return re.sub(r"ή παρόμοιο", "", name, flags=re.IGNORECASE).strip()

    def accept_cookies(self):
        try:
            time.sleep(3)
            accept_button = self.driver.find_element("css selector", ".onetrust-close-btn-handler")
            accept_button.click()
            print("Cookie banner accepted")
            time.sleep(2)
        except Exception:
            print("No cookie banner found or could not click")

    def scrape(self):
        self.driver.get(self.BASE_URL)
        time.sleep(7)

        self.accept_cookies()

        all_vehicles = []

        while True:
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.select(".b-vehicle__body")
            if not cards:
                print("No vehicles found, stopping.")
                break

            for card in cards:
                name_el = card.select_one(".b-vehicle__title")
                name = self.clean_name(name_el.get_text(strip=True)) if name_el else None

                passengers = None
                passenger_el = card.select_one(".icon-passenger")
                if passenger_el and passenger_el.parent:
                    passengers = passenger_el.parent.get_text(strip=True).split()[0]

                small_luggage = large_luggage = None
                for luggage_div in card.select(".b-vehicle__luggages .pair.bold"):
                    icon = luggage_div.select_one("i")
                    qty = luggage_div.select_one("span")
                    if not icon or not qty:
                        continue
                    qty_text = qty.get_text(strip=True)
                    if "icon-suitcase-large" in icon["class"]:
                        large_luggage = qty_text
                    elif "icon-suitcase" in icon["class"]:
                        small_luggage = qty_text

                ac = None
                ac_div = card.select_one(".icon-ac")
                if ac_div and ac_div.parent:
                    ac_text = ac_div.parent.get_text(strip=True)
                    ac = "Με κλιματισμό" in ac_text

                transmission = None
                trans_div = card.select_one(".icon-transmission")
                if trans_div and trans_div.parent:
                    trans_text = trans_div.parent.get_text(strip=True).lower()
                    if "με ταχύτητες" in trans_text:
                        transmission = "Manual"
                    elif "αυτόματο" in trans_text:
                        transmission = "Automatic"

                all_vehicles.append({
                    "Vehicle Name": name,
                    "Number of Passengers": passengers,
                    "Small Luggages": small_luggage,
                    "Large Luggages": large_luggage,
                    "Has A/C": ac,
                    "Transmission": transmission
                })

            # Pagination: check next button
            try:
                next_button_li = self.driver.find_element("css selector", "li.b-pagination__item--next")
                next_button = next_button_li.find_element("css selector", "button.b-pagination__btn--next")
                disabled = next_button.get_attribute("disabled")
                if disabled is not None:
                    print("Next button disabled. Reached last page.")
                    break
                else:
                    print("Clicking next page...")
                    try:
                        next_button.click()
                    except ElementClickInterceptedException:
                        print("Click intercepted, trying JS click")
                        self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(7)
            except NoSuchElementException:
                print("Next button not found. Ending scraping.")
                break

        self.close()
        return all_vehicles

def save_to_db(vehicles, db_name):
    # Delete existing database file if present
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"Deleted existing database file: {db_name}")

    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_name TEXT,
            number_of_passengers INTEGER,
            small_luggages TEXT,
            large_luggages TEXT,
            has_ac BOOLEAN,
            transmission TEXT
        )
    ''')

    for v in vehicles:
        c.execute('''
            INSERT INTO vehicles (
                vehicle_name, number_of_passengers, small_luggages,
                large_luggages, has_ac, transmission
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            v["Vehicle Name"],
            int(v["Number of Passengers"]) if v["Number of Passengers"] and v["Number of Passengers"].isdigit() else None,
            v["Small Luggages"],
            v["Large Luggages"],
            1 if v["Has A/C"] else 0,
            v["Transmission"]
        ))

    conn.commit()
    conn.close()
    print(f"Saved {len(vehicles)} vehicles to database '{db_name}'")

def main():
    scrapers = [
        HertzScraper(headless=True),
        # Add other scrapers here later
    ]

    for scraper in scrapers:
        print(f"Starting scraper: {scraper.__class__.__name__}")
        vehicles = scraper.scrape()

        db_filename = f"{scraper.__class__.__name__.lower()}_vehicles.db"
        save_to_db(vehicles, db_filename)

if __name__ == "__main__":
    main()
