const puppeteer = require('puppeteer');

async function scrapeCars() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.goto('https://www.hertz.gr/en/', { waitUntil: 'networkidle2' });

  // TODO: interact with the site to reach the car list
  // You might need to:
  // - Select pickup/drop-off locations
  // - Set dates
  // - Submit search form

  // Example placeholder result
  const cars = [
    {
      name: 'Fiat Panda',
      price: '€29/day',
      image: 'https://via.placeholder.com/400x200?text=Fiat+Panda',
      details: 'Compact and fuel efficient',
    },
    {
      name: 'VW Golf',
      price: '€42/day',
      image: 'https://via.placeholder.com/400x200?text=VW+Golf',
      details: 'Perfect for long drives',
    }
  ];

  await browser.close();
  return cars;
}

module.exports = scrapeCars;