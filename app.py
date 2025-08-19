import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_database('ratnas_bridal')
products_collection = db.products

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# Admin credentials for demonstration purposes
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# --- Define a single source of truth for categories ---
# This list is used for generating the home page links and the admin dropdown.
# This ensures consistency across the site.
COLLECTIONS_DATA = [
    {"name": "Bridal Jewellery Sets", "url_name": "bridal-jewellery-sets", "image": "set1.jpg"},
    {"name": "Necklace & Earring Sets", "url_name": "necklace-earring-sets", "image": "img12.jpg"},
    {"name": "Exquisite Kundan & Polki", "url_name": "exquisite-kundan-polki", "image": "img17.jpg"},
    {"name": "Bracelets & Bangles", "url_name": "bracelets-bangles", "image": "bangle1.jpg"}
]

# --- Helper function to create a URL-friendly name ---
def create_url_friendly_name(text):
    """
    Converts a string to a URL-friendly format.
    Example: "Necklace & Earring Sets" -> "necklace-earring-sets"
    """
    import re
    # Remove all non-alphanumeric characters (except spaces) and convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
    # Replace spaces with hyphens
    return re.sub(r'\s+', '-', text)


# --- PUBLIC-FACING ROUTES ---
@app.route('/')
def home():
    # Pass collections data to the index page for dynamic links
    return render_template('index.html', collections=COLLECTIONS_DATA)

@app.route('/index.html')
def redirect_to_home():
    return redirect(url_for('home'))

@app.route('/category/<category_url_name>')
def category(category_url_name):
    # Retrieve the product from the database using the URL-friendly name
    products = list(products_collection.find({'category_url_name': category_url_name}))
    
    # Capitalize the display name
    if products:
        display_name = products[0]['category']
    else:
        # Fallback if no products are found, convert URL-friendly name back to title case
        display_name = category_url_name.replace('-', ' ').title()

    return render_template('category.html', products=products, category_name=display_name)


# --- ADMIN ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return jsonify({'success': True, 'redirect_url': url_for('admin_dashboard')})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401
    
    return render_template('login.html')

@app.route('/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    try:
        # Get category names from the predefined list
        categories = [d["name"] for d in COLLECTIONS_DATA]
        products = list(products_collection.find())
    except Exception as e:
        return f"<h1>Database Error</h1><p>Failed to fetch data: {e}</p>", 500

    for product in products:
        product['_id'] = str(product['_id']) 

    return render_template('dashboard.html', products=products, categories=categories)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    if not session.get('logged_in'):
        return jsonify({'message': 'Unauthorized'}), 401

    if request.method == 'POST':
        try:
            category = request.form['category']
            name = request.form['name']
            image_file = request.files['image']
            
            # Create a URL-friendly name for the category using the new helper function
            category_url_name = create_url_friendly_name(category)
            
            upload_result = cloudinary.uploader.upload(image_file)
            image_url = upload_result['secure_url']

            new_product = {
                'category': category,
                'category_url_name': category_url_name, # Save the URL-friendly name
                'name': name,
                'image': image_url
            }
            products_collection.insert_one(new_product)
            return jsonify({'success': True}), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
            
    products = list(products_collection.find())
    for product in products:
        product['_id'] = str(product['_id'])
    return jsonify(products)


@app.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        product_to_edit = products_collection.find_one({'_id': ObjectId(product_id)})
        if not product_to_edit:
            return "Product not found", 404
        
        # Get category names from the predefined list to populate the dropdown
        categories = [d["name"] for d in COLLECTIONS_DATA]
        return render_template('edit-product.html', product=product_to_edit, categories=categories)
        
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            name = request.form.get('name')
            
            # Create the URL-friendly name for the new category
            category_url_name = create_url_friendly_name(category)

            update_data = {
                'category': category,
                'category_url_name': category_url_name, # Update URL name to match new category
                'name': name,
            }

            image_file = request.files.get('image')
            if image_file and image_file.filename != '':
                upload_result = cloudinary.uploader.upload(image_file)
                update_data['image'] = upload_result['secure_url']

            products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not session.get('logged_in'):
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        products_collection.delete_one({'_id': ObjectId(product_id)})
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
        
