from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"

client = MongoClient(MONGO_URI)

db = client["book_store_db"]

# Collections
users_collection = db["users"]
books_collection = db["books"]
orders_collection = db["orders"]
cart_collection = db["cart"]
wishlist_collection = db["wishlist"]
feedback_collection = db["feedback"]
general_feedback_collection = db["general_feedback"]
