CREATE TABLE IF NOT EXISTS shopping_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    color TEXT,
    icon TEXT
);
