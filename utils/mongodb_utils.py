import os
import json
from pymongo import MongoClient
from datetime import datetime
import streamlit as st

# MongoDB connection string - replace with your own when you set up MongoDB Atlas
# This is a placeholder - you'll need to replace it with your actual connection string
MONGO_URI = "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority"

# For local development, you can use environment variables or Streamlit secrets
def get_mongo_uri():
    # First check if it's defined in Streamlit secrets (for Streamlit Cloud)
    if hasattr(st, "secrets") and "mongo" in st.secrets:
        return st.secrets["mongo"]["uri"]
    # Then check environment variables (for local development)
    elif "MONGO_URI" in os.environ:
        return os.environ["MONGO_URI"]
    # Finally, fall back to the hardcoded URI (not recommended for production)
    else:
        return MONGO_URI

def get_database():
    """Get a connection to the MongoDB database."""
    try:
        client = MongoClient(get_mongo_uri())
        return client.dynamic_wallet_db
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        # Fall back to local storage if MongoDB connection fails
        return None

# User data operations
def save_user_transactions_to_db(username, transactions):
    """Save user transactions to MongoDB."""
    db = get_database()
    if db is None:
        return False
    
    try:
        # Convert datetime objects to strings for MongoDB storage
        processed_transactions = []
        for transaction in transactions:
            processed_transaction = transaction.copy()
            if isinstance(transaction.get("Date"), datetime):
                processed_transaction["Date"] = transaction["Date"].strftime("%Y-%m-%d")
            processed_transactions.append(processed_transaction)
        
        # Update or insert user's transactions
        db.users.update_one(
            {"username": username},
            {"$set": {"transactions": processed_transactions, "last_updated": datetime.now()}},
            upsert=True
        )
        return True
    except Exception as e:
        st.error(f"Failed to save transactions to MongoDB: {e}")
        return False

def load_user_transactions_from_db(username):
    """Load user transactions from MongoDB."""
    db = get_database()
    if db is None:
        return []
    
    try:
        user_data = db.users.find_one({"username": username})
        if user_data and "transactions" in user_data:
            # Convert date strings back to datetime objects
            transactions = user_data["transactions"]
            for transaction in transactions:
                if isinstance(transaction.get("Date"), str):
                    try:
                        transaction["Date"] = datetime.strptime(transaction["Date"], "%Y-%m-%d")
                    except ValueError:
                        pass  # Keep as string if parsing fails
            return transactions
        return []
    except Exception as e:
        st.error(f"Failed to load transactions from MongoDB: {e}")
        return []

def save_user_history_to_db(username, history):
    """Save user history to MongoDB."""
    db = get_database()
    if db is None:
        return False
    
    try:
        db.users.update_one(
            {"username": username},
            {"$set": {"history": history, "last_updated": datetime.now()}},
            upsert=True
        )
        return True
    except Exception as e:
        st.error(f"Failed to save history to MongoDB: {e}")
        return False

def load_user_history_from_db(username):
    """Load user history from MongoDB."""
    db = get_database()
    if db is None:
        return []
    
    try:
        user_data = db.users.find_one({"username": username})
        if user_data and "history" in user_data:
            return user_data["history"]
        return []
    except Exception as e:
        st.error(f"Failed to load history from MongoDB: {e}")
        return []

def save_user_settings_to_db(username, settings):
    """Save user settings to MongoDB."""
    db = get_database()
    if db is None:
        return False
    
    try:
        # Convert datetime objects to strings for MongoDB storage
        processed_settings = {}
        for key, value in settings.items():
            if isinstance(value, datetime):
                processed_settings[key] = value.strftime("%Y-%m-%d")
            else:
                processed_settings[key] = value
        
        db.users.update_one(
            {"username": username},
            {"$set": {"settings": processed_settings, "last_updated": datetime.now()}},
            upsert=True
        )
        return True
    except Exception as e:
        st.error(f"Failed to save settings to MongoDB: {e}")
        return False

def load_user_settings_from_db(username):
    """Load user settings from MongoDB."""
    db = get_database()
    if db is None:
        return {}
    
    try:
        user_data = db.users.find_one({"username": username})
        if user_data and "settings" in user_data:
            # Convert date strings back to datetime objects
            settings = user_data["settings"]
            for key, value in settings.items():
                if isinstance(value, str) and key.endswith("_date"):
                    try:
                        settings[key] = datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        pass  # Keep as string if parsing fails
            return settings
        return {}
    except Exception as e:
        st.error(f"Failed to load settings from MongoDB: {e}")
        return {}

# Fallback to local storage if MongoDB is not available
def save_to_local_fallback(username, data_type, data):
    """Save data to local storage as fallback."""
    directory = f"data/users/{username}"
    os.makedirs(directory, exist_ok=True)
    
    filename = f"{directory}/{data_type}.json"
    try:
        # Convert datetime objects to strings
        if isinstance(data, list):
            processed_data = []
            for item in data:
                if isinstance(item, dict):
                    processed_item = {}
                    for k, v in item.items():
                        if isinstance(v, datetime):
                            processed_item[k] = v.strftime("%Y-%m-%d")
                        else:
                            processed_item[k] = v
                    processed_data.append(processed_item)
                else:
                    processed_data.append(item)
            data = processed_data
        elif isinstance(data, dict):
            processed_data = {}
            for k, v in data.items():
                if isinstance(v, datetime):
                    processed_data[k] = v.strftime("%Y-%m-%d")
                else:
                    processed_data[k] = v
            data = processed_data
            
        with open(filename, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        st.error(f"Failed to save to local storage: {e}")
        return False

def load_from_local_fallback(username, data_type):
    """Load data from local storage as fallback."""
    filename = f"data/users/{username}/{data_type}.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Convert date strings back to datetime objects
            if data_type == "transactions" and isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "Date" in item and isinstance(item["Date"], str):
                        try:
                            item["Date"] = datetime.strptime(item["Date"], "%Y-%m-%d")
                        except ValueError:
                            pass  # Keep as string if parsing fails
            elif data_type == "settings" and isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and key.endswith("_date"):
                        try:
                            data[key] = datetime.strptime(value, "%Y-%m-%d")
                        except ValueError:
                            pass  # Keep as string if parsing fails
                            
            return data
        return [] if data_type in ["transactions", "history"] else {}
    except Exception as e:
        st.error(f"Failed to load from local storage: {e}")
        return [] if data_type in ["transactions", "history"] else {} 