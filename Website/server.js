const express = require("express");
const sqlite3 = require("sqlite3").verbose();
const path = require("path");

const app = express();
const PORT = 3000;

// Serve static files
app.use(express.static("public"));

// Database setup
const db = new sqlite3.Database("cars.db");

db.serialize(() => {
  db.run(
    `CREATE TABLE IF NOT EXISTS cars (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      brand TEXT NOT NULL,
      model TEXT NOT NULL,
      price_per_day REAL NOT NULL
    )`
  );

  db.get("SELECT COUNT(*) as count FROM cars", (err, row) => {
    if (row.count === 0) {
      const stmt = db.prepare(
        "INSERT INTO cars (brand, model, price_per_day) VALUES (?, ?, ?)"
      );
      stmt.run("Toyota", "Corolla", 40);
      stmt.run("Honda", "Civic", 50);
      stmt.run("Ford", "Focus", 45);
      stmt.run("Tesla", "Model 3", 100);
      stmt.finalize();
    }
  });
});

// API route to get cars
app.get("/cars", (req, res) => {
  db.all("SELECT * FROM cars", (err, rows) => {
    if (err) return res.status(500).send("Database error");
    res.json(rows);
  });
});

// Serve HTML page
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index2.html"));
});

// Start server
app.listen(PORT, () => {
  console.log(`🚗 Car rental app running at http://localhost:${PORT}`);
});