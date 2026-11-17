# Anime Vault — Anime Watchlist Manager (Flask + MySQL)

A responsive anime watchlist web application built with HTML, CSS, JavaScript, Python Flask and MySQL.

## Features
- Dashboard statistics
- Add, edit and delete anime
- Poster image upload (PNG/JPG/JPEG/WEBP/GIF, max 5 MB) or remote image URL
- Watching, Completed, Plan to Watch, On Hold and Dropped statuses
- Episode progress controls
- Ratings, favorites and personal notes
- Search, status filtering and sorting
- Responsive dark interface and card animations
- Parameterized SQL queries and basic upload validation

## Requirements
- Python 3.10+
- MySQL 8+ or MariaDB
- pip

## 1. Create the database
Run `schema.sql` in MySQL Workbench, phpMyAdmin (SQL tab), or the MySQL command line.
It creates the `anime_watchlist` database and `anime` table.

## 2. Configure environment
Copy `.env.example` to `.env`, then set your MySQL username and password.
Example:
- DB_HOST=127.0.0.1
- DB_PORT=3306
- DB_USER=root
- DB_PASSWORD=your_mysql_password
- DB_NAME=anime_watchlist

Never upload `.env` to GitHub.

## 3. Install dependencies
```bash
python -m venv .venv
# Activate it, then:
pip install -r requirements.txt
```

## 4. Run the app
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Android / Termux note
This is a Python + MySQL web application, not an APK. XAMPP is generally used on a computer.
On Android, you need a running MySQL-compatible server (for example, MariaDB in Termux) and Python/Flask. A database file from SQLite cannot be used directly as a MySQL database; import/export or migration is needed.

## Security notes before public deployment
- Set a strong random SECRET_KEY.
- Use a dedicated MySQL user with permissions only for this database; avoid root.
- Turn off FLASK_DEBUG.
- Run behind a production WSGI server and HTTPS.
- Add authentication and per-user authorization before hosting for multiple people.
- Validate and limit uploads; consider image re-encoding and malware scanning for public uploads.
- Add CSRF protection before deploying on the public internet.
