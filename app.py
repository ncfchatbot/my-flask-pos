import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# --- การตั้งค่า Database (รองรับทั้ง Local และ Server) ---
# 1. SECRET_KEY: ใช้สำหรับความปลอดภัยของ Session และ Form
#    - ถ้าอยู่บน Server (มี env variable) ให้ใช้คีย์จาก Server
#    - ถ้าอยู่ Local ให้ใช้คีย์สำรอง 'dev_fallback_secret...' (นายเปลี่ยนเองได้)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_fallback_secret_key_change_this')

# 2. DATABASE URI: ที่อยู่ของฐานข้อมูล
#    - พยายามดึงที่อยู่จาก Environment Variable 'DATABASE_URL' (สำหรับ Server)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # ถ้ามี DATABASE_URL แสดงว่าอยู่บน Server (เช่น Render) ให้ใช้ PostgreSQL
    # SQLAlchemy เวอร์ชั่นใหม่ๆ สามารถจัดการ 'postgres://' ได้เอง ไม่ต้องแปลงเป็น 'postgresql://' แล้ว
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("--- Using Production Database (PostgreSQL) ---")
else:
    # ถ้าไม่มี DATABASE_URL แสดงว่าอยู่ Local ให้ใช้ SQLite เหมือนเดิม
    # หาพาธเต็มของโฟลเดอร์ปัจจุบันที่ app.py อยู่
    basedir = os.path.abspath(os.path.dirname(__file__))
    # สร้างพาธเต็มไปยังไฟล์ site.db ในโฟลเดอร์ instance
    # ตรวจสอบและสร้างโฟลเดอร์ instance ถ้ายังไม่มี
    instance_path = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    db_path = os.path.join(instance_path, 'site.db')
    # ตั้งค่า DATABASE_URI โดยใช้พาธเต็ม (สังเกตว่ามี /// สามตัวสำหรับ Absolute Path)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    print(f"--- Using Local Development Database (SQLite) at: {db_path} ---")

# ปิดการแจ้งเตือนที่ไม่จำเป็น
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# เริ่มต้นใช้งาน SQLAlchemy
db = SQLAlchemy(app)

# --- Database Models (โครงสร้างตารางในฐานข้อมูล) ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    code = db.Column(db.String(20), unique=True, nullable=True)
    cost = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f"Product('{self.name}', '{self.price}', '{self.stock}')"

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

    def __repr__(self):
        return f"Order('{self.id}', '{self.order_date}', '{self.total_price}')"

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    cost_at_purchase = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f"OrderItem('{self.product_name}', '{self.quantity}', '{self.price_at_purchase}')"

# --- Routes (เส้นทางต่างๆ ของเว็บ) ---

@app.route('/')
def index():
    products = Product.query.all()
    total_sales = db.session.query(db.func.sum(Order.total_price)).filter(Order.payment_status == 'Paid').scalar() or 0
    
    total_cost = 0
    paid_orders = Order.query.filter_by(payment_status='Paid').all()
    for order in paid_orders:
        for item in order.items:
            total_cost += item.cost_at_purchase * item.quantity
            
    gross_profit = total_sales - total_cost
    
    return render_template('index.html', products=products, total_sales=total_sales, total_cost=total_cost, gross_profit=gross_profit)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        code = request.form.get('code')
        cost = float(request.form.get('cost', 0.0))
        
        image_file = request.files['image']
        if image_file:
            image_filename = image_file.filename
            # ตรวจสอบและสร้างโฟลเดอร์ static/product_images ถ้ายังไม่มี
            upload_folder = os.path.join('static', 'product_images')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            image_file.save(os.path.join(upload_folder, image_filename))
        else:
            image_filename = 'default.jpg'

        new_product = Product(name=name, price=price, stock=stock, image_file=image_filename, code=code, cost=cost)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.code = request.form.get('code')
        product.cost = float(request.form.get('cost', 0.0))

        image_file = request.files['image']
        if image_file and image_file.filename != '':