# Global AJAX Loader Implementation Guide

## Overview
This guide shows how to use the global AJAX loader (`/static/ajax-loader.js`) in your Reader Wish project to display loading spinners during AJAX requests.

---

## Basic Usage

### Step 1: Include the Script
Add this line in the `<head>` section of any HTML template:
```html
<script src="/static/ajax-loader.js"></script>
```

### Step 2: Use the Functions
In your JavaScript code, use these functions:

```javascript
// Show the loader
showAjaxLoader();
// or with custom message
showAjaxLoader('Processing your request...');

// Hide the loader
hideAjaxLoader();
```

---

## Complete Example

```html
<!DOCTYPE html>
<html>
<head>
    <script src="/static/ajax-loader.js"></script>
</head>
<body>
    <button onclick="fetchData()">Load Data</button>

    <script>
        function fetchData() {
            showAjaxLoader('Fetching data...');
            
            fetch('/api/get-data')
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    hideAjaxLoader();
                })
                .catch(error => {
                    console.error(error);
                    hideAjaxLoader();
                });
        }
    </script>
</body>
</html>
```

---

## Use Cases in Your Project

### 1. Dashboard Filter (Already Updated)
In `templates/user/dashboard.html`, the filter functionality now uses the global loader:

```javascript
function applyFilters() {
    showAjaxLoader('Loading books...');
    
    fetch("/dashboard?" + params.toString(), {
        headers: {"X-Requested-With": "XMLHttpRequest"}
    })
    .then(response => response.json())
    .then(data => {
        // Process data...
        hideAjaxLoader();
    })
    .catch(error => {
        hideAjaxLoader();
    });
}
```

### 2. Add to Cart
```javascript
function addToCart(bookId) {
    showAjaxLoader('Adding to cart...');
    
    fetch(`/cart/add/${bookId}`)
        .then(response => response.json())
        .then(data => {
            // Handle response...
            hideAjaxLoader();
        })
        .catch(error => hideAjaxLoader());
}
```

### 3. Wishlist Toggle
```javascript
function toggleWishlist(bookId) {
    showAjaxLoader('Updating wishlist...');
    
    fetch(`/add-to-wishlist/${bookId}`)
        .then(response => response.json())
        .then(data => {
            // Handle response...
            hideAjaxLoader();
        })
        .catch(error => hideAjaxLoader());
}
```

### 4. Search/Filter Form
```javascript
document.getElementById('searchForm').addEventListener('submit', function(e) {
    e.preventDefault();
    showAjaxLoader('Searching...');
    
    fetch(this.action + '?' + new URLSearchParams(new FormData(this)))
        .then(response => response.json())
        .then(data => {
            // Display results...
            hideAjaxLoader();
        })
        .catch(error => hideAjaxLoader());
});
```

---

## Important Notes

1. **Always call `hideAjaxLoader()`** in both `.then()` and `.catch()` blocks
2. **Custom Messages**: Pass a custom message to `showAjaxLoader('Your message')`
3. **Automatic Cleanup**: If your request fails, don't forget to hide the loader
4. **Global Function**: Use `showAjaxLoader()` and `hideAjaxLoader()` from any page that includes the script
5. **Aliases Available**: You can also use `showLoader()` and `hideLoader()` as shortcuts

---

## Files Updated

- ✅ `/static/ajax-loader.js` - Global loader script
- ✅ `templates/user/dashboard.html` - Uses global loader for filters

---

## Next Steps

To implement the loader in other pages:
1. Add `<script src="/static/ajax-loader.js"></script>` to the `<head>`
2. Wrap your fetch calls with `showAjaxLoader()` and `hideAjaxLoader()`
3. Test in your browser

---

## Customization

To customize the loader appearance, edit `/static/ajax-loader.js` and modify the `.global-loader*` CSS classes.

