import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class hertzScrapper:
    def __init__(self, url: str, country: str, city: str, pickup_date: str, pickup_time: str, dropoff_date: str, dropoff_time: str, duration: int = 10, 
                 browser_type: str = "chromium", different_drop_off: bool = False):
        self.url = url
        self.country = country
        self.city = city
        self.pickup_date = pickup_date  # dd/mm/yyyy
        self.pickup_time = pickup_time  # HH:MM in 15-min increments
        self.duration = duration    # duration before timing out
        self.dropoff_date = dropoff_date    # dd/mm/yyyy
        self.dropoff_time = dropoff_time    # HH:MM in 15-min increments
        self.browser_type = browser_type
        self.different_drop_off = different_drop_off
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()

        if self.browser_type == "chromium":
            browser_launcher = self.playwright.chromium
        elif self.browser_type == "firefox":
            browser_launcher = self.playwright.firefox
        elif self.browser_type == "webkit":
            browser_launcher = self.playwright.webkit
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")

        print(f"Launching browser: {self.browser_type}")
        browser = await browser_launcher.launch(headless=False)
        page = await browser.new_page()
        await page.goto(self.url, wait_until="domcontentloaded")
        print(f"Opened {self.url}")

        # Accept cookies first
        await self.accept_cookies(page)

        # Network mode
        await self.change_to_network_mode(page)

        # Country / City selection
        await self.select_country(page)
        await self.select_city(page)

        # Pickup / Dropoff locations
        await self.select_pickup_and_dropoff_location(page)

        # Pick-up / Drop-off date & time
        await self.select_pickup_datetime(page)
        await self.select_dropoff_datetime(page)

        await asyncio.sleep(self.duration)
        await browser.close()
        print(f"Closed {self.url}")
        await self.playwright.stop()
        
    async def accept_cookies(self, page):
        # Check for cookies banner and accept it if present.
        try:
            # Wait briefly for the cookie banner to appear
            await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=3000)
            await page.click('#onetrust-accept-btn-handler')
            print("Accepted cookies banner")
        except:
            print("No cookies banner found, skipping...")
    
    async def change_to_network_mode(self, page):
        await page.wait_for_selector('button.btn-network--departure')
        await page.click('button.btn-network--departure')
        print("Clicked the 'Δίκτυο' button")
        
    async def select_country(self, page):
        # Fill the country input
        await page.wait_for_selector('#departurecountry')
        await page.fill('#departurecountry', self.country)
        print(f"Filled country input with: {self.country}")

        # Select country from dropdown option
        country_dropdown_selector = '#departurecountry-multiselect-options li:first-child'
        await page.wait_for_selector(country_dropdown_selector)
        await page.click(country_dropdown_selector)
        print("Selected the first country option from the dropdown")
        
    async def select_city(self, page):
        # Fill city
        await page.wait_for_selector('#departurecity')
        await page.click('#departurecity')
        await page.fill('#departurecity', self.city)
        await page.wait_for_selector('#departurecity-multiselect-options li')
        city_options = await page.query_selector_all('#departurecity-multiselect-options li')
        if city_options:
            await city_options[0].click()
            print(f"Selected city: {self.city}")
        else:
            print("No city options found!")
            
    async def select_pickup_and_dropoff_location(self, page):
        # Departure location: click to show options, ask user to pick
        await page.wait_for_selector('#departurelocation')
        await page.click('#departurelocation')
        print("Clicked departure location input, waiting for options...")

        await page.wait_for_selector('#departurelocation-multiselect-options li')
        dep_loc_elements = await page.query_selector_all('#departurelocation-multiselect-options li')
        dep_locations = [ (await el.text_content()).strip() for el in dep_loc_elements ]

        if not dep_locations:
            print("No departure location options found!")
        else:
            print("Please choose a departure location:")
            for i, opt in enumerate(dep_locations, 1):
                print(f"{i}: {opt}")

            while True:
                choice = input(f"Enter number (1-{len(dep_locations)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(dep_locations):
                    chosen_idx = int(choice) - 1
                    break
                print("Invalid choice, try again.")

            chosen_dep_location = dep_locations[chosen_idx]
            print(f"You chose departure location: {chosen_dep_location}")

            await page.fill('#departurelocation', chosen_dep_location)
            # Confirm by clicking matching dropdown item
            await page.wait_for_selector('#departurelocation-multiselect-options li')
            dep_loc_elements = await page.query_selector_all('#departurelocation-multiselect-options li')
            for el in dep_loc_elements:
                text = (await el.text_content()).strip()
                if text == chosen_dep_location:
                    await el.click()
                    print(f"Selected departure location: {chosen_dep_location}")
                    break

        # Handle different drop off location
        if self.different_drop_off:
            await page.wait_for_selector('#differentReturn')
            await page.check('#differentReturn')
            print("Enabled different drop off location")

            await page.wait_for_selector('#searchLocationReturn')
            await page.click('#searchLocationReturn')
            print("Clicked drop-off location input, waiting for options...")

            await page.wait_for_selector('#searchLocationReturn-multiselect-options li')
            dropoff_elements = await page.query_selector_all('#searchLocationReturn-multiselect-options li')
            dropoff_options = [ (await el.text_content()).strip() for el in dropoff_elements ]

            if not dropoff_options:
                print("No drop-off location options found!")
            else:
                print("Please choose a drop-off location:")
                for i, opt in enumerate(dropoff_options, 1):
                    print(f"{i}: {opt}")

                while True:
                    choice = input(f"Enter number (1-{len(dropoff_options)}): ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(dropoff_options):
                        chosen_idx = int(choice) - 1
                        break
                    print("Invalid choice, try again.")

                chosen_dropoff = dropoff_options[chosen_idx]
                print(f"You chose drop-off location: {chosen_dropoff}")

                await page.fill('#searchLocationReturn', chosen_dropoff)

                await page.wait_for_selector('#searchLocationReturn-multiselect-options li')
                dropoff_elements = await page.query_selector_all('#searchLocationReturn-multiselect-options li')
                for el in dropoff_elements:
                    text = (await el.text_content()).strip()
                    if text == chosen_dropoff:
                        await el.click()
                        print(f"Selected drop-off location: {chosen_dropoff}")
                        break

    async def select_pickup_datetime(self, page):
        await self.select_date_time(
            page,
            dropdown_selector='#dropdownMenudeparture',
            target_date=self.pickup_date,
            target_time=self.pickup_time,
            hour_selector='#hourdeparturedesktop',
            minute_selector='#minutesdeparturedesktop',
            widget_click=True,
            label="Pick-up"
        )

    async def select_dropoff_datetime(self, page):
        await self.select_date_time(
            page,
            dropdown_selector='#dropdownMenureturn',
            target_date=self.dropoff_date,
            target_time=self.dropoff_time,
            hour_selector='#hourreturndesktop',
            minute_selector='#minutesreturndesktop',
            widget_click=False,
            label="Drop-off"
        )

    async def select_date_time(self, page, dropdown_selector, target_date, target_time,
                               hour_selector, minute_selector, widget_click, label=""):
        # Open dropdown
        await page.wait_for_selector(dropdown_selector)
        if (widget_click):
            await page.click(dropdown_selector)
        print(f"{label}: Opened date/time dropdown")

        # Split date
        day, month, year = target_date.split('/')
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        target_month_year = f"{month_names[int(month)-1]} {year}"

        # Wait for calendar to render
        await page.wait_for_selector('.vc-title')

        while True:
            titles = [t.strip() for t in await page.locator('.vc-title').all_text_contents()]
            if target_month_year in titles:
                index = titles.index(target_month_year)
                panel = page.locator('.vc-pane').nth(index)
                day_locator = panel.locator(f'.vc-day:not(.is-disabled):has-text("{int(day)}")')
                await day_locator.first.click()
                print(f"{label}: Selected day {day} in {target_month_year}")
                break

            await page.click('.vc-arrow.vc-next', force=True)
            await page.wait_for_timeout(25)

        # Time selection
        hour, minute = target_time.split(':')
        await page.wait_for_selector(hour_selector)
        await page.select_option(hour_selector, value=str(int(hour)*100))
        print(f"{label}: Selected hour {hour}")

        await page.wait_for_selector(minute_selector)
        await page.select_option(minute_selector, value=str(int(minute)))
        print(f"{label}: Selected minute {minute}")

        # Confirm
        await page.wait_for_selector('button.btn.btn-primary.btn-full-width')
        await page.click('button.btn.btn-primary.btn-full-width')
        print(f"{label}: Confirmed date and time selection")