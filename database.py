import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shop.db"

SAMPLE_PRODUCTS = [
    ("Wireless Headphones", "Premium noise-cancelling headphones with 30-hour battery life.", 149.99, "Electronics", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=600&fit=crop"),
    ("Smart Watch", "Track fitness, notifications, and health metrics on your wrist.", 249.99, "Electronics", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&h=600&fit=crop"),
    ("Leather Backpack", "Durable full-grain leather backpack for daily commute.", 89.99, "Accessories", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&h=600&fit=crop"),
    ("Running Shoes", "Lightweight breathable shoes built for long-distance runs.", 119.99, "Footwear", "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=600&fit=crop"),
    ("Coffee Maker", "Programmable drip coffee maker with thermal carafe.", 79.99, "Home", "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=600&fit=crop"),
    ("Desk Lamp", "Adjustable LED desk lamp with warm and cool light modes.", 45.99, "Home", "https://images.unsplash.com/photo-1507473888945-ef528f7b2f3f?w=600&h=600&fit=crop"),
    ("Sunglasses", "Polarized UV400 protection with classic aviator frame.", 59.99, "Accessories", "https://images.unsplash.com/photo-1572635196234-4f48d0f5d1c8?w=600&h=600&fit=crop"),
    ("Yoga Mat", "Non-slip eco-friendly mat for yoga and pilates.", 34.99, "Fitness", "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=600&h=600&fit=crop"),
    ("Bluetooth Speaker", "Portable waterproof speaker with rich 360° sound.", 69.99, "Electronics", "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&h=600&fit=crop"),
    ("Ceramic Mug Set", "Set of 4 handcrafted ceramic mugs in matte finish.", 29.99, "Home", "https://images.unsplash.com/photo-1514228742587-6b1558fcca51?w=600&h=600&fit=crop"),
    ("Fitness Tracker Band", "Slim activity band with heart rate and sleep tracking.", 49.99, "Fitness", "https://images.unsplash.com/photo-1575311373938-040b1e0c5d66?w=600&h=600&fit=crop"),
    ("Canvas Tote Bag", "Reusable organic cotton tote for shopping and travel.", 24.99, "Accessories", "https://images.unsplash.com/photo-1591561954550-6079686f0899?w=600&h=600&fit=crop"),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_url TEXT NOT NULL,
            stock INTEGER DEFAULT 50
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO products (name, description, price, category, image_url) VALUES (?, ?, ?, ?, ?)",
            SAMPLE_PRODUCTS,
        )

    conn.commit()
    conn.close()
