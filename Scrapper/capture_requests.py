import asyncio
from playwright.async_api import async_playwright

async def main():
    requests_made = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        def log_request(request):
            print(f"Captured request: {request.method} {request.url}")
            requests_made.append({
                "url": request.url,
                "method": request.method,
                "post_data": request.post_data,
                "headers": request.headers
            })

        page.on("request", log_request)

        print("Opening https://www.hertz.gr/el/car-rental/")
        await page.goto("https://www.hertz.gr/el/car-rental/")

        print("You can now manually interact with the browser.")
        print("Press Ctrl+C in this terminal to stop and see all captured requests.")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nCtrl+C received, closing browser...")

        await browser.close()

    print("\n--- All network requests made ---")
    for req in requests_made:
        print(f"\nURL: {req['url']}")
        print(f"Method: {req['method']}")
        if req['post_data']:
            print(f"Post Data: {req['post_data']}")
        else:
            print("Post Data: None")

if __name__ == "__main__":
    asyncio.run(main())
