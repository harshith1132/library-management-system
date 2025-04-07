from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database initialization
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  name TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  author TEXT NOT NULL,
                  isbn TEXT UNIQUE NOT NULL,
                  type TEXT NOT NULL,
                  available BOOLEAN DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT NOT NULL,
                  address TEXT NOT NULL,
                  membership_type TEXT NOT NULL,
                  start_date TEXT NOT NULL,
                  end_date TEXT NOT NULL,
                  active BOOLEAN DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  book_id INTEGER NOT NULL,
                  member_id INTEGER NOT NULL,
                  issue_date TEXT NOT NULL,
                  due_date TEXT NOT NULL,
                  return_date TEXT,
                  fine REAL DEFAULT 0,
                  fine_paid BOOLEAN DEFAULT 0,
                  remarks TEXT,
                  FOREIGN KEY(book_id) REFERENCES books(id),
                  FOREIGN KEY(member_id) REFERENCES members(id))''')
    
    # Create admin user if not exists
    try:
        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                  ('admin', generate_password_hash('admin'), 'admin', 'Administrator'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_fine(due_date, return_date):
    due = datetime.strptime(due_date, '%Y-%m-%d')
    returned = datetime.strptime(return_date, '%Y-%m-%d')
    if returned > due:
        days_overdue = (returned - due).days
        return days_overdue * 10  # $10 per day fine
    return 0

# Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Dashboard
@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', role=session['role'])

# Book Management
@app.route('/books/search', methods=['GET', 'POST'])
def search_books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        search_by = request.form.get('search_by', 'title')
        
        if not search_term:
            flash('Please enter a search term', 'danger')
            return render_template('search_books.html')
        
        conn = get_db_connection()
        if search_by == 'title':
            books = conn.execute('SELECT * FROM books WHERE title LIKE ? AND available = 1', 
                                (f'%{search_term}%',)).fetchall()
        else:
            books = conn.execute('SELECT * FROM books WHERE author LIKE ? AND available = 1', 
                                (f'%{search_term}%',)).fetchall()
        conn.close()
        
        return render_template('search_books.html', books=books, search_term=search_term, search_by=search_by)
    
    return render_template('search_books.html')

@app.route('/books/issue', methods=['GET', 'POST'])
def issue_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        member_id = request.form.get('member_id')
        issue_date = request.form.get('issue_date')
        due_date = request.form.get('due_date')
        remarks = request.form.get('remarks', '')
        
        if not all([book_id, member_id, issue_date, due_date]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('issue_book'))
        
        conn = get_db_connection()
        
        # Check if book is available
        book = conn.execute('SELECT * FROM books WHERE id = ? AND available = 1', (book_id,)).fetchone()
        if not book:
            flash('Selected book is not available', 'danger')
            conn.close()
            return redirect(url_for('issue_book'))
        
        # Check if member exists
        member = conn.execute('SELECT * FROM members WHERE id = ? AND active = 1', (member_id,)).fetchone()
        if not member:
            flash('Invalid member ID', 'danger')
            conn.close()
            return redirect(url_for('issue_book'))
        
        # Create transaction
        conn.execute('INSERT INTO transactions (book_id, member_id, issue_date, due_date, remarks) VALUES (?, ?, ?, ?, ?)',
                    (book_id, member_id, issue_date, due_date, remarks))
        
        # Update book availability
        conn.execute('UPDATE books SET available = 0 WHERE id = ?', (book_id,))
        
        conn.commit()
        conn.close()
        
        flash('Book issued successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('issue_book.html', today=datetime.now().strftime('%Y-%m-%d'),
                         default_due=(datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'))

@app.route('/books/return', methods=['GET', 'POST'])
def return_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        return_date = request.form.get('return_date')
        
        if not all([transaction_id, return_date]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('return_book'))
        
        conn = get_db_connection()
        
        # Get transaction details
        transaction = conn.execute('SELECT * FROM transactions WHERE id = ? AND return_date IS NULL', 
                                 (transaction_id,)).fetchone()
        if not transaction:
            flash('Invalid transaction ID', 'danger')
            conn.close()
            return redirect(url_for('return_book'))
        
        # Calculate fine
        fine = calculate_fine(transaction['due_date'], return_date)
        
        # Update transaction
        conn.execute('UPDATE transactions SET return_date = ?, fine = ? WHERE id = ?',
                    (return_date, fine, transaction_id))
        
        # Update book availability
        conn.execute('UPDATE books SET available = 1 WHERE id = ?', (transaction['book_id'],))
        
        conn.commit()
        conn.close()
        
        flash('Book returned successfully', 'success')
        return redirect(url_for('pay_fine', transaction_id=transaction_id))
    
    return render_template('return_book.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/books/pay_fine/<int:transaction_id>', methods=['GET', 'POST'])
def pay_fine(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    
    if request.method == 'POST':
        fine_paid = request.form.get('fine_paid') == 'on'
        remarks = request.form.get('remarks', '')
        
        if transaction['fine'] > 0 and not fine_paid:
            flash('Please pay the fine to complete the transaction', 'danger')
            conn.close()
            return render_template('pay_fine.html', transaction=transaction)
        
        conn.execute('UPDATE transactions SET fine_paid = ?, remarks = ? WHERE id = ?',
                    (1 if fine_paid else 0, remarks, transaction_id))
        conn.commit()
        conn.close()
        
        flash('Transaction completed successfully', 'success')
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('pay_fine.html', transaction=transaction)

# Membership Management
@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        membership_type = request.form['membership_type']
        
        if not all([name, email, phone, address, membership_type]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('add_member'))
        
        start_date = datetime.now().strftime('%Y-%m-%d')
        if membership_type == '1_year':
            end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        elif membership_type == '2_years':
            end_date = (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d')
        else:  # 6 months
            end_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO members (name, email, phone, address, membership_type, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (name, email, phone, address, membership_type, start_date, end_date))
            conn.commit()
            flash('Member added successfully', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('add_member.html')

@app.route('/members/update', methods=['GET', 'POST'])
def update_member():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        member_id = request.form['member_id']
        action = request.form['action']
        
        if not member_id:
            flash('Please enter a member ID', 'danger')
            return redirect(url_for('update_member'))
        
        conn = get_db_connection()
        member = conn.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
        
        if not member:
            flash('Member not found', 'danger')
            conn.close()
            return redirect(url_for('update_member'))
        
        if action == 'extend':
            extension = request.form['extension']
            current_end = datetime.strptime(member['end_date'], '%Y-%m-%d')
            
            if extension == '1_year':
                new_end = current_end + timedelta(days=365)
            elif extension == '2_years':
                new_end = current_end + timedelta(days=730)
            else:  # 6 months
                new_end = current_end + timedelta(days=180)
            
            conn.execute('UPDATE members SET end_date = ? WHERE id = ?',
                        (new_end.strftime('%Y-%m-%d'), member_id))
            flash('Membership extended successfully', 'success')
        elif action == 'cancel':
            conn.execute('UPDATE members SET active = 0 WHERE id = ?', (member_id,))
            flash('Membership cancelled successfully', 'success')
        
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    return render_template('update_member.html')

# Admin functions
@app.route('/admin/books/add', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        type = request.form['type']
        
        if not all([title, author, isbn, type]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('add_book'))
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO books (title, author, isbn, type) VALUES (?, ?, ?, ?)',
                        (title, author, isbn, type))
            conn.commit()
            flash('Book added successfully', 'success')
        except sqlite3.IntegrityError:
            flash('ISBN already exists', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('add_book.html')

@app.route('/admin/books/update', methods=['GET', 'POST'])
def update_book():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        book_id = request.form['book_id']
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        type = request.form['type']
        available = request.form.get('available', 'off') == 'on'
        
        if not all([book_id, title, author, isbn, type]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('update_book'))
        
        conn = get_db_connection()
        conn.execute('UPDATE books SET title = ?, author = ?, isbn = ?, type = ?, available = ? WHERE id = ?',
                    (title, author, isbn, type, 1 if available else 0, book_id))
        conn.commit()
        conn.close()
        
        flash('Book updated successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('update_book.html')

@app.route('/admin/users/manage', methods=['GET', 'POST'])
def manage_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form['action']
        username = request.form['username']
        name = request.form['name']
        
        if not name:
            flash('Name is required', 'danger')
            return redirect(url_for('manage_users'))
        
        conn = get_db_connection()
        
        if action == 'new':
            password = request.form['password']
            role = request.form['role']
            
            if not password:
                flash('Password is required', 'danger')
                conn.close()
                return redirect(url_for('manage_users'))
            
            try:
                conn.execute('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)',
                            (username, generate_password_hash(password), role, name))
                conn.commit()
                flash('User added successfully', 'success')
            except sqlite3.IntegrityError:
                flash('Username already exists', 'danger')
        else:  # existing
            user_id = request.form['user_id']
            conn.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
            conn.commit()
            flash('User updated successfully', 'success')
        
        conn.close()
        return redirect(url_for('dashboard'))
    
    return render_template('manage_users.html')

# Reports
@app.route('/reports/books')
def book_reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('book_reports.html', books=books)

@app.route('/reports/transactions')
def transaction_reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    transactions = conn.execute('''SELECT t.*, b.title as book_title, m.name as member_name 
                                 FROM transactions t
                                 JOIN books b ON t.book_id = b.id
                                 JOIN members m ON t.member_id = m.id''').fetchall()
    conn.close()
    return render_template('transaction_reports.html', transactions=transactions)

@app.route('/reports/members')
def member_reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    return render_template('member_reports.html', members=members)

if __name__ == '__main__':
    app.run(debug=True)