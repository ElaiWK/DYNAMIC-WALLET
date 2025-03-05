import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def generate_password_hash(password):
    """Generate a password hash using bcrypt."""
    return stauth.Hasher([password]).generate()[0]

def add_user_to_config(username, name, email, password):
    """Add a new user to the config.yaml file."""
    # Load existing config
    config_path = 'data/config.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
    else:
        # Create default config if it doesn't exist
        config = {
            'credentials': {
                'usernames': {}
            },
            'cookie': {
                'expiry_days': 30,
                'key': 'md_wallet_some_signature_key',
                'name': 'md_wallet_cookie'
            },
            'preauthorized': {
                'emails': []
            }
        }
    
    # Generate password hash
    hashed_password = generate_password_hash(password)
    
    # Add user to config
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_password
    }
    
    # Save updated config
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    print(f"User '{username}' added successfully!")
    print(f"Password hash: {hashed_password}")

if __name__ == "__main__":
    print("=== MD Wallet User Generator ===")
    username = input("Enter username: ")
    name = input("Enter full name: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    
    add_user_to_config(username, name, email, password)
    
    # Create user directory
    user_dir = os.path.join('data', 'users', username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        print(f"Created user directory: {user_dir}") 