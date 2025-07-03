from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from bs4 import BeautifulSoup
import time
import re

def clean_name(name):
    return re.sub(r"ή παρόμοιο", "", name, flags=re.IGNORECASE).strip()

def fetch_vehicles_by_pagination():
    url = "https://www.hertz.gr/el/car-rental/autokinita/"
    all_vehicles = []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(7)  # wait for initial page load

    # Handle cookie banner if present
    try:
        time.sleep(3)  # wait for cookie banner to appear
        accept_button = driver.find_element("css selector", ".onetrust-close-btn-handler")
        accept_button.click()
        print("Cookie banner accepted")
        time.sleep(2)  # wait for banner to disappear
    except Exception:
        print("No cookie banner found or could not click")

    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select(".b-vehicle__body")
        if not cards:
            print("No vehicles found, stopping.")
            break

        for card in cards:
            name_el = card.select_one(".b-vehicle__title")
            name = clean_name(name_el.get_text(strip=True)) if name_el else None

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

        # Find the next button and check if disabled
        try:
            next_button_li = driver.find_element("css selector", "li.b-pagination__item--next")
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
                    driver.execute_script("arguments[0].click();", next_button)
                time.sleep(7)  # wait for next page to load
        except NoSuchElementException:
            print("Next button not found. Ending scraping.")
            break

    driver.quit()
    return all_vehicles

if __name__ == "__main__":
    vehicles = fetch_vehicles_by_pagination()
    for v in vehicles:
        print(v)
