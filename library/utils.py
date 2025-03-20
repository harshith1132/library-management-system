import json

def load_data():
    try:
        with open('data/books.json', 'r') as f:
            books = json.load(f)
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        with open('data/memberships.json', 'r') as f:
            memberships = json.load(f)
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
        return {
            'books': books,
            'users': users,
            'memberships': memberships,
            'transactions': transactions
        }
    except FileNotFoundError:
        return {
            'books': [],
            'users': [],
            'memberships': [],
            'transactions': []
        }

def save_data(data):
    with open('data/books.json', 'w') as f:
        json.dump(data['books'], f)
    with open('data/users.json', 'w') as f:
        json.dump(data['users'], f)
    with open('data/memberships.json', 'w') as f:
        json.dump(data['memberships'], f)
    with open('data/transactions.json', 'w') as f:
        json.dump(data['transactions'], f)