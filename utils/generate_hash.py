import bcrypt

def generate_hash(password):
    """Generate a bcrypt hash for a password."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    # Generate hashes for our test passwords
    admin_hash = generate_hash("admin123")
    user_hash = generate_hash("user123")
    
    print(f"Admin hash: {admin_hash}")
    print(f"User hash: {user_hash}")
    
    # Verify the hashes work
    print("\nVerifying hashes:")
    print(f"Admin verification: {bcrypt.checkpw('admin123'.encode(), admin_hash.encode())}")
    print(f"User verification: {bcrypt.checkpw('user123'.encode(), user_hash.encode())}") 