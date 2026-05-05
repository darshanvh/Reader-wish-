# Reader Wish


Reader Wish is a web-based platform for managing and tracking books, orders, and user interactions. It provides both admin and user dashboards, book management, order processing, and wishlist features. The project is built using Flask and MongoDB, with AJAX-powered UI for a seamless user experience.

---

## Table of Contents

- [Features](#features)
- [Admin Module](#admin-module)
- [User Module](#user-module)
- [API Endpoints](#api-endpoints)
- [Database Structure](#database-structure)
- [Static Assets](#static-assets)
- [Templates](#templates)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)



## Features

- Admin dashboard for managing books, orders, deliveries, and users
- User dashboard for browsing books, managing cart, orders, and wishlist
- Book status tracking (available, sold out, deleted)
- Delivery status management
- General and book-specific feedback collection
- AJAX-powered UI for seamless interactions
- Theming support (light/dark mode)
- Secure authentication and session management
- Image upload for book covers

---

## Admin Module

Admin users can:
- View, add, edit, and delete books
- Manage book availability and status (available, sold out, deleted)
- View and manage all orders and delivery statuses
- View and manage user accounts
- Review general feedback from users

Admin templates:
   - available_books.html, books.html, book_management.html, book_status.html, dashboard.html, deleted_books.html, delivery.html, delivery_status.html, general_feedback.html, login.html, my_user.html, orders.html, order_details.html, selling_books.html, sold_out_books.html

## User Module

Users can:
- Browse books by category (fiction, nonfiction, etc.)
- View book details
- Add books to cart and wishlist
- Place orders and view order history
- Manage their account and profile
- Provide feedback

User templates:
   - book_details.html, cart.html, cart_checkout.html, category.html, dashboard.html, fiction_all.html, login.html, my_acc.html, my_orders.html, my_order_details.html, nonfiction_all.html, order.html, signup.html, wishlist.html

---

## API Endpoints

Some AJAX endpoints (see app.py):
- `/api/books` — Get all books (JSON)
- `/api/add-to-cart/<book_id>` — Add a book to cart (POST, AJAX)
- (Add more as implemented)

---

## Database Structure

MongoDB is used for data storage. Main collections (see config.py):
- users
- books
- orders
- cart
- wishlist
- feedback
- general_feedback

---

## Static Assets

- **static/css/**: Theme and style sheets (e.g., theme.css)
- **static/js/**: JavaScript files (e.g., theme-toggle.js)
- **static/images/**: Book covers, banners, and other images
- **static/uploads/books/**: Uploaded book images

---

## Templates

Jinja2 HTML templates for both admin and user interfaces are organized under `templates/admin/` and `templates/user/`.

---

## Project Structure

```
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── static/                 # Static files (CSS, JS, images, uploads)
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/books/
├── templates/              # HTML templates
│   ├── base.html
│   ├── admin/
│   └── user/
├── dashboard/              # (Purpose not specified)
└── AJAX-LOADER-GUIDE.md    # AJAX loader documentation
```


## Getting Started

1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python app.py
   ```
4. **Access the app:**
   Open your browser at `http://localhost:5000` (or the port specified in your config)


## Folder Details

- **static/**: Contains all static assets (CSS, JS, images, uploads)
- **templates/**: Jinja2 HTML templates for admin and user interfaces
- **dashboard/**: (Add description if used)
- **config.py**: MongoDB connection and collection setup
- **app.py**: Main Flask application logic and routes
- **requirements.txt**: Python dependencies


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License

Specify your license here (e.g., MIT, GPL, etc.)
