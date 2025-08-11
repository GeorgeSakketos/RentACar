import asyncio
from playwright.async_api import async_playwright

class hertzScrapper:
    def __init__(self, url: str, country: str, city: str, duration: int = 10, browser_type: str = "chromium"):
        self.url = url
        self.country = country
        self.city = city
        self.duration = duration
        self.browser_type = browser_type
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

        # Click the 'Network' button
        await page.wait_for_selector('button.btn-network--departure')
        await page.click('button.btn-network--departure')
        print("Clicked the 'Δίκτυο' button")

        # Fill the country input
        await page.wait_for_selector('#departurecountry')
        await page.fill('#departurecountry', self.country)
        print(f"Filled country input with: {self.country}")

        # Select first country dropdown option
        country_dropdown_selector = '#departurecountry-multiselect-options li:first-child'
        await page.wait_for_selector(country_dropdown_selector)
        await page.click(country_dropdown_selector)
        print("Selected the first country option from the dropdown")
        
        # Fill the city input
        await page.wait_for_selector('#departurecity')
        await page.fill('#departurecity', self.city)
        print(f"Filled city input with: {self.city}")

        # Select first city dropdown option
        city_dropdown_selector = '#departurecity-multiselect-options li:first-child'
        await page.wait_for_selector(city_dropdown_selector)
        await page.click(city_dropdown_selector)
        print("Selected the first city option from the dropdown")

        # Click once on the departure location input to show options
        await page.wait_for_selector('#departurelocation')
        await page.click('#departurelocation')
        print("Clicked departure location input, waiting for options to appear...")

        # Wait for options to appear
        await page.wait_for_selector('#departurelocation-multiselect-options li')

        # Get all options text
        option_elements = await page.query_selector_all('#departurelocation-multiselect-options li')
        options = [ (await opt.text_content()).strip() for opt in option_elements ]

        print("Please choose one of the following departure locations:")
        for i, opt in enumerate(options, 1):
            print(f"{i}: {opt}")

        while True:
            choice = input(f"Enter the number (1-{len(options)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                choice_index = int(choice) - 1
                break
            print("Invalid choice, try again.")

        chosen_option = options[choice_index]
        print(f"You chose: {chosen_option}")

        # Fill input with chosen option text
        await page.fill('#departurelocation', chosen_option)

        # Wait and click the matching option to confirm selection
        await page.wait_for_selector('#departurelocation-multiselect-options li')
        dropdown_options = await page.query_selector_all('#departurelocation-multiselect-options li')

        for opt in dropdown_options:
            text = (await opt.text_content()).strip()
            if text == chosen_option:
                await opt.click()
                print(f"Selected departure location: {chosen_option}")
                break

        await asyncio.sleep(self.duration)
        await browser.close()
        print(f"Closed {self.url}")
        await self.playwright.stop()