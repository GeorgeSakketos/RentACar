import asyncio
from datetime import datetime, timedelta
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
    # Remove overlay if present
    await page.evaluate("""
        const overlay = document.querySelector('#map-flyout-container');
        if (overlay) overlay.remove();
    """)

    # Open the calendar widget
    await page.click(button_selector, timeout=10000)
    await page.wait_for_selector("section.calendar-flyout-container .ui-datepicker-calendar", timeout=5000)

    for attempt in range(36):  # Try up to 3 years forward/back
        await page.wait_for_timeout(500)  # Let calendar settle

        # Get all 3 month-year headers in the calendar widget
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

        # Check if any displayed month/year matches the target
        matched_index = None
        for i, dt in enumerate(months_years):
            if dt.year == target_date.year and dt.month == target_date.month:
                matched_index = i
                break

        if matched_index is not None:
            # Click the day within the matched calendar
            # The calendars are in order, so find the nth calendar and click the day there
            day_xpath = f"(//section[contains(@class,'calendar-flyout-container')]//table[contains(@class,'ui-datepicker-calendar')])[{matched_index + 1}]//a[text()='{target_date.day}']"
            await page.wait_for_selector(day_xpath, timeout=5000)
            await page.click(day_xpath)
            return  # Done!

        # If target date is after the last displayed month, go next
        if months_years[-1] < target_date:
            await page.click(".ui-datepicker-next")
        # If target date is before the first displayed month, go prev
        elif months_years[0] > target_date:
            await page.click(".ui-datepicker-prev")
        else:
            # Target date is between displayed months but not found? Possible error
            raise Exception("Target month/year is between displayed months but day not found.")

    raise Exception("Desired month/year not found in calendar.")

async def select_time(page, button_selector, hour_id, minute_id, confirm_button_selector, target_time):
    # Click to open the time picker
    await page.click(button_selector)
    await page.wait_for_selector(hour_id, timeout=5000)

    # Parse time string
    hour, minute = target_time.split(":")
    hour = hour.zfill(2)
    minute = minute.zfill(2)

    # Select hour and minute
    await page.select_option(hour_id, hour)
    await page.select_option(minute_id, minute)

    # Click "Select time" button to confirm
    await page.click(confirm_button_selector)

    # Wait a little to ensure UI updates
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
        await select_time(
            page,
            "#pick-up-time-button",           # button to open the picker
            "#time-from-hours",               # select element for hours
            "#time-from-minutes",             # select element for minutes
            "#select-pickUpTime",             # confirmation button
            PICKUP_TIME                       # time string e.g., "10:00"
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

        # Debug
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())