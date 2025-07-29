# session.py
current_user = {
    "username": None,
    "role": None
}

def set_user(username, role):
    current_user["username"] = username
    current_user["role"] = role

def get_user():
    return current_user
