import json
import os
import hashlib

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_users_file_path():
    """Get the path to the users.json file"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    return os.path.join(data_dir, "users.json")

def change_password(username, new_password):
    """Change the password for a specific user"""
    users_file = get_users_file_path()
    
    # Load current users
    with open(users_file, "r") as f:
        users = json.load(f)
    
    # Check if user exists
    if username not in users:
        print(f"User {username} not found!")
        return False
    
    # Update password
    users[username]["password"] = hash_password(new_password)
    
    # Save updated users
    with open(users_file, "w") as f:
        json.dump(users, f, indent=4)
    
    print(f"Password for user {username} has been updated to {new_password}")
    return True

if __name__ == "__main__":
    # Change password for Luis to 1234
    change_password("Luis", "1234") 