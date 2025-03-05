import bcrypt
import getpass

def hash_password():
    """Generate a hashed password for use in the config.yaml file."""
    password = getpass.getpass("Enter the password to hash: ")
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    
    # Return hashed password as string
    return hashed_password.decode()

if __name__ == "__main__":
    print("\nPassword Hash Generator for MD Wallet\n")
    print("This utility generates a hashed password to add to your config.yaml file.")
    
    try:
        hashed = hash_password()
        print("\nHashed Password (copy this to your config.yaml file):")
        print(hashed)
        print("\nExample config entry:")
        print("  username:")
        print("    email: user@example.com")
        print("    name: Example User")
        print(f"    password: {hashed}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    print("\nDone.") 