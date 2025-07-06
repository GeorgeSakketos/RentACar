import asyncio
from playwright.async_api import async_playwright

# ---- CONFIG ----
PICKUP_LOCATION = "Athens Airport"
PICKUP_DATE = "08/09/2025"    # Format DD/MM/YYYY
PICKUP_TIME = "12:02"          # Adjust format to HH:MM with colon
DROPOFF_DATE = "12/07/2025"   # Format DD/MM/YYYY
DROPOFF_TIME = "10:00"         # Format HH:MM

async def select_date(page, date_selector, date_str):
    # date_str is DD/MM/YYYY
    day, month, year = map(int, date_str.split("/"))
    # Click to open calendar
    await page.click(date_selector)
    await page.wait_for_timeout(500)

    # Select year
    await page.select_option(".pika-select-year", str(year))
    # Select month (months are zero-indexed)
    await page.select_option(".pika-select-month", str(month - 1))
    await page.wait_for_timeout(500)

    # Click the day button for the date
    day_selector = f'button.pika-button.pika-day[data-pika-year="{year}"][data-pika-month="{month - 1}"][data-pika-day="{day}"]'
    await page.click(day_selector)
    await page.wait_for_timeout(500)

async def fill_time(page, time_selector, time_str):
    await page.wait_for_selector(time_selector, state="visible", timeout=7000)
    await page.click(time_selector)
    await page.fill(time_selector, "")  # Clear input
    await page.fill(time_selector, time_str)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(500)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Open website
        await page.goto("https://www.avis.gr/")

        # Accept cookie popup
        try:
            await page.wait_for_selector("#consent_prompt_accept", timeout=7000)
            await page.click("#consent_prompt_accept")
            print("[INFO] Cookie accepted.")
        except Exception:
            print("[INFO] Cookie banner not found or already accepted.")

        # Close 'Θέλω Κράτηση' popup if present
        try:
            await page.wait_for_selector("#welcome-close", timeout=7000)
            await page.click("#welcome-close")
            print("[INFO] 'Θέλω Κράτηση' popup closed.")
        except Exception:
            print("[INFO] 'Θέλω Κράτηση' popup not found or already closed.")

        # Fill pickup location
        await page.fill("#hire-search", PICKUP_LOCATION)
        await page.wait_for_timeout(2000)  # Wait for autocomplete suggestions
        await page.keyboard.press("Enter")
        print("[INFO] Pickup location set.")

        # Set Pickup Date using calendar selection
        await select_date(page, "#date-from-display", PICKUP_DATE)

        # Set Pickup Time
        await fill_time(page, "#time-from-display", PICKUP_TIME)
        print("[INFO] Pickup date/time set.")

        # Set Drop-off Date using calendar selection
        await select_date(page, "#date-to-display", DROPOFF_DATE)

        # Set Drop-off Time
        await fill_time(page, "#time-to-display", DROPOFF_TIME)
        print("[INFO] Drop-off date/time set.")

        # Submit the search form
        await page.click("button.standard-form__submit[type='submit']")
        print("[INFO] Form submitted. Waiting for results...")

        # Wait for results and print them
        try:
            await page.wait_for_selector(".vehicle-card", timeout=20000)
            cars = await page.query_selector_all(".vehicle-card")
            print(f"\n[INFO] Found {len(cars)} cars:\n")
            for car in cars:
                try:
                    title = await car.query_selector_eval(".vehicle-title", "el => el.textContent.trim()")
                    price = await car.query_selector_eval(".price-total", "el => el.textContent.trim()")
                    print(f"🟢 {title} | {price}")
                except Exception:
                    continue
        except Exception:
            print("[WARN] No vehicles found or failed to load.")

        await browser.close()

asyncio.run(main())
