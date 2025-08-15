from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

# MySQL configuration, change it accordingly
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change this to your MySQL password
    'database': 'budget_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash('Username already exists.')
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM budgets WHERE user_id = %s', (user_id,))
    budgets = cursor.fetchall()
    cursor.execute('''SELECT t.*, b.name as budget_name FROM transactions t
                      JOIN budgets b ON t.budget_id = b.id
                      WHERE b.user_id = %s ORDER BY t.date DESC''', (user_id,))
    transactions = cursor.fetchall()
    # Summary calculations
    total_budget = sum(b['amount'] for b in budgets)
    total_spent = sum(t['amount'] for t in transactions)
    remaining = total_budget - total_spent
    # For filtering
    budget_options = [{'id': b['id'], 'name': b['name']} for b in budgets]
    cursor.close()
    conn.close()
    return render_template('dashboard.html', username=session['username'], budgets=budgets, transactions=transactions, total_budget=total_budget, total_spent=total_spent, remaining=remaining, budget_options=budget_options)

@app.route('/add_budget', methods=['POST'])
def add_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    amount = request.form['amount']
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO budgets (user_id, name, amount) VALUES (%s, %s, %s)', (user_id, name, amount))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Budget added!')
    return redirect(url_for('dashboard'))

@app.route('/delete_budget', methods=['POST'])
def delete_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    budget_id = request.form['budget_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM budgets WHERE id = %s AND user_id = %s', (budget_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Budget deleted!')
    return redirect(url_for('dashboard'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    description = request.form['description']
    amount = request.form['amount']
    budget_id = request.form['budget_id']
    txn_date = date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO transactions (budget_id, description, amount, date) VALUES (%s, %s, %s, %s)''', (budget_id, description, amount, txn_date))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Transaction added!')
    return redirect(url_for('dashboard'))

@app.route('/delete_transaction', methods=['POST'])
def delete_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transaction_id = request.form['transaction_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE t FROM transactions t
                      JOIN budgets b ON t.budget_id = b.id
                      WHERE t.id = %s AND b.user_id = %s''', (transaction_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Transaction deleted!')
    return redirect(url_for('dashboard'))

@app.route('/edit_budget', methods=['POST'])
def edit_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    budget_id = request.form['budget_id']
    name = request.form['name']
    amount = request.form['amount']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE budgets SET name = %s, amount = %s WHERE id = %s AND user_id = %s', (name, amount, budget_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Budget updated!')
    return redirect(url_for('dashboard'))

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transaction_id = request.form['transaction_id']
    description = request.form['description']
    amount = request.form['amount']
    txn_date = request.form['date']
    budget_id = request.form['budget_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE transactions t
                      JOIN budgets b ON t.budget_id = b.id
                      SET t.description = %s, t.amount = %s, t.date = %s, t.budget_id = %s
                      WHERE t.id = %s AND b.user_id = %s''', (description, amount, txn_date, budget_id, transaction_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Transaction updated!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':

    app.run(debug=True) 
