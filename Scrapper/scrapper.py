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

    await page.click(date_selector)
    print(f"[INFO] Clicked {date_selector} to open calendar.")

    await page.wait_for_selector(".pika-single:visible", timeout=5000)
    print("[INFO] Calendar is visible.")

    await page.select_option(".pika-single:visible .pika-select-year", str(year))
    await page.select_option(".pika-single:visible .pika-select-month", str(month - 1))

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

async def scrape_vehicle_data(page):
    print("[INFO] Waiting for vehicle listings to load...")
    await page.wait_for_selector(".vehicle__inner", timeout=20000)

    vehicle_cards = await page.query_selector_all(".vehicle__inner")
    print(f"[INFO] Found {len(vehicle_cards)} vehicle cards.")

    results = []
    for card in vehicle_cards:
        # Vehicle name inside vehicle__specs > vehicle__header > vehicle__header__inner
        name_el = await card.query_selector(".vehicle__specs .vehicle__header .vehicle__header__inner")
        name = (await name_el.inner_text()).strip() if name_el else "N/A"

        # Vehicle image
        img_el = await card.query_selector("img")
        img_url = await img_el.get_attribute("data-small") if img_el else "N/A"

        # Price pay on collection
        pay_collection_el = await card.query_selector(
            'div.vehicle__prices-option[data-payment-type="pay_collection"] p.vehicle__prices-price'
        )
        pay_collection_price = (await pay_collection_el.inner_text()).strip() if pay_collection_el else "N/A"

        # Price pay online
        pay_online_el = await card.query_selector(
            'div.vehicle__prices-option.vehicle__prices-option--primary[data-payment-type="pay_online"] p.vehicle__prices-price'
        )
        pay_online_price = (await pay_online_el.inner_text()).strip() if pay_online_el else "N/A"

        # Vehicle details
        details_els = await card.query_selector_all("ul.vehicle__footer__features li.vehicle__footer__features__item")
        details = [await (await li.get_property("textContent")).json_value() for li in details_els]

        results.append({
            "name": name,
            "image_url": img_url,
            "price_pay_collection": pay_collection_price,
            "price_pay_online": pay_online_price,
            "details": details,
        })

    for idx, vehicle in enumerate(results, 1):
        print(f"\n[VEHICLE {idx}]")
        print(f"Name: {vehicle['name']}")
        print(f"Image URL: {vehicle['image_url']}")
        print(f"Price (Pay on collection): {vehicle['price_pay_collection']}")
        print(f"Price (Pay online): {vehicle['price_pay_online']}")
        print(f"Details: {vehicle['details']}")

    return results

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
                        # Clicking submit triggers navigation, so wait for navigation
                        async with page.expect_navigation():
                            await btn.click()
                        print("[INFO] Correct 'Find a Car' submit button clicked and navigation happened.")
                        break
            else:
                print("[ERROR] 'ΒΡΕΙΤΕ ΑΥΤΟΚΙΝΗΤΟ' button not found or not visible.")
                await browser.close()
                return
        except Exception as e:
            print(f"[ERROR] Failed to click submit button: {e}")
            await browser.close()
            return

        # Scrape vehicle data on results page
        await scrape_vehicle_data(page)

        await browser.close()

asyncio.run(main())