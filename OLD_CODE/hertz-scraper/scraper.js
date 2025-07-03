const puppeteer = require('puppeteer');

async function scrapeCars() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.goto('https://www.hertz.gr/en/car-rental/', { waitUntil: 'networkidle2' });

  // Wait for car listing container to appear
  await page.waitForSelector('.car-info-wrapper', { timeout: 30000 });

  // Extract car data
  const cars = await page.evaluate(() => {
    const carCards = document.querySelectorAll('.b-vehicle__header');
    return Array.from(carCards).map(card => {
      const name = card.querySelector('.b-vehicle__title')?.innerText || '';
      // const price = card.querySelector('.car-price')?.innerText || '';
      // const image = card.querySelector('img')?.src || '';
      // const link = card.querySelector('a')?.href || '';
      // return { name, price, image, link };
      return { name };
    });
  });

  await browser.close();
  return cars;
}

module.exports = scrapeCars;
