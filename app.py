from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="codtech", port=3306)
cursor = conn.cursor()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    cursor.execute("SELECT * FROM amazon_products")
    books = cursor.fetchall()
    return render_template('index.html', books=books)

@app.route('/storefronts')
def storefronts():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    return render_template('storefronts.html')

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    cursor.execute("SELECT id, product_asin, name, price, quantity, image_url FROM cart")
    cart_items = cursor.fetchall()
    total_price = sum(item[3] * item[4] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    user_id = session['user_id']
    cursor.execute("SELECT name, email, phone FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    return render_template('profile.html', user=user)

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    cursor.execute("SELECT email, phone FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    return render_template('settings.html', user=user)

@app.route('/update-settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']

    cursor.execute("UPDATE users SET email = %s, phone = %s WHERE id = %s", (email, phone, user_id))
    if password:
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (password, user_id))

    conn.commit()
    return redirect(url_for('profile'))

@app.route('/product-details/<asin>')
def product_details(asin):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    cursor.execute("SELECT * FROM amazon_products WHERE asin = %s", (asin,))
    product = cursor.fetchone()
    return render_template('product-details.html', product=product)

@app.route('/add-to-cart/<asin>', methods=['POST'])
def add_to_cart(asin):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    cursor.execute("SELECT name, price, img_source FROM amazon_products WHERE asin = %s", (asin,))
    product = cursor.fetchone()
    name, price, image_url = product
    cursor.execute("INSERT INTO cart (product_asin, name, price, image_url, quantity) VALUES (%s, %s, %s, %s, %s)", (asin, name, price, image_url, 1))
    conn.commit()
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    conn.commit()
    return redirect(url_for('cart'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'login':
            email = request.form['email']
            password = request.form['password']
            cursor.execute("SELECT id FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('index'))
        elif action == 'signup':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            phone = request.form['phone']
            cursor.execute("INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)", 
                    (name, email, password, phone))
            conn.commit()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            session['user_id'] = user[0]
            return redirect(url_for('index'))
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth'))

@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    query = request.args.get('query')
    cursor.execute("""
        SELECT * FROM amazon_products 
        WHERE name LIKE %s OR category_1 LIKE %s OR category_2 LIKE %s OR category_3 LIKE %s OR primary_category LIKE %s
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    return render_template('search_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)