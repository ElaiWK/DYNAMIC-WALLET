import os
import json
import hashlib
import sys

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    """Create a new users.json file with default users"""
    # Determine the right path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    users_file = os.path.join(data_dir, "users.json")
    
    # Create default users with simplified passwords
    default_users = {
        "Humberto": {"password": hash_password("test123"), "created_at": "2023-09-01 12:00:00"},
        "admin": {"password": hash_password("admin123"), "created_at": "2023-09-01 12:00:00", "is_admin": True}
    }
    
    # Write to file
    with open(users_file, 'w') as f:
        json.dump(default_users, f, indent=2)
    
    print(f"Created users file at: {users_file}")
    
    # Also create the users directory structure that the app is looking for
    users_dir = os.path.join(data_dir, "users")
    os.makedirs(users_dir, exist_ok=True)
    
    # Create directories for each user
    for username in default_users.keys():
        user_dir = os.path.join(users_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        print(f"Created user directory: {user_dir}")
    
    print(f"Users: {', '.join(default_users.keys())}")
    print("You can now log in with:")
    print("Username: admin, Password: admin123")
    print("Username: Humberto, Password: test123")

if __name__ == "__main__":
    main() 