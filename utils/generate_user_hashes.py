import bcrypt

def generate_hash(password):
    """Generate a bcrypt hash for a password."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# List of users and their passwords
users = [
    {"username": "Valeríya", "password": "Bw7$pQzX9tLm"},
    {"username": "Luis", "password": "K3r@NvD8sYfE"},
    {"username": "Joao", "password": "P9j$Tz5LqWxH"},
    {"username": "Humberto", "password": "G4h&FmV7cRpZ"},
    {"username": "Goncalo", "password": "X2s#Jb6QnDvA"},
    {"username": "Josue", "password": "M5t@Rz8PkLdS"},
    {"username": "Bruno", "password": "C7f$Qp3HjNxY"},
    {"username": "PauloP", "password": "V9g&Zk4TmBwJ"},
    {"username": "PauloR", "password": "L6h#Xd2RqFsP"},
    {"username": "Jose", "password": "T8j$Mn5VcKpZ"},
    {"username": "Ricardo", "password": "D3k@Qb7GxWfS"},
    {"username": "Antonio", "password": "N4m&Vp9JzTcR"},
    {"username": "Sodia", "password": "F6s#Hd3LqBxZ"},
    {"username": "Timoteo", "password": "R9t$Kp5MnVjW"},
    {"username": "Armando", "password": "H2v@Zf8QcPdG"},
    {"username": "Nelson", "password": "W7g&Jm4TzBsX"},
    {"username": "Tudor", "password": "S3k#Vb9NpRfD"},
    {"username": "Mika", "password": "Y5m$Qz7HjLcT"},
    {"username": "Lucas", "password": "B8p@Xd4GvWkS"},
    {"username": "Carla", "password": "J6r&Zn2TmFqP"},
]

if __name__ == "__main__":
    print("Generating hashes for all users...")
    print("\nYAML format for config.yaml:")
    print("credentials:")
    print("  usernames:")
    
    # Keep existing admin and usuario1 users
    print("    admin:")
    print("      email: admin@mdwallet.com")
    print("      name: Administrator")
    print("      password: $2b$12$a8w/xyRsQ6BgkTEMe6NiI.PrueBouT/NyYKXurFnGiGniXjYlM5Sy  # Password: admin123")
    print("    usuario1:")
    print("      email: user1@mdwallet.com")
    print("      name: Usuario 1")
    print("      password: $2b$12$mrWZdi0LGT5d/UCMPwsHMuO5V2IXuEYi1bBQkddJtT3prUiYOLQre  # Password: user123")
    
    # Add all new users
    for user in users:
        username = user["username"]
        password = user["password"]
        hashed = generate_hash(password)
        
        print(f"    {username}:")
        print(f"      email: {username.lower()}@mdwallet.com")
        print(f"      name: {username}")
        print(f"      password: {hashed}  # Password: {password}")
    
    print("\nVerifying hashes...")
    for user in users:
        username = user["username"]
        password = user["password"]
        hashed = generate_hash(password)
        verification = bcrypt.checkpw(password.encode(), hashed.encode())
        print(f"{username}: {verification}") 