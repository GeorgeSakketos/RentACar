import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

PICKUP_LOCATION = "Athens Airport"
DROPOFF_LOCATION = "Athens Airport"

PICKUP_DATE = datetime.strptime("15-04-2026", '%d-%m-%Y')
DROPOFF_DATE = datetime.today() + timedelta(days=6)
PICKUP_TIME = "12:00"
DROPOFF_TIME = "10:00"

from datetime import datetime

GREEK_MONTHS = {
    "ΙΑΝΟΥΑΡΙΟΣ": "January", "ΦΕΒΡΟΥΑΡΙΟΣ": "February", "ΜΑΡΤΙΟΣ": "March",
    "ΑΠΡΙΛΙΟΣ": "April", "ΜΑΪΟΣ": "May", "ΙΟΥΝΙΟΣ": "June",
    "ΙΟΥΛΙΟΣ": "July", "ΑΥΓΟΥΣΤΟΣ": "August", "ΣΕΠΤΕΜΒΡΙΟΣ": "September",
    "ΟΚΤΩΒΡΙΟΣ": "October", "ΝΟΕΜΒΡΙΟΣ": "November", "ΔΕΚΕΜΒΡΙΟΣ": "December"
}

async def select_date(page, button_selector, target_date):
    # Remove overlay that blocks clicks
    await page.evaluate("""
        const overlay = document.querySelector('#map-flyout-container');
        if (overlay) overlay.remove();
    """)

    # Open calendar
    await page.click(button_selector, timeout=10000)
    await page.wait_for_selector("section.calendar-flyout-container .ui-datepicker-calendar", timeout=5000)

    for attempt in range(36):  # Try for 3 years
        await page.wait_for_timeout(500)  # Let calendar settle

        found = False

        # Check all 3 visible calendar groups
        for group_index in range(1, 4):
            try:
                month_sel = f".ui-datepicker-group:nth-child({group_index}) .ui-datepicker-month"
                year_sel = f".ui-datepicker-group:nth-child({group_index}) .ui-datepicker-year"

                displayed_month_el = await page.query_selector(month_sel)
                displayed_year_el = await page.query_selector(year_sel)

                if not (displayed_month_el and displayed_year_el):
                    continue

                greek_month = (await displayed_month_el.text_content()).strip().upper()
                year_text = (await displayed_year_el.text_content()).strip()

                english_month = GREEK_MONTHS.get(greek_month)
                if not english_month:
                    continue

                displayed_date = datetime.strptime(f"{english_month} {year_text}", "%B %Y")

                print(f"📅 Calendar {group_index} shows: {displayed_date.strftime('%B %Y')}")

                if displayed_date.year == target_date.year and displayed_date.month == target_date.month:
                    # Click the day in the correct panel
                    day_xpath = f"(//div[contains(@class,'ui-datepicker-group')][{group_index}]//a[text()='{target_date.day}'])[1]"
                    await page.wait_for_selector(day_xpath, timeout=5000)
                    await page.click(day_xpath)
                    found = True
                    break
            except Exception as e:
                print(f"⚠️ Error reading group {group_index}: {e}")
                continue

        if found:
            return
        else:
            await page.click(".ui-datepicker-next")

    raise Exception("❌ Desired month/year not found in calendar.")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.avis.gr/rent-a-car", timeout=60000)

        # Accept cookies
        try:
            await page.click("#consent_prompt_accept", timeout=10000)
            print("✅ Cookies accepted.")
        except:
            pass

        # Pickup location
        await page.fill("#hire-search", "")
        for c in PICKUP_LOCATION:
            await page.type("#hire-search", c, delay=150)
        await asyncio.sleep(2)
        await page.keyboard.press("Enter")
        print("✅ Pickup location.")

        # Dropoff location
        await page.fill("#return-search", "")
        for c in DROPOFF_LOCATION:
            await page.type("#return-search", c, delay=150)
        await asyncio.sleep(2)
        await page.keyboard.press("Enter")
        print("✅ Dropoff location.")

        # Pickup date
        await select_date(page, "#pick-up-date-button", PICKUP_DATE)
        print(f"✅ Pickup date: {PICKUP_DATE.strftime('%d/%m/%Y')}")

        # Pickup time
        await page.select_option("select[name='pickuptime']", PICKUP_TIME)
        print("✅ Pickup time.")

        # Dropoff date
        await select_date(page, "#return-date-button", DROPOFF_DATE)
        print(f"✅ Dropoff date: {DROPOFF_DATE.strftime('%d/%m/%Y')}")

        # Dropoff time
        await page.select_option("select[name='dropofftime']", DROPOFF_TIME)
        print("✅ Dropoff time.")

        # Debug
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())