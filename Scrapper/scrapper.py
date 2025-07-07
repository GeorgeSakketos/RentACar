import asyncio
from playwright.async_api import async_playwright

# ---- CONFIG ----
PICKUP_LOCATION = "Athens Airport"
PICKUP_DATE = "07/08/2025"    # Format DD/MM/YYYY
PICKUP_TIME = "13:30"         # Must match exactly one of the dropdown times
DROPOFF_DATE = "12/08/2025"
DROPOFF_TIME = "15:00"        # Must match exactly one of the dropdown times

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
    await page.wait_for_timeout(300)

    # Select only the visible timepicker list
    time_picker_lists = await page.query_selector_all(".ui-timepicker-list")

    for time_picker in time_picker_lists:
        visible = await time_picker.is_visible()
        if visible:
            options = await time_picker.query_selector_all("li")
            for option in options:
                text = (await option.inner_text()).strip()
                if text == time_str:
                    await option.scroll_into_view_if_needed()
                    await option.hover()
                    await option.click()
                    await page.wait_for_timeout(500)
                    print(f"[INFO] Selected time: {time_str}")
                    return
            raise Exception(f"[ERROR] Time option '{time_str}' not found in dropdown.")

    raise Exception("[ERROR] No visible timepicker list found.")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.avis.gr/")

        # Accept cookie banner
        try:
            await page.wait_for_selector("#consent_prompt_accept", timeout=7000)
            await page.click("#consent_prompt_accept")
            print("[INFO] Cookie accepted.")
        except Exception:
            print("[INFO] Cookie banner not found or already accepted.")

        # Close welcome popup
        try:
            await page.wait_for_selector("#welcome-close", timeout=7000)
            await page.click("#welcome-close")
            print("[INFO] 'Θέλω Κράτηση' popup closed.")
        except Exception:
            print("[INFO] 'Θέλω Κράτηση' popup not found or already closed.")

        # Set pickup location using autocomplete
        await page.click("#hire-search")
        await page.fill("#hire-search", "")
        await page.type("#hire-search", PICKUP_LOCATION, delay=100)

        try:
            await page.wait_for_selector("button.booking-widget__results__link", timeout=5000)
            await page.wait_for_timeout(1000)
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

        # Pickup date/time
        await select_date(page, "#date-from-display", PICKUP_DATE)
        await fill_time(page, "#time-from-display", PICKUP_TIME)
        print("[INFO] Pickup date/time set.")

        # Drop-off date/time
        await select_date(page, "#date-to-display", DROPOFF_DATE)
        await fill_time(page, "#time-to-display", DROPOFF_TIME)
        print("[INFO] Drop-off date/time set.")

        # Submit form using visible "ΒΡΕΙΤΕ ΑΥΤΟΚΙΝΗΤΟ" button
        try:
            buttons = await page.query_selector_all("div.standard-form__actions button[type='submit']")
            for btn in buttons:
                text = (await btn.inner_text()).strip()
                if "ΒΡΕΙΤΕ ΑΥΤΟΚΙΝΗΤΟ" in text:
                    visible = await btn.is_visible()
                    if visible:
                        await btn.scroll_into_view_if_needed()
                        await btn.hover()
                        await btn.click()
                        print("[INFO] Correct 'Find a Car' submit button clicked.")
                        break
            else:
                print("[ERROR] 'ΒΡΕΙΤΕ ΑΥΤΟΚΙΝΗΤΟ' button not found or not visible.")
        except Exception as e:
            print(f"[ERROR] Failed to click submit button: {e}")


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
                except Exception:
                    continue
        except Exception:
            print("[WARN] No vehicles found or failed to load.")

        await browser.close()

asyncio.run(main())
