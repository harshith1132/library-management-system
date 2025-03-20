from datetime import datetime, timedelta

class Book:
    def __init__(self, title, author, isbn, type='book'):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.type = type
        self.available = True

class User:
    def __init__(self, username, password, role='user'):
        self.username = username
        self.password = password
        self.role = role

class Membership:
    def __init__(self, user_id, duration='6 months', start_date=datetime.now()):
        self.user_id = user_id
        self.duration = duration
        self.start_date = start_date
        self.end_date = self.calculate_end_date()

    def calculate_end_date(self):
        if self.duration == '6 months':
            return self.start_date + timedelta(days=180)
        elif self.duration == '1 year':
            return self.start_date + timedelta(days=365)
        elif self.duration == '2 years':
            return self.start_date + timedelta(days=730)

class Transaction:
    def __init__(self, book_isbn, user_id, issue_date, return_date=None, fine=0):
        self.book_isbn = book_isbn
        self.user_id = user_id
        self.issue_date = issue_date
        self.return_date = return_date
        self.fine = fine