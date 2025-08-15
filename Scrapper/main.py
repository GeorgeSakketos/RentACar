import asyncio
from datetime import datetime
from herz_scrapper import hertzScrapper

async def main():
    hertz_url = "https://www.hertz.gr/en/car-rental/"
    
    # Pick Up (and Optional Drop-Off) Country and City
    different_drop_off = True
    country = "Greece"  # Desired country
    city = "Athens"      # Desired city
    
    # Pick-Up and Drop-Off Date and Time
    pickup_datetime = datetime.strptime("12/09/2025 16:45", "%d/%m/%Y %H:%M")
    dropoff_datetime = datetime.strptime("11/10/2025 11:15", "%d/%m/%Y %H:%M")
    
    manager = hertzScrapper(hertz_url, country, city, pickup_datetime, dropoff_datetime, duration=30, browser_type="chromium", different_drop_off=different_drop_off)
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main())