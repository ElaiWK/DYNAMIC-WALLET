import os
import json
import hashlib
import sys

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against a provided password"""
    hashed = hash_password(provided_password)
    print(f"Stored password hash: {stored_password}")
    print(f"Provided password hash: {hashed}")
    return stored_password == hashed

def get_users_file_path():
    """Get the path to the users.json file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, "data")
    users_file = os.path.join(data_dir, "users.json")
    print(f"Looking for users file at: {users_file}")
    return users_file

def load_users():
    """Load users from the JSON file"""
    users_file = get_users_file_path()
    
    if os.path.exists(users_file):
        try:
            with open(users_file, "r") as f:
                users = json.load(f)
            print(f"Successfully loaded {len(users)} users")
            return users
        except Exception as e:
            print(f"Error loading users file: {str(e)}")
            return {}
    else:
        print(f"Users file not found at {users_file}")
        return {}

def test_auth(username, password):
    """Test authentication for a username and password"""
    users = load_users()
    
    if not users:
        print("No users found, authentication not possible")
        return False
    
    if username not in users:
        print(f"User '{username}' not found")
        return False
    
    result = verify_password(users[username]["password"], password)
    print(f"Password verification result: {result}")
    return result

def main():
    """Test authentication for default users"""
    print("Testing authentication...")
    
    test_auth("admin", "admin123")
    print("-" * 40)
    test_auth("Humberto", "test123")
    print("-" * 40)
    
    # Let user test custom credentials
    username = input("Enter username to test: ")
    password = input("Enter password to test: ")
    test_auth(username, password)

if __name__ == "__main__":
    main() 