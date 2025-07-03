from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def fetch_vehicle_data():
    url = "https://www.hertz.gr/el/car-rental/autokinita/"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(7)  # wait for JS to render

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    vehicles = []

    for card in soup.select(".b-vehicle__body"):
        # Vehicle Name
        name_el = card.select_one(".b-vehicle__title")
        name = name_el.get_text(strip=True) if name_el else None

        # Passengers
        passengers = None
        passenger_el = card.select_one(".icon-passenger")
        if passenger_el and passenger_el.parent:
            passengers = passenger_el.parent.get_text(strip=True).split()[0]  # e.g. "5 επιβάτες" → "5"

        # Luggage
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

        # A/C
        ac = None
        ac_div = card.select_one(".icon-ac")
        if ac_div and ac_div.parent:
            ac_text = ac_div.parent.get_text(strip=True)
            ac = "Με κλιματισμό" in ac_text

        # Transmission
        transmission = None
        trans_div = card.select_one(".icon-transmission")
        if trans_div and trans_div.parent:
            trans_text = trans_div.parent.get_text(strip=True)
            if "με ταχύτητες" in trans_text.lower():
                transmission = "Manual"
            elif "αυτόματο" in trans_text.lower():
                transmission = "Automatic"

        vehicles.append({
            "Vehicle Name": name,
            "Number of Passengers": passengers,
            "Small Luggages": small_luggage,
            "Large Luggages": large_luggage,
            "Has A/C": ac,
            "Transmission": transmission
        })

    return vehicles

if __name__ == "__main__":
    results = fetch_vehicle_data()
    for v in results:
        print(v)
