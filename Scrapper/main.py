import asyncio
from herz_scrapper import hertzScrapper

async def main():
    hertz_url = "https://www.hertz.gr/en/car-rental/"
    country = "Greece"  # Desired country
    city = "Athens"      # Desired city
    manager = hertzScrapper(hertz_url, country, city, duration=10, browser_type="chromium", different_drop_off=True)
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main())