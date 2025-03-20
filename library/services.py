from project.models import *
from datetime import datetime, timedelta

def authenticate_user(users, username, password):
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

def add_book(books):
    title = input("Enter book title: ")
    author = input("Enter author name: ")
    isbn = input("Enter ISBN: ")
    type = input("Enter type (book/movie): ") or 'book'
    book = Book(title, author, isbn, type)
    books.append(book.__dict__)
    print("Book added successfully!")

def update_book(books):
    isbn = input("Enter ISBN of the book to update: ")
    for book in books:
        if book['isbn'] == isbn:
            book['title'] = input("Enter new title: ")
            book['author'] = input("Enter new author: ")
            book['type'] = input("Enter new type (book/movie): ") or 'book'
            print("Book updated successfully!")
            return
    print("Book not found!")

def add_membership(memberships):
    user_id = input("Enter user ID: ")
    duration = input("Enter duration (6 months, 1 year, 2 years): ") or '6 months'
    membership = Membership(user_id, duration)
    memberships.append(membership.__dict__)
    print("Membership added successfully!")

def update_membership(memberships):
    user_id = input("Enter user ID: ")
    for membership in memberships:
        if membership['user_id'] == user_id:
            membership['duration'] = input("Enter new duration (6 months, 1 year, 2 years): ") or '6 months'
            membership['end_date'] = Membership(user_id, membership['duration']).calculate_end_date()
            print("Membership updated successfully!")
            return
    print("Membership not found!")

def manage_user(users):
    username = input("Enter username: ")
    for user in users:
        if user['username'] == username:
            user['role'] = input("Enter new role (admin/user): ") or 'user'
            print("User role updated successfully!")
            return
    print("User not found!")

def search_book(books):
    search_term = input("Enter search term (title/author/isbn): ")
    for book in books:
        if search_term.lower() in book['title'].lower() or search_term.lower() in book['author'].lower() or search_term == book['isbn']:
            print(f"Title: {book['title']}, Author: {book['author']}, ISBN: {book['isbn']}, Available: {book['available']}")

def issue_book(data):
    isbn = input("Enter ISBN of the book to issue: ")
    user_id = input("Enter your user ID: ")
    for book in data['books']:
        if book['isbn'] == isbn and book['available']:
            issue_date = datetime.now()
            return_date = issue_date + timedelta(days=15)
            transaction = Transaction(isbn, user_id, issue_date, return_date)
            data['transactions'].append(transaction.__dict__)
            book['available'] = False
            print("Book issued successfully!")
            return
    print("Book not available or not found!")

def return_book(data):
    isbn = input("Enter ISBN of the book to return: ")
    user_id = input("Enter your user ID: ")
    for transaction in data['transactions']:
        if transaction['book_isbn'] == isbn and transaction['user_id'] == user_id and not transaction['return_date']:
            transaction['return_date'] = datetime.now()
            fine = calculate_fine(transaction)
            if fine > 0:
                print(f"Fine to be paid: {fine}")
            else:
                print("No fine to be paid.")
            for book in data['books']:
                if book['isbn'] == isbn:
                    book['available'] = True
                    print("Book returned successfully!")
                    return
    print("Book not found or already returned!")

def calculate_fine(transaction):
    return_date = datetime.strptime(transaction['return_date'], "%Y-%m-%d %H:%M:%S")
    due_date = datetime.strptime(transaction['issue_date'], "%Y-%m-%d %H:%M:%S") + timedelta(days=15)
    if return_date > due_date:
        return (return_date - due_date).days * 1  # $1 per day fine
    return 0

def pay_fine(data):
    isbn = input("Enter ISBN of the book: ")
    user_id = input("Enter your user ID: ")
    for transaction in data['transactions']:
        if transaction['book_isbn'] == isbn and transaction['user_id'] == user_id:
            fine = calculate_fine(transaction)
            if fine > 0:
                print(f"Fine to be paid: {fine}")
                paid = input("Pay fine? (yes/no): ")
                if paid.lower() == 'yes':
                    transaction['fine'] = fine
                    print("Fine paid successfully!")
                    return
            else:
                print("No fine to be paid.")
                return
    print("Transaction not found!")

def generate_reports(data):
    print("Generating reports...")
    # Implement report generation logic here

def handle_transactions(data):
    print("Handling transactions...")
    # Implement transaction handling logic here