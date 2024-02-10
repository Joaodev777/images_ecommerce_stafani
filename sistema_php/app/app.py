import os
from flask import Flask, render_template, request, redirect, url_for, flash

import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

DATABASE = 'database.db'
UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def create_tables():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS product (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER,
                    image TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS customer (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS sale (
                    id INTEGER PRIMARY KEY,
                    customer_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    cpf TEXT,
                    address TEXT,
                    payment_method TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customer(id))''')

    conn.commit()
    conn.close()
    
    
def create_upload_folder():
    upload_path = os.path.join(app.root_path, UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

create_tables()
create_upload_folder()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        quantity = request.form['quantity']  # Captura a quantidade do produto
        image = request.files['image']

        filename = None

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.root_path, UPLOAD_FOLDER, filename))

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO product (name, category, price, quantity, image) VALUES (?, ?, ?, ?, ?)",
                    (name, category, price, quantity, filename))
        conn.commit()
        conn.close()

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM product")
    products = cur.fetchall()
    conn.close()

    print(products)

    return render_template('index.html', products=products)

@app.route('/delete_product', methods=['POST'])
def delete_product():
    if request.method == 'POST':
        product_id = request.form['product_id']

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM product WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        
        flash('Produto excluído com sucesso!', 'success')

    return redirect(url_for('index'))


@app.route('/produtos')
def produtos():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This makes each row a dictionary
    cur = conn.cursor()
    cur.execute("SELECT * FROM product")
    products = cur.fetchall()
    conn.close()
    return render_template('produtos.html', products=products)
@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_email = request.form['customer_email']
        product_name = request.form['product_name']
        quantity = int(request.form['quantity'])
        customer_cpf = request.form['customer_cpf']
        customer_address = request.form['customer_address']
        payment_method = request.form['payment_method']

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()

        # Inserir dados do cliente no banco de dados
        cur.execute("INSERT INTO customer (name, email) VALUES (?, ?)", (customer_name, customer_email))
        customer_id = cur.lastrowid

        # Inserir dados da venda no banco de dados
        cur.execute("INSERT INTO sale (customer_id, product_name, quantity, cpf, address, payment_method) VALUES (?, ?, ?, ?, ?, ?)",
                    (customer_id, product_name, quantity, customer_cpf, customer_address, payment_method))

        # Atualizar a quantidade do produto no banco de dados
        cur.execute("UPDATE product SET quantity = quantity - ? WHERE name = ?", (quantity, product_name))

        conn.commit()
        conn.close()
        flash('Venda cadastrada com sucesso!', 'success')

        return redirect(url_for('vendas'))
    else:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT c.name, c.email, s.product_name, s.quantity FROM customer c INNER JOIN sale s ON c.id = s.customer_id")
        vendas = cur.fetchall()
        cur.execute("SELECT name FROM product")
        products = [row[0] for row in cur.fetchall()]
        conn.close()
        return render_template('vendas.html', vendas=vendas, products=products)


if __name__ == '__main__':
    app.run(debug=True)
