import asyncio
from datetime import datetime
from herz_scrapper import hertzScrapper
from safeguards import SafeGuards

async def main():
    hertz_url = "https://www.hertz.gr/en/car-rental/"
    
    # Pick Up (and Optional Drop-Off) Country and City
    different_drop_off = True
    country = "Greece"  # Desired country
    city = "Athens"      # Desired city
    
    # Pick-Up and Drop-Off Date and Time
    pickup_datetime = datetime.strptime("12/09/2025 16:45", "%d/%m/%Y %H:%M")
    dropoff_datetime = datetime.strptime("11/10/2025 11:15", "%d/%m/%Y %H:%M")
    
    # Companies To Use
    companies_list = ["Hertz", "Avis", "NoName"]
    
    # Validate Date and Time
    safeguard = SafeGuards(companies_list, pickup_datetime, dropoff_datetime)
    await safeguard.safeguard()
    
    hertz_manager = hertzScrapper(hertz_url, country, city, pickup_datetime, dropoff_datetime, duration=15, browser_type="chromium", different_drop_off=different_drop_off)
    await hertz_manager.start()

if __name__ == "__main__":
    asyncio.run(main())