import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

# ✅ IMPORT ALL COLLECTIONS
from config import (
    users_collection,
    books_collection,
    orders_collection,
    cart_collection,
    wishlist_collection,
    feedback_collection,
    general_feedback_collection
)

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ---------------- IMAGE UPLOAD CONFIG ----------------
UPLOAD_FOLDER = "static/uploads/books"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from flask import jsonify

# ✅ Get books (for AJAX loading / filtering)
@app.route("/api/books")
def get_books():
    books = list(books_collection.find())
    
    for b in books:
        b["_id"] = str(b["_id"])  # Convert ObjectId to string

    return jsonify(books)


# ✅ Add to cart (AJAX)
@app.route("/api/add-to-cart/<book_id>", methods=["POST"])
def api_add_to_cart(book_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"})

    user_id = ObjectId(session["user_id"])

    existing = cart_collection.find_one({
        "user_id": user_id,
        "book_id": ObjectId(book_id)
    })

    if not existing:
        cart_collection.insert_one({
            "user_id": user_id,
            "book_id": ObjectId(book_id)
        })

    return jsonify({"success": True})


# ✅ Remove from cart (AJAX)
@app.route("/api/remove-from-cart/<book_id>", methods=["POST"])
def api_remove_from_cart(book_id):
    user_id = ObjectId(session["user_id"])

    cart_collection.delete_one({
        "user_id": user_id,
        "book_id": ObjectId(book_id)
    })

    return jsonify({"success": True})


# ---------------- DEFAULT ----------------
@app.route("/")
def home():
    return redirect("/signup")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        password = request.form["password"]

        if users_collection.find_one({"phone": phone}):
            return "Phone number already registered!"

        users_collection.insert_one({
            "name": name,
            "phone": phone,
            "email": email,
            "password": generate_password_hash(password),
            "role": "user"
        })

        return redirect("/login")

    return render_template("user/signup.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]

        user = users_collection.find_one({"phone": phone})

        # ✅ USER NOT FOUND
        if not user:
            return "Invalid phone number or password!"

        # ✅ BLOCK CHECK (ADD THIS HERE)
        if user.get("is_blocked", False):
            return "🚫 Your account has been blocked by admin"

        # ✅ PASSWORD CHECK
        if not check_password_hash(user["password"], password):
            return "Invalid phone number or password!"

        # ✅ LOGIN SUCCESS
        session["user_id"] = str(user["_id"])
        session["role"] = user["role"]
        session["user"] = True
        session["user_name"] = user.get("name", "")
        return redirect("/dashboard")

    return render_template("user/login.html")


# ---------------- USER DASHBOARD ----------------
from flask import jsonify

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = ObjectId(session["user_id"])

    # ---------------- PAGINATION ----------------
    page = request.args.get("page", 1, type=int)
    per_page = 8   # 4 columns × 2 rows = 8 books
    skip = (page - 1) * per_page

    # ---------------- GET FILTER VALUES ----------------
    book_type = request.args.get("type")
    price_range = request.args.get("price")
    sort_option = request.args.get("sort")
    author = request.args.get("author")

    # ---------------- BASE QUERY ----------------
    query = {
        "is_deleted": False,
        "availability": True
    }

    # ---------------- TYPE FILTER ----------------
    if book_type:
        query["genre"] = book_type

    # ---------------- PRICE FILTER ----------------
    if price_range:
        if price_range == "0-5000":
            query["price"] = {"$lte": 5000}
        elif price_range == "5000-15000":
            query["price"] = {"$gte": 5000, "$lte": 15000}
        elif price_range == "15000-50000":
            query["price"] = {"$gte": 15000, "$lte": 50000}
        elif price_range == "50000+":
            query["price"] = {"$gte": 50000}

    # ---------------- FETCH BOOKS ----------------
    books_cursor = books_collection.find(query)

    # ---------------- SORTING ----------------
    if sort_option == "price-low":
        books_cursor = books_cursor.sort("price", 1)
    elif sort_option == "price-high":
        books_cursor = books_cursor.sort("price", -1)
    elif sort_option == "newest":
        books_cursor = books_cursor.sort("created_at", -1)
    elif sort_option == "price_low":
        books_cursor = books_cursor.sort("price", 1)
    elif sort_option == "price_high":
        books_cursor = books_cursor.sort("price", -1)
    elif sort_option == "name":
        books_cursor = books_cursor.sort("book_name", 1)

    # ---------------- TOTAL COUNT ----------------
    total_books = books_collection.count_documents(query)
    total_pages = (total_books + per_page - 1) // per_page

    # ---------------- APPLY PAGINATION ----------------
    books = list(
        books_cursor
        .skip(skip)
        .limit(per_page)
    )

    # ---------------- CART ITEMS ----------------
    cart_items = cart_collection.find({"user_id": user_id})
    cart_book_ids = [str(c["book_id"]) for c in cart_items]

    # ---------------- WISHLIST ITEMS ----------------
    wishlist_items = wishlist_collection.find({"user_id": user_id})
    wishlist_ids = [str(w["book_id"]) for w in wishlist_items]

    # ---------------- USER INFO ----------------
    user = users_collection.find_one({"_id": user_id}, {"password": 0})

    # =====================================================
    # ---------------- FICTION GENRE LIST -----------------
    # =====================================================

    fiction_genres = [
        "Fantasy",
        "Science Fiction",
        "Mystery",
        "Thriller",
        "Romance",
        "History",
        "Horror",
        "Adventure",
        "Drama",
        "Comedy"
    ]

    # ---------------- FICTION BOOKS (LIMIT 7) ----------------
    fiction_query = {
        "is_deleted": False,
        "availability": True,
        "$or": [
            {"category": "Fiction"},
            {"genre": {"$in": fiction_genres}}
        ]
    }

    fiction_books = list(
        books_collection.find(fiction_query).limit(7)
    )

    # =====================================================
    # ---------------- NON-FICTION GENRES -----------------
    # =====================================================

    non_fiction_genres = [
        "Biography",
        "Autobiography",
        "Self-Help",
        "History",
        "Science",
        "Travel",
        "Cookbooks",
        "Essay",
        "Academic",
        "Textbooks",
        "Romantic"
    ]

    # ---------------- NON-FICTION BOOKS (LIMIT 7) ----------------
    non_fiction_query = {
        "is_deleted": False,
        "availability": True,
        "genre": {"$in": non_fiction_genres}
    }

    non_fiction_books = list(
        books_collection.find(non_fiction_query).limit(7)
    )

    # =====================================================
    # ---------------- TOP RATED BOOKS --------------------
    # =====================================================
    
    # Get all available books
    all_books = list(books_collection.find({
        "is_deleted": False,
        "availability": True
    }))
    
    # Calculate average rating for each book
    books_with_ratings = []
    for book in all_books:
        feedbacks = list(feedback_collection.find({"book_id": book["_id"]}))
        if feedbacks:
            avg_rating = sum(f["rating"] for f in feedbacks) / len(feedbacks)
            review_count = len(feedbacks)
            book["avg_rating"] = round(avg_rating, 1)
            book["review_count"] = review_count
            books_with_ratings.append(book)
    
    # Sort by average rating (highest first) and limit to top 6
    top_rated_books = sorted(
        books_with_ratings, 
        key=lambda x: (x["avg_rating"], x["review_count"]), 
        reverse=True
    )[:6]

    # ---------------- AJAX RESPONSE ----------------
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify([
            {
                "_id": str(b["_id"]),
                "image": b["image"],
                "author": b.get("author", "Unknown"),
                "price": b["price"]
            } for b in books
        ])

    # ---------------- NORMAL RENDER ----------------
    return render_template(
        "user/dashboard.html",
        books=books,
        photos=books,
        page=page,
        fiction_books=fiction_books,
        non_fiction_books=non_fiction_books,
        top_rated_books=top_rated_books,
        total_pages=total_pages,
        cart_book_ids=cart_book_ids,
        wishlist_ids=wishlist_ids,
        user_name=user["name"] if user else ""
    )





# ---------------- REMOVE FROM CART ----------------
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login")

    user_id = ObjectId(session["user_id"])
    cart_items = cart_collection.find({"user_id": user_id})

    books = []
    for item in cart_items:
        book = books_collection.find_one({"_id": item["book_id"]})
        if book:
            books.append(book)

    return render_template("user/cart.html", books=books)

# ---------------- ADD TO CART ----------------
@app.route("/cart/add/<book_id>")
def add_to_cart(book_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = ObjectId(session["user_id"])
    book_obj_id = ObjectId(book_id)  # 👈 IMPORTANT

    if not cart_collection.find_one({
        "user_id": user_id,
        "book_id": book_obj_id
    }):
        cart_collection.insert_one({
            "user_id": user_id,
            "book_id": book_obj_id   # 👈 MUST be ObjectId
        })

    return redirect("/dashboard")


# ---------------- REMOVE FROM CART ----------------
@app.route("/cart/remove/<book_id>")
def remove_from_cart(book_id):
    if "user_id" not in session:
        return redirect("/login")

    cart_collection.delete_one({
        "user_id": ObjectId(session["user_id"]),
        "book_id": ObjectId(book_id)
    })

    return redirect("/cart")   # 👈 IMPORTANT


# ---------------- WISHLIST ----------------



# ---------------- WISHLIST ----------------
@app.route("/add-to-wishlist/<book_id>")
def add_to_wishlist(book_id):
    if "user_id" not in session:
        return redirect("/login")
    user_id = ObjectId(session["user_id"])
    book_obj_id = ObjectId(book_id)
    existing = wishlist_collection.find_one({"user_id": user_id, "book_id": book_obj_id})
    if existing:
        wishlist_collection.delete_one({"_id": existing["_id"]})
    else:
        wishlist_collection.insert_one({"user_id": user_id, "book_id": book_obj_id})
    return redirect(request.referrer or "/dashboard")


@app.route("/wishlist")
def wishlist():
    if "user_id" not in session:
        return redirect("/login")
    user_id = ObjectId(session["user_id"])
    wishlist_items = list(wishlist_collection.find({"user_id": user_id}))
    books = []
    for item in wishlist_items:
        book = books_collection.find_one({"_id": item["book_id"], "is_deleted": False})
        if book:
            books.append(book)
    return render_template("user/wishlist.html", books=books)


@app.route("/wishlist/remove/<book_id>")
def remove_from_wishlist(book_id):
    if "user_id" not in session:
        return redirect("/login")
    wishlist_collection.delete_one({"user_id": ObjectId(session["user_id"]), "book_id": ObjectId(book_id)})
    return redirect("/wishlist")
    return redirect("/cart")

# ---------------- BUY NOW ----------------
@app.route("/buy/<book_id>")
def buy_now(book_id):
    if "user_id" not in session:
        return redirect("/login")
    
    # Redirect to order page instead of receipt
    return redirect(f"/order/{book_id}")

# ---------------- UPDATE QUANTITY ----------------
@app.route("/update-quantity/<action>")
def update_quantity(action):
    if "checkout_book_id" not in session:
        return redirect("/dashboard")

    qty = session.get("quantity", 1)
    book = books_collection.find_one({"_id": ObjectId(session["checkout_book_id"])})

    if not book:
        return "Book not found!"

    if action == "plus" and qty < book["stock"]:  # Limit by stock
        qty += 1
    elif action == "minus" and qty > 1:
        qty -= 1

    session["quantity"] = qty

    return render_template("user/receipt.html", book=book, quantity=qty)


# ---------------- CHECKOUT DETAILS ----------------
@app.route("/checkout/details", methods=["GET", "POST"])
def checkout_details():
    if "user_id" not in session or "checkout_book_id" not in session:
        return redirect("/dashboard")

    book = books_collection.find_one(
        {"_id": ObjectId(session["checkout_book_id"])}
    )
    quantity = session.get("quantity", 1)

    if request.method == "POST":
        session["checkout_info"] = {
            "name": request.form["name"],
            "phone": request.form["phone"],
            "email": request.form["email"],
            "address": request.form["address"],
            "pin_code": request.form["pin_code"],
            "state": request.form["state"],
            "district": request.form["district"]
        }
        return redirect("/checkout/payment")

    return render_template("user/checkout_details.html", book=book, quantity=quantity)

# ---------------- PAYMENT ----------------
@app.route("/checkout/payment", methods=["GET", "POST"])
def checkout_payment():
    if (
        "user_id" not in session
        or "checkout_book_id" not in session
        or "checkout_info" not in session
    ):
        return redirect("/dashboard")

    book = books_collection.find_one(
        {"_id": ObjectId(session["checkout_book_id"])}
    )

    quantity = session.get("quantity", 1)
    total_price = book["price"] * quantity
    user_info = session["checkout_info"]

    if request.method == "POST":

        # ✅ CREATE ORDER
        orders_collection.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "book_id": book["_id"],
            "book_name": book["book_name"],
            "book_image": book.get("image"),
            "price": book["price"],
            "quantity": quantity,
            "total_price": total_price,
            "order_date": datetime.now(),
            "status": "Paid",
            "user_info": user_info
        })

        # ✅ REDUCE STOCK
        new_stock = book["stock"] - quantity
        books_collection.update_one(
            {"_id": book["_id"]},
            {
                "$inc": {"stock": -quantity},
                "$set": {"availability": new_stock > 0}
            }
        )

        cart_collection.delete_one({
            "user_id": ObjectId(session["user_id"]),
            "book_id": book["_id"]
        })

        session.clear()

        return render_template(
            "user/payment_success.html",
            book=book,
            quantity=quantity,
            total_price=total_price,
            user_info=user_info
        )

    return render_template(
        "user/payment.html",
        book=book,
        quantity=quantity,
        total_price=total_price,
        user_info=user_info
    )


# ---------------- CART CHECKOUT (BUY ALL) ----------------
@app.route("/cart/checkout", methods=["GET", "POST"])
def cart_checkout():
    if "user_id" not in session:
        return redirect("/login")

    user_id = ObjectId(session["user_id"])
    cart_items = list(cart_collection.find({"user_id": user_id}))

    if not cart_items:
        return "Your cart is empty!"

    # Gather book details and ensure availability
    books = []
    total_price = 0
    for item in cart_items:
        book = books_collection.find_one({"_id": item["book_id"]})
        if not book or book.get("stock", 0) < 1:
            return "One or more items in your cart are not available."  # simple guard
        books.append({
            "_id": book["_id"],
            "book_name": book["book_name"],
            "price": book["price"],
            "image": book.get("image"),
            "quantity": 1
        })
        total_price += book["price"] * 1

    if request.method == "POST":
        # Save checkout items and info to session and redirect to payment flow
        session["checkout_cart_items"] = [ {"book_id": str(b["_id"]), "quantity": b["quantity"]} for b in books ]
        session["checkout_info"] = {
            "name": request.form["name"],
            "phone": request.form["phone"],
            "email": request.form["email"],
            "address": request.form["address"],
            "pin_code": request.form["pin_code"],
            "state": request.form["state"],
            "district": request.form["district"]
        }
        return redirect("/checkout/payment_cart")

    # Prefill user info when available
    user = users_collection.find_one({"_id": user_id}, {"password": 0})

    return render_template("user/cart_checkout.html", books=books, total_price=total_price, user=user)


# ---------------- CART PAYMENT (MULTI ITEM) ----------------
@app.route("/checkout/payment_cart", methods=["GET", "POST"])
def checkout_payment_cart():
    if (
        "user_id" not in session
        or "checkout_cart_items" not in session
        or "checkout_info" not in session
    ):
        return redirect("/dashboard")

    # Reconstruct books from session
    cart_items = session["checkout_cart_items"]
    books = []
    total_price = 0

    for ci in cart_items:
        book = books_collection.find_one({"_id": ObjectId(ci["book_id"])})
        if not book:
            return "A book in your checkout is missing."
        qty = ci.get("quantity", 1)
        if book.get("stock", 0) < qty:
            return f"Not enough stock for {book['book_name']}"
        books.append({"book": book, "quantity": qty})
        total_price += book["price"] * qty

    user_info = session["checkout_info"]

    if request.method == "POST":
        # Create orders for each book
        created_orders = []
        for item in books:
            book = item["book"]
            qty = item["quantity"]
            order = {
                "user_id": ObjectId(session["user_id"]),
                "book_id": book["_id"],
                "book_name": book["book_name"],
                "book_image": book.get("image"),
                "price": book["price"],
                "quantity": qty,
                "total_price": book["price"] * qty,
                "order_date": datetime.now(),
                "status": "Paid",
                "user_info": user_info
            }
            orders_collection.insert_one(order)

            # Reduce stock
            books_collection.update_one(
                {"_id": book["_id"]},
                {
                    "$inc": {"stock": -qty},
                    "$set": {"availability": (book.get("stock", 0) - qty) > 0}
                }
            )

            # Remove from cart
            cart_collection.delete_one({"user_id": ObjectId(session["user_id"]), "book_id": book["_id"]})

            created_orders.append(order)

        # Clean up session keys related to checkout (keep user logged in)
        session.pop("checkout_cart_items", None)
        session.pop("checkout_info", None)

        return render_template("user/payment_success_cart.html", orders=created_orders, total_price=total_price, user_info=user_info)

    return render_template("user/payment_cart.html", books=books, total_price=total_price, user_info=user_info)


@app.route("/my-order/<order_id>")
def my_order_details(order_id):
    if "user_id" not in session:
        return redirect("/login")

    try:
        order_obj_id = ObjectId(order_id)
    except:
        return "Invalid Order ID"

    # Only the logged-in user can view their order
    order = orders_collection.find_one({
        "_id": order_obj_id,
        "user_id": ObjectId(session["user_id"])
    })

    if not order:
        return "Order not found!"

    # If order doesn't have user_info, fetch from users collection
    if "user_info" not in order:
        user = users_collection.find_one({"_id": ObjectId(session["user_id"])})
        if user:
            order["user_info"] = {
                "name": user.get("name", "N/A"),
                "phone": user.get("phone", "N/A"),
                "email": user.get("email", "N/A"),
                "address": user.get("address", "N/A"),
                "pin_code": user.get("pin_code", "N/A"),
                "state": user.get("state", "N/A")
            }

    return render_template("user/my_order_details.html", order=order)

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "darshan" and request.form["password"] == "darshanhegde":
            session["admin"] = True
            return redirect("/admin/dashboard")
        return "Invalid Admin Credentials!"

    return render_template("admin/login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin/login")
    
    # Get real statistics
    total_books = books_collection.count_documents({"is_deleted": False})
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    
    return render_template("admin/dashboard.html", 
                         total_books=total_books,
                         total_users=total_users,
                         total_orders=total_orders)

# ---------------- ADMIN BOOKS ----------------
@app.route("/admin/books")
def admin_books():
    if not session.get("admin"):
        return redirect("/admin/login")

    books = books_collection.find({"is_deleted": False})
    return render_template("admin/books.html", books=books)

# ---------------- ADD BOOK ----------------
@app.route("/admin/books/add", methods=["POST"])
def add_book():
    if not session.get("admin"):
        return redirect("/admin/login")

    image = request.files.get("image")
    image_filename = None

    if image and image.filename:
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

    initial_stock = int(request.form["stock"])

    books_collection.insert_one({
        "book_name": request.form["book_name"],
        "author": request.form["author"],
        "genre": request.form["genre"],
        "price": float(request.form["price"]),
        "initial_stock": initial_stock,
        "stock": initial_stock,
        "availability": True,
        "image": image_filename,
        "is_deleted": False
    })

    flash("Book added successfully!", "success")
    return redirect("/admin/books")

# ---------------- UPDATE BOOK ----------------
@app.route("/admin/books/update/<id>", methods=["POST"])
def update_book(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    books_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "book_name": request.form["book_name"],
            "author": request.form["author"],
            "genre": request.form["genre"],
            "price": float(request.form["price"]),
            "stock": int(request.form["stock"]),
            "availability": int(request.form["stock"]) > 0
        }}
    )

    return redirect("/admin/books")

# ---------------- DELETE BOOK ----------------
@app.route("/admin/books/delete/<id>")
def delete_book(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    books_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_deleted": True}}
    )

    return redirect("/admin/books/status")


# ---------------- RESTORE BOOK ----------------
@app.route("/admin/books/restore/<id>")
def restore_book(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    books_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_deleted": False}}
    )

    return redirect("/admin/books/status")

# ---------------- BOOK STATUS ----------------
@app.route("/admin/books/status")
def book_status():
    if not session.get("admin"):
        return redirect("/admin/login")

    all_books = list(books_collection.find())

    for book in all_books:
        book["is_deleted"] = book.get("is_deleted", False)
        book["initial_stock"] = book.get("initial_stock", book.get("stock", 0))
        book["stock"] = book.get("stock", 0)
        book["sold"] = book["initial_stock"] - book["stock"]

    available_books = [
        b for b in all_books if not b["is_deleted"] and b["stock"] > 0
    ]
    sold_books = [
        b for b in all_books if not b["is_deleted"] and b["stock"] == 0
    ]
    deleted_books = [
        b for b in all_books if b["is_deleted"]
    ]

    return render_template(
        "admin/book_status.html",
        all_books=all_books,
        available_books=available_books,
        sold_books=sold_books,
        deleted_books=deleted_books
    )


# ---------------- ADMIN ORDERS ----------------
@app.route("/admin/orders")
def admin_orders():
    if not session.get("admin"):
        return redirect("/admin/login")

    orders = list(orders_collection.find().sort("order_date", -1))

    unique_books = {}
    for order in orders:
        book_id = str(order["book_id"])

        # keep only one order per book
        if book_id not in unique_books:
            unique_books[book_id] = order

    return render_template(
        "admin/orders.html",
        orders=unique_books.values()
    )


@app.route("/admin/order/<book_id>")
def admin_order_details(book_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    try:
        book_obj_id = ObjectId(book_id)
    except:
        return "Invalid Book ID"

    orders = list(orders_collection.find({"book_id": book_obj_id}).sort("order_date", -1))

    if not orders:
        return "No orders found for this book"

    return render_template(
        "admin/order_details.html",
        orders=orders,
        book_name=orders[0]["book_name"]
    )
# ---------------- ADMIN BOOK MANAGEMENT ----------------

@app.route("/admin/book-management")
def admin_book_management():
    if not session.get("admin"):
        return redirect("/admin/login")

    books = list(books_collection.find())
    return render_template("admin/book_management.html", books=books)



@app.route("/admin/books/delete/permanent/<id>")
def delete_book_permanent(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    # 🔥 HARD DELETE (permanent)
    books_collection.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/book-management")





# ---------------- USER ORDERS ----------------
@app.route("/my-orders")
def my_orders():
    if "user_id" not in session:
        return redirect("/login")

    orders = list(
        orders_collection.find(
            {"user_id": ObjectId(session["user_id"])}
        ).sort("order_date", -1)
    )

    return render_template("user/my_orders.html", orders=orders)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")



@app.route("/my-acc")
def my_account():
    if "user_id" not in session:
        return redirect("/login")

    user = users_collection.find_one(
        {"_id": ObjectId(session["user_id"])},
        {"password": 0}  # do NOT send password to template
    )

    return render_template("user/my_acc.html", user=user)


    # ---------------- ADMIN USERS ----------------
@app.route("/admin/users")
def admin_users():
    if not session.get("admin"):
        return redirect("/admin/login")

    users = list(users_collection.find({}, {"password": 0}))  # exclude password
    return render_template("admin/my_user.html", users=users)


@app.route("/admin/user/block/<user_id>")
def block_user(user_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_blocked": True}}
    )
    return redirect("/admin/users")


@app.route("/admin/user/unblock/<user_id>")
def unblock_user(user_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_blocked": False}}
    )
    return redirect("/admin/users")

@app.route("/admin/user/delete/<user_id>")
def delete_user(user_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    users_collection.delete_one({"_id": ObjectId(user_id)})
    return redirect("/admin/users")



# ---------------- ADMIN AVAILABLE BOOKS ----------------
@app.route("/admin/available_bookss")
def admin_available_books():
    if not session.get("admin"):
        return redirect("/admin/login")

    available_books = list(
        books_collection.find({
            "is_deleted": False,
            "availability": True,
            "stock": {"$gt": 0}
        })
    )

    return render_template(
        "admin/available_books.html",
        books=available_books
    )


# ---------------- ADMIN SOLD OUT BOOKS ----------------
@app.route("/admin/sold_out_books")
def admin_sold_out_books():
    if not session.get("admin"):
        return redirect("/admin/login")

    sold_out_books = list(
        books_collection.find({
            "is_deleted": False,
            "stock": 0
        })
    )

    return render_template(
        "admin/sold_out_books.html",
        books=sold_out_books
    )


# ---------------- ADMIN DELETED BOOKS (SOFT DELETE) ----------------
@app.route("/admin/deleted_books")
def admin_deleted_books():
    if not session.get("admin"):
        return redirect("/admin/login")

    deleted_books = list(
        books_collection.find({
            "is_deleted": True
        })
    )

    return render_template(
        "admin/deleted_books.html",
        books=deleted_books
    )

# ---------------- ADMIN SELLING BOOKS (WITH DATE FILTER) ----------------
@app.route("/admin/selling_books")
def admin_selling_books():
    if not session.get("admin"):
        return redirect("/admin/login")

    selected_date = request.args.get("date")  # YYYY-MM-DD from calendar

    query = {}

    if selected_date:
        start = datetime.strptime(selected_date, "%Y-%m-%d")
        end = start.replace(hour=23, minute=59, second=59)

        query["order_date"] = {
            "$gte": start,
            "$lte": end
        }

    orders = list(
        orders_collection.find(query).sort("order_date", -1)
    )

    grouped_orders = {}

    for order in orders:
        date_key = order["order_date"].strftime("%d-%m-%Y")

        if date_key not in grouped_orders:
            grouped_orders[date_key] = []

        grouped_orders[date_key].append(order)

    return render_template(
        "admin/selling_books.html",
        grouped_orders=grouped_orders,
        selected_date=selected_date
    )


# ---------------- CATEGORY PAGE ----------------
@app.route("/category/<genre>")
def category_page(genre):
    if "user_id" not in session:
        return redirect("/login")

    user_id = ObjectId(session["user_id"])

    # Fetch books of that genre only
    books = list(books_collection.find({
        "genre": genre,
        "is_deleted": False,
        "availability": True
    }))

    # Cart IDs
    cart_items = cart_collection.find({"user_id": user_id})
    cart_book_ids = [str(c["book_id"]) for c in cart_items]

    # Wishlist IDs
    wishlist_items = wishlist_collection.find({"user_id": user_id})
    wishlist_ids = [str(w["book_id"]) for w in wishlist_items]

    return render_template(
        "user/category.html",
        books=books,
        genre=genre,
        cart_book_ids=cart_book_ids,
        wishlist_ids=wishlist_ids
    )

@app.route("/fiction")
def fiction():
    fiction_books = list(
        books_collection.find({
            "is_deleted": False,
            "availability": True,
            "category": "Fiction"
        })
    )
    return render_template("fiction.html", fiction_books=fiction_books)


@app.route("/fiction-all")
def fiction_all():
    if not session.get("user"):
        return redirect("/login")

    fiction_genres = [
        "Fantasy",
        "Science Fiction",
        "Mystery",
        "Thriller",
        "Romance",
        "Historical Fiction",
        "Horror",
        "Adventure",
        "Drama"
    ]

    fiction_books = list(
        books_collection.find({
            "is_deleted": False,
            "availability": True,
            "genre": {"$in": fiction_genres}
        })
    )

    # Get user wishlist & cart ids (if you already have this logic elsewhere, reuse it)
    user_mobile = session["user"]

    wishlist_ids = []
    cart_book_ids = []

    user_data = users_collection.find_one({"mobile": user_mobile})
    if user_data:
        wishlist_ids = [str(i) for i in user_data.get("wishlist", [])]
        cart_book_ids = [str(i) for i in user_data.get("cart", [])]

    return render_template(
        "user/fiction_all.html",
        fiction_books=fiction_books,
        wishlist_ids=wishlist_ids,
        cart_book_ids=cart_book_ids
    )

@app.route("/nonfiction-all")
def nonfiction_all():
    if not session.get("user"):
        return redirect("/login")

    non_fiction_genres = [
        "Biography",
        "Autobiography",
        "Self-Help",
        "History",
        "Science",
        "Travel",
        "Cookbooks",
        "Essay",
        "Academic",
        "Textbooks"
    ]

    non_fiction_books = list(
        books_collection.find({
            "is_deleted": False,
            "availability": True,
            "genre": {"$in": non_fiction_genres}
        })
    )

    # Same user logic as fiction
    user_mobile = session["user"]

    wishlist_ids = []
    cart_book_ids = []

    user_data = users_collection.find_one({"mobile": user_mobile})
    if user_data:
        wishlist_ids = [str(i) for i in user_data.get("wishlist", [])]
        cart_book_ids = [str(i) for i in user_data.get("cart", [])]

    return render_template(
        "user/nonfiction_all.html",
        non_fiction_books=non_fiction_books,
        wishlist_ids=wishlist_ids,
        cart_book_ids=cart_book_ids
    )

# ---------------- ORDER FLOW ----------------
# Step 1: Redirect to order page
@app.route("/buy/<id>")
def buy_now_redirect(id):
    if "user_id" not in session:
        return redirect("/login")
    return redirect(f"/order/{id}")

# Step 1: Quantity Selection (GET) & Submit (POST)
@app.route("/order/<id>", methods=["GET", "POST"])
def order_page(id):
    if "user_id" not in session:
        return redirect("/login")
    
    try:
        book = books_collection.find_one({"_id": ObjectId(id)})
    except:
        return "Invalid Book ID"
    
    if not book:
        return "Book not found"
    
    if request.method == "POST":
        quantity = int(request.form.get("quantity", 1))
        total = book["price"] * quantity
        
        # Store in session for next step
        session["order_data"] = {
            "book_id": str(id),
            "book_name": book.get("book_name", ""),
            "author": book.get("author", ""),
            "price": book["price"],
            "image": book.get("image", ""),
            "quantity": quantity,
            "total": total
        }
        
        return redirect(f"/order/{id}/details")
    
    return render_template("user/order.html", product=book, product_id=id, step=1)

# Step 2: Delivery Details Form
@app.route("/order/<id>/details", methods=["GET", "POST"])
def order_details(id):
    if "user_id" not in session:
        return redirect("/login")
    
    # Get product info from session
    order_data = session.get("order_data")
    if not order_data or order_data.get("book_id") != str(id):
        return redirect(f"/order/{id}")
    
    if request.method == "POST":
        name = request.form.get("name")
        mobile = request.form.get("mobile")
        email = request.form.get("email")
        address = request.form.get("address")
        pin_code = request.form.get("pin_code")
        state = request.form.get("state")
        
        # Store delivery details in session
        session["delivery_data"] = {
            "name": name,
            "mobile": mobile,
            "email": email,
            "address": address,
            "pin_code": pin_code,
            "state": state
        }
        
        return redirect(f"/order/{id}/receipt")
    
    # Get product details
    product = {
        "book_name": order_data.get("book_name", ""),
        "author": order_data.get("author", ""),
        "price": order_data.get("price", 0),
        "image": order_data.get("image", "")
    }
    
    return render_template(
        "user/order.html",
        product=product,
        product_id=id,
        step=2,
        quantity=order_data.get("quantity", 1),
        total=order_data.get("total", 0)
    )

# Step 3: Receipt Page
@app.route("/order/<id>/receipt")
def order_receipt(id):
    if "user_id" not in session:
        return redirect("/login")
    
    order_data = session.get("order_data")
    delivery_data = session.get("delivery_data")
    
    if not order_data or not delivery_data or order_data.get("book_id") != str(id):
        return redirect(f"/order/{id}")
    
    # Generate order ID
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    order_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    # Save order to database
    user_id = ObjectId(session["user_id"])
    
    orders_collection.insert_one({
        "order_id": order_id,
        "user_id": user_id,
        "book_id": ObjectId(id),
        "book_name": order_data.get("book_name", ""),
        "book_image": order_data.get("image", ""),
        "author": order_data.get("author", ""),
        "price": order_data.get("price", 0),
        "quantity": order_data.get("quantity", 1),
        "total_price": order_data.get("total", 0),
        "user_info": {
            "name": delivery_data.get("name", ""),
            "phone": delivery_data.get("mobile", ""),
            "email": delivery_data.get("email", ""),
            "address": delivery_data.get("address", ""),
            "pin_code": delivery_data.get("pin_code", ""),
            "state": delivery_data.get("state", "")
        },
        "order_date": datetime.now(),
        "status": "Pending"
    })
    
    # Clear session data
    session.pop("order_data", None)
    session.pop("delivery_data", None)
    
    product = {
        "book_name": order_data.get("book_name", ""),
        "author": order_data.get("author", ""),
        "price": order_data.get("price", 0),
        "image": order_data.get("image", "")
    }
    
    return render_template(
        "user/order.html",
        product=product,
        product_id=id,
        step=3,
        order_id=order_id,
        order_date=order_date,
        name=delivery_data.get("name", ""),
        mobile=delivery_data.get("mobile", ""),
        email=delivery_data.get("email", ""),
        address=delivery_data.get("address", ""),
        pin_code=delivery_data.get("pin_code", ""),
        state=delivery_data.get("state", ""),
        quantity=order_data.get("quantity", 1),
        total=order_data.get("total", 0)
    )

# ---------------- FEEDBACK SYSTEM ----------------
# Get book details with feedback
@app.route("/book/<book_id>")
def book_details(book_id):
    if "user_id" not in session:
        return redirect("/login")
    
    try:
        book = books_collection.find_one({"_id": ObjectId(book_id)})
    except:
        return "Invalid Book ID"
    
    if not book:
        return "Book not found"
    
    # Get all feedback for this book
    feedbacks = list(feedback_collection.find({"book_id": ObjectId(book_id)}).sort("created_at", -1))
    
    # Get user names for each feedback
    for feedback in feedbacks:
        user = users_collection.find_one({"_id": feedback["user_id"]}, {"name": 1})
        feedback["user_name"] = user["name"] if user else "Anonymous"
    
    # Check if current user already gave feedback
    user_feedback = feedback_collection.find_one({
        "book_id": ObjectId(book_id),
        "user_id": ObjectId(session["user_id"])
    })
    
    return render_template(
        "user/book_details.html",
        book=book,
        feedbacks=feedbacks,
        user_feedback=user_feedback
    )

# Add feedback
@app.route("/book/<book_id>/feedback", methods=["POST"])
def add_feedback(book_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"})
    
    try:
        rating = int(request.form.get("rating", 0))
        comment = request.form.get("comment", "").strip()
        
        if rating < 1 or rating > 5:
            return jsonify({"success": False, "message": "Rating must be between 1 and 5"})
        
        if not comment:
            return jsonify({"success": False, "message": "Comment is required"})
        
        # Check if user already gave feedback
        existing = feedback_collection.find_one({
            "book_id": ObjectId(book_id),
            "user_id": ObjectId(session["user_id"])
        })
        
        if existing:
            # Update existing feedback
            feedback_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "rating": rating,
                    "comment": comment,
                    "updated_at": datetime.now()
                }}
            )
        else:
            # Add new feedback
            feedback_collection.insert_one({
                "book_id": ObjectId(book_id),
                "user_id": ObjectId(session["user_id"]),
                "rating": rating,
                "comment": comment,
                "created_at": datetime.now()
            })
        
        return jsonify({"success": True, "message": "Feedback submitted successfully"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Edit feedback
@app.route("/book/<book_id>/feedback/edit", methods=["POST"])
def edit_feedback(book_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"})
    
    try:
        rating = int(request.form.get("rating", 0))
        comment = request.form.get("comment", "").strip()
        
        if rating < 1 or rating > 5:
            return jsonify({"success": False, "message": "Rating must be between 1 and 5"})
        
        if not comment:
            return jsonify({"success": False, "message": "Comment is required"})
        
        # Update user's feedback
        result = feedback_collection.update_one(
            {
                "book_id": ObjectId(book_id),
                "user_id": ObjectId(session["user_id"])
            },
            {"$set": {
                "rating": rating,
                "comment": comment,
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Feedback updated successfully"})
        else:
            return jsonify({"success": False, "message": "Feedback not found"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Delete feedback
@app.route("/book/<book_id>/feedback/delete", methods=["POST"])
def delete_feedback(book_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"})
    
    try:
        result = feedback_collection.delete_one({
            "book_id": ObjectId(book_id),
            "user_id": ObjectId(session["user_id"])
        })
        
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "Feedback deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Feedback not found"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Get feedback for a book (AJAX)
@app.route("/api/book/<book_id>/feedback")
def get_book_feedback(book_id):
    try:
        feedbacks = list(feedback_collection.find({"book_id": ObjectId(book_id)}).sort("created_at", -1))
        
        result = []
        for feedback in feedbacks:
            user = users_collection.find_one({"_id": feedback["user_id"]}, {"name": 1})
            result.append({
                "user_name": user["name"] if user else "Anonymous",
                "rating": feedback["rating"],
                "comment": feedback["comment"],
                "created_at": feedback["created_at"].strftime("%d-%m-%Y %H:%M")
            })
        
        return jsonify({"success": True, "feedbacks": result})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ---------------- GENERAL FEEDBACK (FOOTER) ----------------
@app.route("/submit-general-feedback", methods=["POST"])
def submit_general_feedback():
    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        
        if not name or not email or not message:
            return jsonify({"success": False, "message": "All fields are required"})
        
        # Save feedback to database
        general_feedback_collection.insert_one({
            "name": name,
            "email": email,
            "message": message,
            "user_id": ObjectId(session["user_id"]) if "user_id" in session else None,
            "created_at": datetime.now(),
            "status": "pending"
        })
        
        return jsonify({"success": True, "message": "Thank you for your feedback!"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ---------------- ADMIN VIEW GENERAL FEEDBACK ----------------
@app.route("/admin/general-feedback")
def admin_general_feedback():
    if not session.get("admin"):
        return redirect("/admin/login")
    
    feedbacks = list(general_feedback_collection.find().sort("created_at", -1))
    
    return render_template("admin/general_feedback.html", feedbacks=feedbacks)

# ---------------- ADMIN DELETE GENERAL FEEDBACK ----------------
@app.route("/admin/general-feedback/delete/<feedback_id>")
def delete_general_feedback(feedback_id):
    if not session.get("admin"):
        return redirect("/admin/login")
    
    general_feedback_collection.delete_one({"_id": ObjectId(feedback_id)})
    
    return redirect("/admin/general-feedback")

# ---------------- ADMIN DELIVERY ----------------
@app.route("/admin/delivery")
def admin_delivery():
    if not session.get("admin"):
        return redirect("/admin/login")
    
    # Get orders that are pending (not picked up yet)
    orders = list(orders_collection.find({"status": {"$in": ["Paid", "Pending"]}}).sort("order_date", -1))
    
    # Enrich orders with book details
    for order in orders:
        book = books_collection.find_one({"_id": order["book_id"]})
        if book:
            order["book_name"] = book["book_name"]
            order["book_image"] = book.get("image", "")
            order["book_price"] = book["price"]
    
    return render_template("admin/delivery.html", orders=orders)

# ---------------- ADMIN DELIVERY STATUS ----------------
@app.route("/admin/delivery-status")
def admin_delivery_status():
    if not session.get("admin"):
        return redirect("/admin/login")
    
    # Get orders that are picked up but not delivered yet
    orders = list(orders_collection.find({"status": "Picked Up"}).sort("pickup_time", -1))
    
    # Enrich orders with book details
    for order in orders:
        book = books_collection.find_one({"_id": order["book_id"]})
        if book:
            order["book_name"] = book["book_name"]
            order["book_image"] = book.get("image", "")
            order["book_price"] = book["price"]
    
    return render_template("admin/delivery_status.html", orders=orders)

# ---------------- PICKUP ORDER ----------------
@app.route("/admin/delivery/pickup/<order_id>")
def pickup_order(order_id):
    if not session.get("admin"):
        return redirect("/admin/login")
    
    try:
        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {
                "status": "Picked Up",
                "pickup_time": datetime.now()
            }}
        )
    except:
        pass
    
    return redirect("/admin/delivery")

# ---------------- CANCEL PICKUP ----------------
@app.route("/admin/delivery-status/cancel/<order_id>")
def cancel_pickup(order_id):
    if not session.get("admin"):
        return redirect("/admin/login")
    
    try:
        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "Pending"},
             "$unset": {"pickup_time": "", "delivered_time": ""}}
        )
    except:
        pass
    
    return redirect("/admin/delivery-status")

# ---------------- MARK AS DELIVERED ----------------
@app.route("/admin/delivery-status/delivered/<order_id>")
def mark_delivered(order_id):
    if not session.get("admin"):
        return redirect("/admin/login")
    
    try:
        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {
                "status": "Delivered",
                "delivered_time": datetime.now()
            }}
        )
    except:
        pass
    
    return redirect("/admin/delivery-status")
    
    return redirect("/admin/delivery-status")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
