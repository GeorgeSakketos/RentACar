import asyncio
from herz_scrapper import hertzScrapper

async def main():
    hertz_url = "https://www.hertz.gr/en/car-rental/"
    country = "Greece"  # Desired country
    city = "Athens"      # Desired city
    pickup_date = "19/01/2026"  # dd/mm/yyyy
    pickup_time = "12:45"       # Intervals of 15 minutes
    dropoff_date = "12/02/2026" # dd/mm/yyyy
    dropoff_time = "11:15"      # Intervals of 15 minutes
    different_drop_off = True
    manager = hertzScrapper(hertz_url, country, city, pickup_date, pickup_time, dropoff_date, dropoff_time, duration=30, browser_type="chromium", different_drop_off=different_drop_off)
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main())