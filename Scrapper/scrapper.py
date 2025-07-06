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

        # Accept cookies if banner appears
        try:
            await page.wait_for_selector("#consent_prompt_accept", timeout=7000)
            await page.click("#consent_prompt_accept")
            print("[INFO] Cookie accepted.")
        except Exception:
            print("[INFO] Cookie banner not found or already accepted.")

        # Close welcome popup if present
        try:
            await page.wait_for_selector("#welcome-close", timeout=7000)
            await page.click("#welcome-close")
            print("[INFO] 'Θέλω Κράτηση' popup closed.")
        except Exception:
            print("[INFO] 'Θέλω Κράτηση' popup not found or already closed.")

        # Fill pickup location with slow typing to trigger autocomplete
        await page.click("#hire-search")
        await page.fill("#hire-search", "")
        await page.type("#hire-search", PICKUP_LOCATION, delay=100)

        # Wait for autocomplete options and pause 1 second before clicking first option
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

        # Set pickup date and time
        await select_date(page, "#date-from-display", PICKUP_DATE)
        await fill_time(page, "#time-from-display", PICKUP_TIME)
        print("[INFO] Pickup date/time set.")

        # Submit form with refined selector and multiple fallback click methods
        try:
            submit_selector = 'button.standard-form__submit:has-text("ΒΡΕΙΤΕ ΑΥΤΟΚΙΝΗΤΟ")'
            await page.wait_for_selector(submit_selector, state="visible", timeout=7000)
            button = await page.query_selector(submit_selector)

            if not button:
                print("[ERROR] Submit button with expected text not found.")
            else:
                is_disabled = await button.get_attribute("disabled")
                if is_disabled:
                    print("[WARN] Submit button is disabled, cannot click.")
                else:
                    await button.scroll_into_view_if_needed()
                    try:
                        await page.dispatch_event(submit_selector, "click")
                        print("[INFO] Form submitted with dispatch_event click.")
                    except Exception as e:
                        print(f"[WARN] dispatch_event click failed: {e}")
                        try:
                            await page.eval_on_selector(submit_selector, "button => button.click()")
                            print("[INFO] Form submitted with JS click.")
                        except Exception as e2:
                            print(f"[WARN] JS click failed: {e2}")
                            try:
                                await button.focus()
                                await page.keyboard.press("Enter")
                                print("[INFO] Form submitted with Enter key.")
                            except Exception as e3:
                                print(f"[ERROR] Keyboard Enter failed: {e3}")
                                print("[ERROR] Failed to submit the form by any method.")
        except Exception as e:
            print(f"[ERROR] Submit button not found or other error: {e}")

        # Wait for search results
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
