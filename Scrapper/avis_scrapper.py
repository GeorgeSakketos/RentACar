import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

PICKUP_LOCATION = "Athens Airport"
DROPOFF_LOCATION = "Athens Airport"

PICKUP_DATE = datetime.strptime("15-04-2026", '%d-%m-%Y')
DROPOFF_DATE = datetime.strptime("20-04-2026", '%d-%m-%Y')
PICKUP_TIME = "12:00"
DROPOFF_TIME = "10:00"

GREEK_MONTHS = {
    "ΙΑΝΟΥΑΡΙΟΣ": "January", "ΦΕΒΡΟΥΑΡΙΟΣ": "February", "ΜΑΡΤΙΟΣ": "March",
    "ΑΠΡΙΛΙΟΣ": "April", "ΜΑΪΟΣ": "May", "ΙΟΥΝΙΟΣ": "June",
    "ΙΟΥΛΙΟΣ": "July", "ΑΥΓΟΥΣΤΟΣ": "August", "ΣΕΠΤΕΜΒΡΙΟΣ": "September",
    "ΟΚΤΩΒΡΙΟΣ": "October", "ΝΟΕΜΒΡΙΟΣ": "November", "ΔΕΚΕΜΒΡΙΟΣ": "December"
}

async def select_date(page, button_selector, target_date):
    # Remove overlay if present (adjust selector to your case)
    await page.evaluate("""
        const overlay = document.querySelector('#map-flyout-container');
        if (overlay) overlay.remove();
    """)

    # Open the calendar widget
    await page.click(button_selector, timeout=10000)

    # Wait until at least one calendar is visible
    calendar_tables = await page.query_selector_all("section.calendar-flyout-container .ui-datepicker-calendar")
    for _ in range(20):  # retry up to ~5 seconds
        visible_found = False
        for cal in calendar_tables:
            if await cal.is_visible():
                visible_found = True
                break
        if visible_found:
            break
        await page.wait_for_timeout(250)
    else:
        raise Exception("No visible calendar found after opening date picker.")

    # Now loop through calendar months to find and click the target date
    for attempt in range(36):  # try up to 3 years ahead/back
        await page.wait_for_timeout(500)  # wait for calendar animation/settle

        month_elements = await page.query_selector_all(".calendar-flyout-container .ui-datepicker-month")
        year_elements = await page.query_selector_all(".calendar-flyout-container .ui-datepicker-year")

        months_years = []
        for m_el, y_el in zip(month_elements, year_elements):
            month_text = (await m_el.text_content()).strip().upper()
            year_text = (await y_el.text_content()).strip()
            english_month = GREEK_MONTHS.get(month_text)
            if not english_month:
                raise Exception(f"Unknown Greek month: {month_text}")
            dt = datetime.strptime(f"{english_month} {year_text}", "%B %Y")
            months_years.append(dt)

        print("Reach Point 1")

        matched_index = None
        for i, dt in enumerate(months_years):
            if dt.year == target_date.year and dt.month == target_date.month:
                matched_index = i
                break

        if matched_index is not None:
            day_xpath = (
                f"(//section[contains(@class,'calendar-flyout-container')]"
                f"//table[contains(@class,'ui-datepicker-calendar')])[{matched_index + 1}]"
                f"//a[text()='{target_date.day}']"
            )
            await page.wait_for_selector(day_xpath, timeout=5000)
            await page.click(day_xpath)
            return  # Date selected successfully!

        print("Reach Point 2")

        # Navigate calendar forward or backward as needed
        if months_years[-1] < target_date:
            await page.click(".ui-datepicker-next")
        elif months_years[0] > target_date:
            await page.click(".ui-datepicker-prev")
        else:
            raise Exception("Target month/year is between displayed months but day not found.")

    raise Exception("Desired month/year not found in calendar.")

async def select_time(page, button_selector, hour_id, minute_id, confirm_button_selector, target_time):
    await page.click(button_selector)
    await page.wait_for_selector(hour_id, timeout=5000)

    hour, minute = target_time.split(":")
    await page.select_option(hour_id, hour.zfill(2))
    await page.select_option(minute_id, minute.zfill(2))

    await page.click(confirm_button_selector)
    await page.wait_for_timeout(500)

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
            await page.type("#hire-search", c, delay=100)
        await asyncio.sleep(1.5)
        await page.keyboard.press("Enter")
        print("✅ Pickup location.")

        # Dropoff location
        await page.fill("#return-search", "")
        for c in DROPOFF_LOCATION:
            await page.type("#return-search", c, delay=100)
        await asyncio.sleep(1.5)
        await page.keyboard.press("Enter")
        print("✅ Dropoff location.")

        # Pickup date
        await select_date(page, "#pick-up-date-button", PICKUP_DATE)
        print(f"✅ Pickup date: {PICKUP_DATE.strftime('%d/%m/%Y')}")

        # Pickup time
        await select_time(
            page,
            "#pick-up-time-button",
            "#time-from-hours",
            "#time-from-minutes",
            "#select-pickUpTime",
            PICKUP_TIME
        )
        print("✅ Pickup time selected.")

        # Dropoff date
        await select_date(page, "#drop-off-date-button", DROPOFF_DATE)
        print(f"✅ Dropoff date: {DROPOFF_DATE.strftime('%d/%m/%Y')}")

        # Dropoff time
        await select_time(
            page,
            "#return-time-button",
            "#time-to-hours",
            "#time-to-minutes",
            "#select-returnTime",
            DROPOFF_TIME
        )
        print("✅ Dropoff time selected.")

        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())