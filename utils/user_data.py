import os
import json
import pandas as pd
from datetime import datetime

# Define path to user data folder
USER_DATA_DIR = 'data/users'

def ensure_user_directory(username):
    """Ensure the user's data directory exists."""
    user_dir = os.path.join(USER_DATA_DIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def save_user_transactions(username, transactions):
    """Save a user's transactions to their data file."""
    user_dir = ensure_user_directory(username)
    file_path = os.path.join(user_dir, 'transactions.json')
    
    with open(file_path, 'w') as f:
        json.dump(transactions, f, indent=2)

def load_user_transactions(username):
    """Load a user's transactions from their data file."""
    user_dir = ensure_user_directory(username)
    file_path = os.path.join(user_dir, 'transactions.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        return []

def save_user_history(username, history):
    """Save a user's report history to their data file."""
    user_dir = ensure_user_directory(username)
    file_path = os.path.join(user_dir, 'history.json')
    
    # Convert datetime objects to strings for JSON serialization
    serializable_history = []
    for report in history:
        # Create a copy of the report to avoid modifying the original
        report_copy = report.copy()
        
        # Convert date objects to strings
        if 'start_date' in report_copy and isinstance(report_copy['start_date'], datetime.date.__class__):
            report_copy['start_date'] = report_copy['start_date'].strftime('%Y-%m-%d')
        if 'end_date' in report_copy and isinstance(report_copy['end_date'], datetime.date.__class__):
            report_copy['end_date'] = report_copy['end_date'].strftime('%Y-%m-%d')
            
        serializable_history.append(report_copy)
    
    with open(file_path, 'w') as f:
        json.dump(serializable_history, f, indent=2)

def load_user_history(username):
    """Load a user's report history from their data file."""
    user_dir = ensure_user_directory(username)
    file_path = os.path.join(user_dir, 'history.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            history = json.load(f)
            
        # Convert date strings back to datetime objects
        for report in history:
            if 'start_date' in report and isinstance(report['start_date'], str):
                report['start_date'] = datetime.strptime(report['start_date'], '%Y-%m-%d').date()
            if 'end_date' in report and isinstance(report['end_date'], str):
                report['end_date'] = datetime.strptime(report['end_date'], '%Y-%m-%d').date()
                
        return history
    else:
        return []

def save_user_settings(username, settings):
    """Save a user's settings to their data file."""
    user_dir = ensure_user_directory(username)
    file_path = os.path.join(user_dir, 'settings.json')
    
    # Convert date objects to strings
    serializable_settings = {}
    for key, value in settings.items():
        if isinstance(value, datetime.date.__class__):
            serializable_settings[key] = value.strftime('%Y-%m-%d')
        else:
            serializable_settings[key] = value
    
    with open(file_path, 'w') as f:
        json.dump(serializable_settings, f, indent=2)

def load_user_settings(username):
    """Load a user's settings from their data file."""
    user_dir = ensure_user_directory(username)
    file_path = os.path.join(user_dir, 'settings.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            settings = json.load(f)
            
        # Convert date strings back to datetime objects
        for key, value in list(settings.items()):
            if key.endswith('_date') and isinstance(value, str):
                settings[key] = datetime.strptime(value, '%Y-%m-%d').date()
                
        return settings
    else:
        return {} 