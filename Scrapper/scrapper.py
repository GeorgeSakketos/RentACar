import asyncio
from playwright.async_api import async_playwright

# ---- CONFIG ----
PICKUP_LOCATION = "Athens Airport"
PICKUP_DATE = "07/07/2025"    # Format DD/MM/YYYY
PICKUP_TIME = "13:30"          # Must match exactly one of the dropdown times
DROPOFF_DATE = "12/07/2025"
DROPOFF_TIME = "10:00"

async def select_date(page, date_selector, date_str):
    try:
        day, month, year = map(int, date_str.split("/"))
    except ValueError:
        raise ValueError("Date must be in 'DD/MM/YYYY' format")

    # Open the date picker
    await page.click(date_selector)

    # Wait for year selector to appear
    await page.wait_for_selector(".pika-select-year")

    # Select year
    await page.select_option(".pika-select-year", str(year))

    # Select month (0-based index)
    await page.select_option(".pika-select-month", str(month - 1))

    # Wait for day buttons to appear
    day_selector = (
        f'button.pika-button.pika-day[data-pika-year="{year}"]'
        f'[data-pika-month="{month - 1}"][data-pika-day="{day}"]'
    )
    await page.wait_for_selector(day_selector)

    # Click the day button
    await page.click(day_selector)

async def fill_time(page, time_selector, time_str):
    await page.wait_for_selector(time_selector, state="visible", timeout=7000)
    await page.click(time_selector)
    await page.wait_for_timeout(500)
    option_selector = f'.ui-timepicker-list li:text("{time_str}")'
    await page.wait_for_selector(option_selector, timeout=5000)
    await page.click(option_selector)
    await page.wait_for_timeout(500)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.avis.gr/")

        try:
            await page.wait_for_selector("#consent_prompt_accept", timeout=7000)
            await page.click("#consent_prompt_accept")
            print("[INFO] Cookie accepted.")
        except Exception:
            print("[INFO] Cookie banner not found or already accepted.")

        try:
            await page.wait_for_selector("#welcome-close", timeout=7000)
            await page.click("#welcome-close")
            print("[INFO] 'Θέλω Κράτηση' popup closed.")
        except Exception:
            print("[INFO] 'Θέλω Κράτηση' popup not found or already closed.")

        # Clear and type pickup location slowly to trigger autocomplete dropdown
        await page.click("#hire-search")
        await page.fill("#hire-search", "")
        await page.type("#hire-search", PICKUP_LOCATION, delay=100)

        # Wait for autocomplete options and pause 1 second before clicking first option
        try:
            await page.wait_for_selector("button.booking-widget__results__link", timeout=5000)
            await page.wait_for_timeout(1000)  # <-- Added 1 second wait here
            first_option = await page.query_selector("button.booking-widget__results__link")
            if first_option:
                await first_option.click()
                print("[INFO] Pickup location set by selecting first autocomplete suggestion.")
            else:
                print("[WARN] No autocomplete options found, pressing Enter as fallback.")
                await page.keyboard.press("Enter")
        except Exception:
            print("[WARN] Autocomplete options did not appear, pressing Enter as fallback.")
            await page.keyboard.press("Enter")

        # Set pickup date and time
        await select_date(page, "#date-from-display", PICKUP_DATE)
        await fill_time(page, "#time-from-display", PICKUP_TIME)
        print("[INFO] Pickup date/time set.")

        # Submit form
        await page.click("button.standard-form__submit[type='submit']")
        print("[INFO] Form submitted. Waiting for results...")

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
