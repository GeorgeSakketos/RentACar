import asyncio
from herz_scrapper import hertzScrapper

async def main():
    hertz_url = "https://www.hertz.gr/en/car-rental/"
    country = "Greece"  # Desired country
    city = "Athens"      # Desired city
    pickup_date = "19/07/2026"  # dd/mm/yyyy
    pickup_time = "10:15"       # Must match available option
    different_drop_off = True
    manager = hertzScrapper(hertz_url, country, city, pickup_date, pickup_time, duration=10, browser_type="chromium", different_drop_off=different_drop_off)
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main())