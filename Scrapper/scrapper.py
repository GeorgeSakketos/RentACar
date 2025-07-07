import asyncio
from playwright.async_api import async_playwright

# ---- CONFIG ----
PICKUP_LOCATION = "Athens Airport"
PICKUP_DATE = "07/07/2025"
PICKUP_TIME = "13:30"
DROPOFF_DATE = "12/07/2025"
DROPOFF_TIME = "10:00"

async def select_date(page, date_selector, date_str):
    try:
        day, month, year = map(int, date_str.split("/"))
    except ValueError:
        raise ValueError("Date must be in 'DD/MM/YYYY' format")

    # Click to open calendar
    await page.click(date_selector)
    print(f"[INFO] Clicked {date_selector} to open calendar.")

    # Wait for the calendar to be visible — this avoids the issue with invisible elements
    await page.wait_for_selector(".pika-single:visible", timeout=5000)
    print("[INFO] Calendar is visible.")

    # Select year
    await page.select_option(".pika-single:visible .pika-select-year", str(year))
    await page.select_option(".pika-single:visible .pika-select-month", str(month - 1))

    # Wait for correct day button
    day_selector = (
        f'.pika-single:visible button.pika-button.pika-day[data-pika-year="{year}"]'
        f'[data-pika-month="{month - 1}"][data-pika-day="{day}"]'
    )
    await page.wait_for_selector(day_selector, timeout=5000)
    await page.click(day_selector)
    print(f"[INFO] Selected date {date_str}.")

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
            await page.click("#consent_prompt_accept", timeout=7000)
            print("[INFO] Cookie accepted.")
        except:
            print("[INFO] Cookie banner skipped.")

        try:
            await page.click("#welcome-close", timeout=7000)
            print("[INFO] Welcome popup closed.")
        except:
            print("[INFO] Welcome popup skipped.")

        # Pickup location autocomplete
        await page.click("#hire-search")
        await page.fill("#hire-search", "")
        await page.type("#hire-search", PICKUP_LOCATION, delay=100)

        try:
            await page.wait_for_selector("button.booking-widget__results__link", timeout=5000)
            await page.wait_for_timeout(1000)
            first_option = await page.query_selector("button.booking-widget__results__link")
            if first_option:
                await first_option.click()
                print("[INFO] Pickup location selected.")
            else:
                await page.keyboard.press("Enter")
        except:
            await page.keyboard.press("Enter")

        # Pickup date and time
        await select_date(page, "#date-from-display", PICKUP_DATE)
        await fill_time(page, "#time-from-display", PICKUP_TIME)
        print("[INFO] Pickup date/time set.")

        # Drop-off date and time
        await select_date(page, "#date-to-display", DROPOFF_DATE)
        await fill_time(page, "#time-to-display", DROPOFF_TIME)
        print("[INFO] Drop-off date/time set.")

        # Submit button
        try:
            await page.wait_for_selector("div.standard-form__actions > button.standard-form__submit", timeout=7000)
            await page.click("div.standard-form__actions > button.standard-form__submit")
            print("[INFO] Form submitted.")
        except Exception as e:
            print(f"[ERROR] Submit failed: {e}")

        # Wait for results
        try:
            await page.wait_for_selector(".vehicle-card", timeout=20000)
            cars = await page.query_selector_all(".vehicle-card")
            print(f"\n[INFO] Found {len(cars)} cars:\n")
            for car in cars:
                try:
                    title = await car.query_selector_eval(".vehicle-title", "el => el.textContent.trim()")
                    price = await car.query_selector_eval(".price-total", "el => el.textContent.trim()")
                    print(f"🟢 {title} | {price}")
                except:
                    continue
        except:
            print("[WARN] No cars found.")

        await browser.close()

asyncio.run(main())
