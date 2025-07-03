const express = require('express');
const scrapeCars = require('./scraper');

const app = express();
const PORT = 3000;

app.get('/cars', async (req, res) => {
  try {
    const cars = await scrapeCars();
    res.json(cars);
  } catch (err) {
    console.error(err);
    res.status(500).send('Scraping failed.');
  }
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});