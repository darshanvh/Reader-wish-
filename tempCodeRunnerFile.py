import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session
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
        "Historical Fiction",
        "Horror",
        "Adventure",
        "Drama"
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
        "Textbooks"
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