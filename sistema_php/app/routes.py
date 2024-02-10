import os
from flask import render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from app.app import app, db
from app.models import Product

UPLOAD_FOLDER = 'app/static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None

        new_product = Product(name=name, category=category, price=price, image=filename)
        db.session.add(new_product)
        db.session.commit()

    return render_template('index.html')

@app.route('/produto')
def produtos():
    products = Product.query.all()
    return render_template('produtos.html', products=products)
