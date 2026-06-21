import os
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-shop-secret-change-in-production")


@app.before_request
def before_request():
    g.db = get_connection()


@app.teardown_request
def teardown_request(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)

    return wrapped


def get_cart():
    return session.setdefault("cart", {})


def cart_count():
    cart = get_cart()
    return sum(cart.values())


def cart_items():
    cart = get_cart()
    if not cart:
        return [], 0.0

    placeholders = ",".join("?" * len(cart))
    rows = g.db.execute(
        f"SELECT * FROM products WHERE id IN ({placeholders})",
        list(cart.keys()),
    ).fetchall()

    items = []
    total = 0.0
    for row in rows:
        qty = cart[str(row["id"])]
        subtotal = row["price"] * qty
        total += subtotal
        items.append({"product": row, "quantity": qty, "subtotal": subtotal})
    return items, total


@app.context_processor
def inject_globals():
    return {"cart_count": cart_count(), "current_user": session.get("user_name")}


@app.route("/")
def index():
    featured = g.db.execute(
        "SELECT * FROM products ORDER BY id LIMIT 8"
    ).fetchall()
    categories = g.db.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    return render_template("index.html", featured=featured, categories=categories)


@app.route("/products")
def products():
    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY name"
    items = g.db.execute(query, params).fetchall()
    categories = g.db.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()

    return render_template(
        "products.html",
        products=items,
        categories=categories,
        active_category=category,
        search=search,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = g.db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    related = g.db.execute(
        "SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4",
        (product["category"], product_id),
    ).fetchall()
    return render_template("product_detail.html", product=product, related=related)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    product = g.db.execute(
        "SELECT id FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    cart = get_cart()
    key = str(product_id)
    cart[key] = cart.get(key, 0) + int(request.form.get("quantity", 1))
    session.modified = True
    flash("Item added to cart.", "success")
    return redirect(request.referrer or url_for("cart"))


@app.route("/cart")
def cart():
    items, total = cart_items()
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/update/<int:product_id>", methods=["POST"])
def cart_update(product_id):
    cart = get_cart()
    key = str(product_id)
    quantity = int(request.form.get("quantity", 1))

    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = quantity

    session.modified = True
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def cart_remove(product_id):
    cart = get_cart()
    cart.pop(str(product_id), None)
    session.modified = True
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_items()
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not email or not address:
            flash("Please fill in all shipping details.", "error")
            return render_template("checkout.html", items=items, total=total)

        cursor = g.db.execute(
            """INSERT INTO orders (user_id, customer_name, customer_email, shipping_address, total)
               VALUES (?, ?, ?, ?, ?)""",
            (session.get("user_id"), name, email, address, total),
        )
        order_id = cursor.lastrowid

        for item in items:
            g.db.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    order_id,
                    item["product"]["id"],
                    item["product"]["name"],
                    item["quantity"],
                    item["product"]["price"],
                ),
            )
            g.db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["product"]["id"]),
            )

        g.db.commit()
        session["cart"] = {}
        session.modified = True
        return redirect(url_for("order_confirmation", order_id=order_id))

    default_name = session.get("user_name", "")
    default_email = session.get("user_email", "")
    return render_template(
        "checkout.html",
        items=items,
        total=total,
        default_name=default_name,
        default_email=default_email,
    )


@app.route("/order/<int:order_id>")
def order_confirmation(order_id):
    order = g.db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        flash("Order not found.", "error")
        return redirect(url_for("index"))

    order_items_rows = g.db.execute(
        "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    return render_template(
        "order_confirmation.html", order=order, order_items=order_items_rows
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            existing = g.db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                flash("An account with this email already exists.", "error")
            else:
                g.db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                g.db.commit()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = g.db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("index"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/orders")
@login_required
def orders():
    rows = g.db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("orders.html", orders=rows)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
