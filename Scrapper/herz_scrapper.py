import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright
from timeout import Timeout

class hertzScrapper:
    def __init__(self, url: str, country: str, city: str, pickup_datetime: datetime,
                 dropoff_datetime: datetime, duration: int = 5, browser_type: str = "chromium",
                 different_drop_off: bool = False, max_restarts: int = 2):
        self.url = url
        self.country = country
        self.city = city
        self.pickup_datetime = pickup_datetime
        self.duration = duration
        self.dropoff_datetime = dropoff_datetime
        self.browser_type = browser_type
        self.different_drop_off = different_drop_off
        self.playwright = None
        
        # Timeout Handler
        self.timeout_handler = Timeout()

    async def start(self):
        # Create Page
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
        await self.timeout_handler.retry_step("Accept cookies", self.accept_cookies, page)

        # Network mode
        await self.timeout_handler.retry_step("Change to network mode", self.change_to_network_mode, page)

        # Country / City selection
        await self.timeout_handler.retry_step("Select country", self.select_country, page)
        await self.timeout_handler.retry_step("Select city", self.select_city, page)

        # Pickup / Dropoff locations
        await self.timeout_handler.retry_step("Select pickup/dropoff", self.select_pickup_and_dropoff_location, page)

        # Pick-up / Drop-off date & time
        await self.timeout_handler.retry_step("Select pickup datetime", self.select_pickup_datetime, page)
        await self.timeout_handler.retry_step("Select dropoff datetime", self.select_dropoff_datetime, page)
        
        # Search Results
        await self.timeout_handler.retry_step("Search for results", self.search_for_results, page)
        
        # Scrape Data and Print
        results = await self.timeout_handler.retry_step("Scrape results", self.scrape_results, page)
        for result in results:
            print(result)

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
        calendar_selector='.dropdown-menu.show',
        target_datetime=self.pickup_datetime,
        hour_selector='#hourdeparturedesktop',
        minute_selector='#minutesdeparturedesktop',
        widget_click=False,
        label="Pick-up"
    )

        # Wait for pickup calendar to close & drop-off to open
        await page.wait_for_selector('#hourreturndesktop', timeout=5000)
        print("Drop-off calendar is now active")

    async def select_dropoff_datetime(self, page):
        await self.select_date_time(
        page,
        dropdown_selector='#dropdownMenureturn',
        calendar_selector='.dropdown-menu.dropdown-menu-end.show',
        target_datetime=self.dropoff_datetime,
        hour_selector='#hourreturndesktop',
        minute_selector='#minutesreturndesktop',
        widget_click=True,
        label="Drop-off"
    )

    async def select_date_time(self, page, dropdown_selector, calendar_selector, target_datetime,
                               hour_selector, minute_selector, widget_click, label=""):
        # Open dropdown
        await page.wait_for_selector(dropdown_selector)
        await page.click(dropdown_selector)
        if widget_click:
            await page.click(dropdown_selector)
        print(f"{label}: Opened date/time dropdown")

        # Split date
        day = target_datetime.day
        month = target_datetime.month
        year = target_datetime.year
        
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        target_month_year = f"{month_names[int(month)-1]} {year}"

        # Scope calendar inside dropdown menu
        calendar_container = page.locator(calendar_selector)

        # Wait for calendar to render
        await calendar_container.locator('.vc-title').first.wait_for()

        while True:
            titles = [t.strip() for t in await calendar_container.locator('.vc-title').all_text_contents()]
            if target_month_year in titles:
                index = titles.index(target_month_year)
                panel = calendar_container.locator('.vc-pane').nth(index)
                day_locator = panel.locator(f'.vc-day:not(.is-disabled):has-text("{int(day)}")')
                await day_locator.first.click()
                print(f"{label}: Selected day {day} in {target_month_year}")
                break

            next_arrow = calendar_container.locator('.vc-arrow.vc-next')
            await next_arrow.first.click(force=True)
            await page.wait_for_timeout(25)

        hour = target_datetime.hour
        minute = target_datetime.minute

        # Time selection 
        await page.wait_for_selector(hour_selector)
        await page.select_option(hour_selector, value=str(int(hour)*100))
        print(f"{label}: Selected hour {hour}")

        await page.wait_for_selector(minute_selector)
        await page.select_option(minute_selector, value=str(int(minute)))
        print(f"{label}: Selected minute {minute}")

        # Confirm
        await page.wait_for_selector(f'{calendar_selector} button.btn.btn-primary.btn-full-width')
        await page.click(f'{calendar_selector} button.btn.btn-primary.btn-full-width')
        print(f"{label}: Confirmed date and time selection")
        
    async def search_for_results(self, page):
        # Click the search button
        await page.wait_for_selector('button.btn.btn-outline-primary.btn-full-width.submit-button')
        await page.click('button.btn.btn-outline-primary.btn-full-width.submit-button')
        print("Clicked 'Find your vehicle' button")
        
    async def scrape_results(self, page):
        # Wait for the visible fleet grid
        await page.wait_for_selector('.s-booking-fleet__grid:visible', timeout=20000)
        grid = page.locator('.s-booking-fleet__grid:visible').first

        # Cards only inside the visible grid, and only visible ones
        all_nodes_in_grid = grid.locator('.b-vehicle__body')
        visible_cards = grid.locator('.b-vehicle__body:visible')

        total_nodes = await all_nodes_in_grid.count()
        visible_count = await visible_cards.count()
        print(f"Car nodes in DOM (in grid): {total_nodes}, visible cards counted: {visible_count}")

        cars = []
        seen_titles = set()

        while True:
            # Wait for grid and visible car cards
            await page.wait_for_selector('.s-booking-fleet__grid')
            visible_cards = page.locator('.b-vehicle__body')
            visible_count = await visible_cards.count()

            for i in range(visible_count):
                card = visible_cards.nth(i)

                # Car name (strip "or similar")
                raw_title = await card.locator('.b-vehicle__title').text_content()
                title = (raw_title or '').replace('or similar', '').strip() or 'Unknown'

                # De-dup
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                # Category
                li_elements = await card.locator('.b-vehicle__groups li').all()
                category = 'Unknown'
                for li in li_elements:
                    attrs = await li.get_attribute("class")
                    data_toggle = await li.get_attribute("data-bs-toggle")

                    if data_toggle or (attrs and "separator" in attrs):
                        continue

                    text = (await li.text_content() or "").strip()
                    if text:
                        category = text
                        break
                    
                # Passengers
                passenger_locator = card.locator('.pair.bold i.icon-passenger')
                passengers = "Unknown"
                if await passenger_locator.count() > 0:
                    passengers_text = await passenger_locator.nth(0).locator("xpath=..").text_content()
                    if passengers_text:
                        passengers = passengers_text.strip().replace("\n", " ")
                        
                # Suitcases
                suitcase_locator = card.locator('.icon-suitcase')
                suitcases = "Unknown"
                if await suitcase_locator.count() > 0:
                    # get the sibling span next to <i class="icon-suitcase">
                    suitcase_text = await suitcase_locator.nth(0).evaluate("el => el.nextElementSibling?.textContent")
                    if suitcase_text:
                        match = re.search(r"\d+", suitcase_text)
                        suitcases = int(match.group()) if match else "Unknown"

                cars.append({
                    'name': title,
                    'category': category,
                    'passengers': passengers,
                    'suitcases': suitcases,
                })

            # Check if "Next" button is disabled
            next_button = page.locator('button.b-pagination__btn--next')
            if not await next_button.is_enabled():
                print("Reached last page of results.")
                break

            # Go to next page
            await next_button.click()
            await page.wait_for_timeout(2000)  # wait for results to reload

        print(f"Scraped {len(cars)} cars")
        return cars