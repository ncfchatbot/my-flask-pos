import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# --- การตั้งค่า Database ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
database_url = os.environ.get('DATABASE_URL')

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'site.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    code = db.Column(db.String(20), unique=True, nullable=True)
    cost = db.Column(db.Float, nullable=False, default=0.0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), nullable=False, default='Pending')
    order_status = db.Column(db.String(20), nullable=False, default='Pending')
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_address = db.Column(db.Text, nullable=True)
    destination_branch = db.Column(db.String(100), nullable=True)
    transport_company = db.Column(db.String(50), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    cost_at_purchase = db.Column(db.Float, nullable=False, default=0.0)

# --- Routes ---
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        code = request.form.get('code')
        cost = float(request.form.get('cost', 0.0))
        
        image_filename = 'default.jpg'
        image_file = request.files['image']
        
        if image_file and image_file.filename != '':
            image_filename = image_file.filename
            upload_folder = os.path.join('static', 'product_images')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            image_file.save(os.path.join(upload_folder, image_filename))

        new_product = Product(name=name, price=price, stock=stock, image_file=image_filename, code=code, cost=cost)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_product.html')

# --- *** ส่วนสำคัญที่เพิ่มเข้ามาใหม่ *** ---
# ฟังก์ชันนี้จะทำงานก่อนที่ Request แรกจะเข้ามา
# เพื่อสร้างตาราง Database ทั้งหมดถ้ายังไม่มี
with app.app_context():
    db.create_all()
    print("--- Database tables checked/created ---")

# --- Main Entry Point (สำหรับ Local) ---
if __name__ == '__main__':
    app.run(debug=True)