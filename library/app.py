from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load data
def load_data():
    data = {
        'books': [],
        'users': [],
        'memberships': [],
        'transactions': []
    }
    
    if os.path.exists('data/books.json'):
        with open('data/books.json', 'r') as f:
            data['books'] = json.load(f)
    if os.path.exists('data/users.json'):
        with open('data/users.json', 'r') as f:
            data['users'] = json.load(f)
    if os.path.exists('data/memberships.json'):
        with open('data/memberships.json', 'r') as f:
            data['memberships'] = json.load(f)
    if os.path.exists('data/transactions.json'):
        with open('data/transactions.json', 'r') as f:
            data['transactions'] = json.load(f)
    return data

# Save data
def save_data(data):
    with open('data/books.json', 'w') as f:
        json.dump(data['books'], f)
    with open('data/users.json', 'w') as f:
        json.dump(data['users'], f)
    with open('data/memberships.json', 'w') as f:
        json.dump(data['memberships'], f)
    with open('data/transactions.json', 'w') as f:
        json.dump(data['transactions'], f)

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    data = load_data()
    user = next((u for u in data['users'] if u['username'] == username and u['password'] == password), None)
    if user:
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('home'))

@app.route('/admin/dashboard')
def admin_dashboard():
    data = load_data()
    return render_template('admin_dashboard.html', books=data['books'], users=data['users'], memberships=data['memberships'])

@app.route('/user/dashboard')
def user_dashboard():
    data = load_data()
    return render_template('user_dashboard.html', books=data['books'])

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        type = request.form.get('type', 'book')
        book = {'title': title, 'author': author, 'isbn': isbn, 'type': type, 'available': True}
        data = load_data()
        data['books'].append(book)
        save_data(data)
        flash('Book added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_book.html')

@app.route('/update_book/<isbn>', methods=['GET', 'POST'])
def update_book(isbn):
    data = load_data()
    book = next((b for b in data['books'] if b['isbn'] == isbn), None)
    if request.method == 'POST':
        book['title'] = request.form['title']
        book['author'] = request.form['author']
        book['type'] = request.form.get('type', 'book')
        save_data(data)
        flash('Book updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('update_book.html', book=book)

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        user_id = request.form['user_id']
        issue_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S')
        transaction = {'book_isbn': isbn, 'user_id': user_id, 'issue_date': issue_date, 'return_date': return_date, 'fine': 0}
        data = load_data()
        data['transactions'].append(transaction)
        for book in data['books']:
            if book['isbn'] == isbn:
                book['available'] = False
        save_data(data)
        flash('Book issued successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    data = load_data()
    return render_template('issue_book.html', books=data['books'])

@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        user_id = request.form['user_id']
        data = load_data()
        for transaction in data['transactions']:
            if transaction['book_isbn'] == isbn and transaction['user_id'] == user_id and not transaction.get('return_date'):
                transaction['return_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                fine = calculate_fine(transaction)
                if fine > 0:
                    flash(f'Fine to be paid: {fine}', 'warning')
                else:
                    flash('No fine to be paid.', 'success')
                for book in data['books']:
                    if book['isbn'] == isbn:
                        book['available'] = True
                save_data(data)
                flash('Book returned successfully!', 'success')
                return redirect(url_for('pay_fine', isbn=isbn, user_id=user_id))
        flash('Book not found or already returned!', 'error')
    data = load_data()
    return render_template('return_book.html', books=data['books'])

def calculate_fine(transaction):
    return_date = datetime.strptime(transaction['return_date'], '%Y-%m-%d %H:%M:%S')
    due_date = datetime.strptime(transaction['issue_date'], '%Y-%m-%d %H:%M:%S') + timedelta(days=15)
    if return_date > due_date:
        return (return_date - due_date).days * 1  # $1 per day fine
    return 0

@app.route('/pay_fine/<isbn>/<user_id>', methods=['GET', 'POST'])
def pay_fine(isbn, user_id):
    data = load_data()
    transaction = next((t for t in data['transactions'] if t['book_isbn'] == isbn and t['user_id'] == user_id), None)
    if request.method == 'POST':
        if transaction:
            fine = calculate_fine(transaction)
            if fine > 0:
                transaction['fine'] = fine
                save_data(data)
                flash('Fine paid successfully!', 'success')
            else:
                flash('No fine to be paid.', 'success')
            return redirect(url_for('user_dashboard'))
    return render_template('pay_fine.html', transaction=transaction)

@app.route('/add_membership', methods=['GET', 'POST'])
def add_membership():
    if request.method == 'POST':
        user_id = request.form['user_id']
        duration = request.form.get('duration', '6 months')
        start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_date = (datetime.now() + timedelta(days=180 if duration == '6 months' else 365 if duration == '1 year' else 730)).strftime('%Y-%m-%d %H:%M:%S')
        membership = {'user_id': user_id, 'duration': duration, 'start_date': start_date, 'end_date': end_date}
        data = load_data()
        data['memberships'].append(membership)
        save_data(data)
        flash('Membership added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_membership.html')

@app.route('/update_membership/<user_id>', methods=['GET', 'POST'])
def update_membership(user_id):
    data = load_data()
    membership = next((m for m in data['memberships'] if m['user_id'] == user_id), None)
    if request.method == 'POST':
        membership['duration'] = request.form.get('duration', '6 months')
        membership['end_date'] = (datetime.strptime(membership['start_date'], '%Y-%m-%d %H:%M:%S') + timedelta(days=180 if membership['duration'] == '6 months' else 365 if membership['duration'] == '1 year' else 730)).strftime('%Y-%m-%d %H:%M:%S')
        save_data(data)
        flash('Membership updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('update_membership.html', membership=membership)

@app.route('/manage_user', methods=['GET', 'POST'])
def manage_user():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form.get('role', 'user')
        data = load_data()
        for user in data['users']:
            if user['username'] == username:
                user['role'] = role
                save_data(data)
                flash('User role updated successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
        flash('User not found!', 'error')
    data = load_data()
    return render_template('manage_user.html', users=data['users'])

@app.route('/search_book', methods=['GET', 'POST'])
def search_book():
    if request.method == 'POST':
        search_term = request.form['search_term']
        data = load_data()
        results = [b for b in data['books'] if search_term.lower() in b['title'].lower() or search_term.lower() in b['author'].lower() or search_term == b['isbn']]
        return render_template('search_book.html', results=results)
    return render_template('search_book.html')

if __name__ == '__main__':
    app.run(debug=True)