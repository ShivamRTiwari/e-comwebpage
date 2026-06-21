# ShopVerse — Python E-Commerce Website

A full-featured e-commerce web application built with **Flask** and **SQLite**.

## Features

- Product catalog with categories and search
- Product detail pages with related items
- Session-based shopping cart
- Guest checkout (no login required)
- User registration and login
- Order history for logged-in users
- Responsive, modern UI

## Project Structure

```
webpage/
├── app.py              # Flask application and routes
├── database.py         # SQLite schema and sample products
├── requirements.txt    # Python dependencies
├── shop.db             # SQLite database (created on first run)
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/          # Jinja2 HTML templates
```

## Quick Start

1. **Create a virtual environment (recommended):**

   ```bash
   cd /Users/shivam1.tiwari/Documents/MyScript/webpage
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**

   ```bash
   python app.py
   ```

4. **Open in browser:**

   ```
   http://localhost:5000
   ```

## Usage

| Page | URL |
|------|-----|
| Home | `/` |
| All products | `/products` |
| Filter by category | `/products?category=Electronics` |
| Search | `/products?q=headphones` |
| Cart | `/cart` |
| Checkout | `/checkout` |
| Register | `/register` |
| Login | `/login` |
| My orders | `/orders` (login required) |

## Configuration

Set a production secret key via environment variable:

```bash
export SECRET_KEY="your-secure-random-key"
python app.py
```

## Tech Stack

- **Backend:** Python 3, Flask 3
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Auth:** Werkzeug password hashing
