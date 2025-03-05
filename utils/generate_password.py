import bcrypt
import yaml
from yaml.loader import SafeLoader
from yaml.dumper import SafeDumper
import os

def hash_password(password):
    """Generate a hashed version of the password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def add_user(username, password, name, email):
    """Add a new user to the config file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.yaml')
    
    # Load existing config
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Add new user
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hash_password(password)
    }
    
    # Save updated config
    with open(config_path, 'w') as file:
        yaml.dump(config, file, Dumper=SafeDumper)
    
    print(f"User '{username}' added successfully!")

if __name__ == "__main__":
    print("MD Wallet - User Management")
    print("-" * 30)
    
    username = input("Username: ")
    password = input("Password: ")
    name = input("Full Name: ")
    email = input("Email: ")
    
    add_user(username, password, name, email) 