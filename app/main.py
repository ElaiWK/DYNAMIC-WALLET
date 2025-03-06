import streamlit as st

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="Dynamic Wallet",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import os
import json
import re
import time
import shutil
import yaml
import hashlib
from datetime import datetime, timedelta, date
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import traceback
import hmac
from enum import Enum
import matplotlib
matplotlib.use('Agg')

from constants.config import (
    TransactionType,
    ExpenseCategory,
    IncomeCategory,
    MealType,
    HR_RATES,
    DATE_FORMAT,
    TRANSACTION_HEADERS
)
from utils.helpers import (
    get_week_period,
    is_late_submission,
    calculate_meal_expense,
    calculate_hr_expense,
    format_currency,
    create_transaction_df,
    get_period_summary
)

# Initialize session state for first load
if "first_load" not in st.session_state:
    st.session_state.first_load = True

# CRITICAL: Always reset authentication state when the script loads
# This is essential for both local and cloud deployments
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data_loaded' not in st.session_state:
    st.session_state.user_data_loaded = False

# Initialize SQLite database
def init_db():
    """Initialize the SQLite database with required tables"""
    try:
        conn = sqlite3.connect('dynamic_wallet.db')
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS user_data
        (username TEXT, data_type TEXT, data TEXT, 
        PRIMARY KEY (username, data_type))
        ''')
        conn.commit()
        
        # Verify the table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_data'")
        if not c.fetchone():
            print("ERROR - Failed to create user_data table")
        else:
            print("DEBUG - SQLite database initialized successfully")
            
        conn.close()
    except Exception as e:
        print(f"ERROR - Failed to initialize database: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")

def verify_db_integrity():
    """Verify the integrity of the database and repair if needed"""
    try:
        conn = sqlite3.connect('dynamic_wallet.db')
        c = conn.cursor()
        
        # Check if the user_data table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_data'")
        if not c.fetchone():
            print("WARNING - user_data table not found, recreating...")
            c.execute('''
            CREATE TABLE IF NOT EXISTS user_data
            (username TEXT, data_type TEXT, data TEXT, 
            PRIMARY KEY (username, data_type))
            ''')
            conn.commit()
        
        # Verify we can read from the table
        try:
            c.execute("SELECT COUNT(*) FROM user_data")
            count = c.fetchone()[0]
            print(f"DEBUG - Database contains {count} records")
        except sqlite3.OperationalError:
            print("ERROR - Could not read from user_data table, recreating...")
            c.execute("DROP TABLE IF EXISTS user_data")
            c.execute('''
            CREATE TABLE IF NOT EXISTS user_data
            (username TEXT, data_type TEXT, data TEXT, 
            PRIMARY KEY (username, data_type))
            ''')
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR - Database integrity check failed: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return False

def save_user_data(username, data_type, data):
    """Save user data to SQLite database"""
    if not username:
        print(f"DEBUG - No username provided, skipping save_user_data for {data_type}")
        return
        
    print(f"DEBUG - Saving {data_type} for user {username}")
    
    # Convert data to JSON string
    try:
        data_converted = convert_to_serializable(data)
        data_json = json.dumps(data_converted)
        
        # Print sample of data being saved
        data_sample = str(data_converted)[:100] + "..." if len(str(data_converted)) > 100 else str(data_converted)
        print(f"DEBUG - Data being saved: {data_sample}")
        
        conn = sqlite3.connect('dynamic_wallet.db')
        c = conn.cursor()
        
        # First check if the record exists
        c.execute("SELECT COUNT(*) FROM user_data WHERE username=? AND data_type=?", 
                 (username, data_type))
        exists = c.fetchone()[0] > 0
        
        if exists:
            print(f"DEBUG - Updating existing record for {username}, {data_type}")
            c.execute("UPDATE user_data SET data=? WHERE username=? AND data_type=?",
                    (data_json, username, data_type))
        else:
            print(f"DEBUG - Inserting new record for {username}, {data_type}")
            c.execute("INSERT INTO user_data VALUES (?, ?, ?)",
                    (username, data_type, data_json))
        
        conn.commit()
        
        # Verify the data was saved correctly
        c.execute("SELECT data FROM user_data WHERE username=? AND data_type=?",
                (username, data_type))
        result = c.fetchone()
        
        if result:
            print(f"DEBUG - Successfully saved {data_type} for user {username}")
            print(f"DEBUG - Saved data size: {len(result[0])} bytes")
        else:
            print(f"DEBUG - WARNING: Data may not have been saved correctly for {username}, {data_type}")
        
        conn.close()
    except Exception as e:
        print(f"DEBUG - Error saving {data_type}: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")

def load_user_data(username, data_type, default=None):
    """Load user data from SQLite database"""
    if not username:
        print(f"DEBUG - No username provided, skipping load_user_data for {data_type}")
        return default or []
        
    print(f"DEBUG - Loading {data_type} for user {username}")
    
    if default is None:
        default = []
        
    try:
        conn = sqlite3.connect('dynamic_wallet.db')
        c = conn.cursor()
        c.execute("SELECT data FROM user_data WHERE username=? AND data_type=?",
                (username, data_type))
        result = c.fetchone()
        conn.close()
        
        if result:
            try:
                data = json.loads(result[0])
                print(f"DEBUG - Successfully loaded {data_type} for user {username}")
                print(f"DEBUG - Data sample: {str(data)[:100]}...")
                return data
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSON decode error for {data_type}: {str(e)}")
                print(f"DEBUG - Raw data: {result[0][:100]}...")
                return default
        else:
            print(f"DEBUG - No {data_type} found for user {username}")
            return default
    except Exception as e:
        print(f"DEBUG - Error loading {data_type}: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return default

# Replace file-based functions with SQLite functions
def save_user_transactions(username, transactions):
    """Save user transactions to both SQLite database and file"""
    print(f"DEBUG - Saving transactions for user {username} with {len(transactions)} items")
    
    # Save to SQLite
    save_user_data(username, 'transactions', transactions)
    
    # Also save to file as backup
    try:
        user_dir = get_user_dir(username)
        transactions_file = os.path.join(user_dir, "transactions.json")
        
        with open(transactions_file, 'w') as f:
            json.dump(convert_to_serializable(transactions), f, indent=2)
            print(f"DEBUG - Successfully saved transactions to file for user {username}")
    except Exception as e:
        print(f"DEBUG - Error saving transactions to file: {str(e)}")

def load_user_transactions(username):
    """Load user transactions from SQLite database with file-based fallback"""
    try:
        # First try to load from SQLite
        transactions_from_db = load_user_data(username, 'transactions', [])
        
        if transactions_from_db and len(transactions_from_db) > 0:
            print(f"DEBUG - Successfully loaded transactions from SQLite for user {username}")
            return transactions_from_db
        
        # If SQLite failed or returned empty, try file-based approach
        print(f"DEBUG - SQLite transactions empty, trying file-based approach for {username}")
        user_dir = get_user_dir(username)
        transactions_file = os.path.join(user_dir, "transactions.json")
        
        if os.path.exists(transactions_file):
            try:
                with open(transactions_file, 'r') as f:
                    transactions_data = json.load(f)
                    print(f"DEBUG - Successfully loaded transactions from file for user {username}")
                    print(f"DEBUG - File-based transactions has {len(transactions_data)} items")
                    
                    # Save to SQLite for future use
                    save_user_data(username, 'transactions', transactions_data)
                    
                    return transactions_data
            except Exception as e:
                print(f"DEBUG - Error loading transactions from file: {str(e)}")
        
        # If all else fails, return empty list
        print(f"DEBUG - No transactions found for user {username}")
        return []
    except Exception as e:
        print(f"DEBUG - Error in load_user_transactions: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return []

def save_user_history(username, history):
    """Save user history to both SQLite database and file"""
    print(f"DEBUG - Saving history for user {username} with {len(history)} items")
    
    # Ensure history is a list
    if not isinstance(history, list):
        print(f"DEBUG - Warning: history is not a list, it's a {type(history)}")
        history = list(history) if hasattr(history, '__iter__') else [history]
    
    # Ensure each item in history is properly serializable
    for i, report in enumerate(history):
        if not isinstance(report, dict):
            print(f"DEBUG - Warning: report {i} is not a dict, it's a {type(report)}")
            continue
        
        # Ensure required keys exist
        required_keys = ["number", "period", "transactions", "summary"]
        for key in required_keys:
            if key not in report:
                print(f"DEBUG - Warning: report {i} is missing key '{key}'")
                if key == "summary":
                    report["summary"] = {"total_expenses": 0, "net_amount": 0}
                elif key == "transactions":
                    report["transactions"] = []
                elif key == "number":
                    report["number"] = f"Relatório {i+1}"
                elif key == "period":
                    report["period"] = "Período não especificado"
    
    # Save to SQLite
    save_user_data(username, 'history', history)
    
    # Also save to file as backup
    try:
        user_dir = get_user_dir(username)
        history_file = os.path.join(user_dir, "history.json")
        
        with open(history_file, 'w') as f:
            json.dump(convert_to_serializable(history), f, indent=2)
            print(f"DEBUG - Successfully saved history to file for user {username}")
    except Exception as e:
        print(f"DEBUG - Error saving history to file: {str(e)}")

def load_user_history(username):
    """Load user history from file"""
    try:
        print(f"DEBUG - Loading history for user {username}")
        user_dir = get_user_dir(username)
        history_file = os.path.join(user_dir, "history.json")
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    print(f"DEBUG - Successfully loaded history from file for user {username}")
                    print(f"DEBUG - File-based history has {len(history_data)} items")
                    print(f"DEBUG - History data sample: {str(history_data)[:200]}...")
                    return history_data
            except Exception as e:
                print(f"DEBUG - Error loading history from file: {str(e)}")
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
        
        # If all else fails, return empty list
        print(f"DEBUG - No history found for user {username}")
        return []
    except Exception as e:
        print(f"DEBUG - Error in load_user_history: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return []

def save_user_dates(username, start_date, end_date, report_counter=1):
    """Save user date range and report counter to both SQLite database and file"""
    dates_data = {
        "start_date": start_date,
        "end_date": end_date,
        "report_counter": report_counter
    }
    
    # Save to SQLite
    save_user_data(username, 'dates', dates_data)
    
    # Also save to file as backup
    try:
        user_dir = get_user_dir(username)
        dates_file = os.path.join(user_dir, "dates.json")
        
        with open(dates_file, 'w') as f:
            json.dump(convert_to_serializable(dates_data), f, indent=2)
            print(f"DEBUG - Successfully saved dates to file for user {username}")
    except Exception as e:
        print(f"DEBUG - Error saving dates to file: {str(e)}")

def load_user_dates(username):
    """Load user date range and report counter from file"""
    try:
        print(f"DEBUG - Loading dates for user {username}")
        user_dir = get_user_dir(username)
        dates_file = os.path.join(user_dir, "dates.json")
        
        if os.path.exists(dates_file):
            try:
                with open(dates_file, 'r') as f:
                    dates_data = json.load(f)
                    print(f"DEBUG - Successfully loaded dates from file for user {username}")
                    
                    start_date = dates_data.get('start_date')
                    end_date = dates_data.get('end_date')
                    report_counter = dates_data.get('report_counter', 1)
                    
                    # Convert string dates to datetime objects
                    if isinstance(start_date, str):
                        try:
                            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
                            except ValueError:
                                print(f"DEBUG - Could not parse start_date: {start_date}")
                                # Default to today
                                start_date = datetime.now().date()
                    
                    if isinstance(end_date, str):
                        try:
                            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                end_date = datetime.strptime(end_date, '%d/%m/%Y').date()
                            except ValueError:
                                print(f"DEBUG - Could not parse end_date: {end_date}")
                                # Default to today + 6 days
                                end_date = datetime.now().date() + timedelta(days=6)
                    
                    return {
                        "start_date": start_date,
                        "end_date": end_date,
                        "report_counter": report_counter
                    }
            except Exception as e:
                print(f"DEBUG - Error loading dates from file: {str(e)}")
        
        # If file doesn't exist or error, return default dates
        print(f"DEBUG - No dates found for user {username}, using defaults")
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())  # Monday of current week
        end_date = start_date + timedelta(days=6)  # Sunday of current week
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "report_counter": 1
        }
    except Exception as e:
        print(f"DEBUG - Error in load_user_dates: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        
        # Return default dates in case of error
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "report_counter": 1
        }

# User authentication functions
def get_users_file_path():
    """Get the path to the users.json file"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        # st.write(f"Debug - Data directory path: {data_dir}")
        # st.write(f"Debug - Data directory exists: {os.path.exists(data_dir)}")
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                # st.write(f"Debug - Created data directory: {data_dir}")
            except Exception as e:
                # st.write(f"Debug - Error creating data directory: {str(e)}")
                # Use a fallback location
                data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
                # st.write(f"Debug - Using fallback data directory: {data_dir}")
        
        users_file = os.path.join(data_dir, "users.json")
        # st.write(f"Debug - Users file path: {users_file}")
        # st.write(f"Debug - Users file exists: {os.path.exists(users_file)}")
        return users_file
    except Exception as e:
        # If all else fails, use a local path
        return "users.json"

def load_users():
    """Load users from the JSON file"""
    try:
        users_file = get_users_file_path()
        
        if os.path.exists(users_file):
            try:
                with open(users_file, "r") as f:
                    users = json.load(f)
                # st.write(f"Debug - Successfully loaded {len(users)} users")
                return users
            except Exception as e:
                # st.write(f"Debug - Error loading users file: {str(e)}")
                pass
        
        # If file doesn't exist or there was an error, initialize with default users
        # st.write("Debug - Initializing default users")
        return initialize_default_users()
    except Exception as e:
        # st.write(f"Debug - Critical error in load_users: {str(e)}")
        # Return a minimal set of users as a last resort
        return {
            "admin": {
                "password": hash_password("admin123"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_admin": True
            }
        }

def initialize_default_users():
    """Initialize the system with default users if none exist"""
    default_users = {
        "Valeriya": {"password": hash_password("Bw7$pQzX9tLm"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Luis": {"password": hash_password("K3r@NvD8sYfE"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Joao": {"password": hash_password("P9j$Tz5LqWxH"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Humberto": {"password": hash_password("G4h&FmV7cRpZ"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Goncalo": {"password": hash_password("X2s#Jb6QnDvA"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Josue": {"password": hash_password("M5t@Rz8PkLdS"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Bruno": {"password": hash_password("C7f$Qp3HjNxY"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "PauloP": {"password": hash_password("V9g&Zk4TmBwJ"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "PauloR": {"password": hash_password("L6h#Xd2RqFsP"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Jose": {"password": hash_password("T8j$Mn5VcKpZ"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Ricardo": {"password": hash_password("D3k@Qb7GxWfS"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Antonio": {"password": hash_password("N4m&Vp9JzTcR"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Sodia": {"password": hash_password("F6s#Hd3LqBxZ"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Timoteo": {"password": hash_password("R9t$Kp5MnVjW"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Armando": {"password": hash_password("H2v@Zf8QcPdG"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Nelson": {"password": hash_password("W7g&Jm4TzBsX"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Tudor": {"password": hash_password("S3k#Vb9NpRfD"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Mika": {"password": hash_password("Y5m$Qz7HjLcT"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Lucas": {"password": hash_password("B8p@Xd4GvWkS"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "Carla": {"password": hash_password("J6r&Zn2TmFqP"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "admin": {"password": hash_password("admin123"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "is_admin": True}
    }
    save_users(default_users)
    return default_users

def save_users(users):
    """Save users to the JSON file"""
    try:
        users_file = get_users_file_path()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        with open(users_file, "w") as f:
            json.dump(users, f, indent=4)
        # st.write(f"Debug - Successfully saved {len(users)} users")
        return True
    except Exception as e:
        # st.write(f"Debug - Error saving users file: {str(e)}")
        return False
    except Exception as e:
        # st.write(f"Debug - Critical error in save_users: {str(e)}")
        return False

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against a provided password"""
    return stored_password == hash_password(provided_password)

def create_user(username, password):
    """Create a new user"""
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    return True

def authenticate(username, password):
    """Authenticate a user with username and password"""
    try:
        # st.write(f"Debug - Authenticating user: {username}")
        
        # Special case for admin in cloud environment
        if username == "admin" and os.environ.get("STREAMLIT_CLOUD") == "true":
            # st.write("Debug - Using hardcoded admin credentials")
            return password == "admin123"
        
        users = load_users()
        # st.write(f"Debug - Loaded users: {list(users.keys())}")
        
        if username not in users:
            # st.write(f"Debug - User {username} not found")
            return False
        
        result = verify_password(users[username]["password"], password)
        # st.write(f"Debug - Password verification result: {result}")
        return result
    except Exception as e:
        # st.write(f"Debug - Authentication error: {str(e)}")
        return False

def show_login_page():
    """Show the login page"""
    # st.write("Debug - Current session state keys:", list(st.session_state.keys()))
    
    # Adicionar título "DYNAMIC WALLET"
    st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>DYNAMIC WALLET</h1>", unsafe_allow_html=True)
    
    # Centralizar o formulário de login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Login form
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Nome de usuário")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")
            
            if submit_button:
                st.write(f"Tentando login para usuário: {username}")
                
                if authenticate(username, password):
                    st.success(f"Login bem-sucedido! Bem-vindo, {username}!")
                    
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.is_admin = username == "admin"
                    
                    print(f"DEBUG - Login successful for user: {username}")
                    print(f"DEBUG - Is admin: {st.session_state.is_admin}")
                    
                    # Clear existing data first to prevent mixing
                    for key in list(st.session_state.keys()):
                        if key not in ["authenticated", "username", "is_admin", "page", "first_load"]:
                            del st.session_state[key]
                    
                    # Load user data
                    print(f"DEBUG - Loading user data for: {username}")
                    
                    # Make sure user directory exists
                    user_dir = get_user_dir(username)
                    os.makedirs(user_dir, exist_ok=True)
                    
                    # Load transactions
                    print("DEBUG - Loading transactions")
                    st.session_state.transactions = load_user_transactions(username) or []
                    print(f"DEBUG - Loaded {len(st.session_state.transactions)} transactions")
                    
                    # Load history
                    print("DEBUG - Loading history")
                    st.session_state.history = load_user_history(username) or []
                    print(f"DEBUG - Loaded {len(st.session_state.history)} history items")
                    print(f"DEBUG - History data: {str(st.session_state.history)[:200]}...")
                    
                    # Load dates
                    dates = load_user_dates(username)
                    st.session_state.start_date = dates["start_date"]
                    st.session_state.end_date = dates["end_date"]
                    st.session_state.report_counter = dates.get("report_counter", 1)
                    
                    print(f"DEBUG - Loaded dates: {st.session_state.start_date} to {st.session_state.end_date}")
                    print(f"DEBUG - Report counter: {st.session_state.report_counter}")
                    
                    # Redirect to main page
                    st.session_state.page = "main"
                    st.rerun()
                else:
                    st.error("Nome de usuário ou senha inválidos")

def get_week_dates(date):
    # Get Monday (start) of the week
    monday = date - timedelta(days=date.weekday())
    # Get Sunday (end) of the week
    sunday = monday + timedelta(days=6)
    return monday, sunday

def format_date_range(start_date, end_date):
    """Format date range for display, handling both string and datetime objects"""
    # Convert string dates to datetime objects if needed
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format
            start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
    
    if isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format
            end_date = datetime.strptime(end_date, '%d/%m/%Y').date()
    
    return f"De {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"

def get_next_week_dates(current_end_date):
    """Get the next week's date range, handling both string and datetime objects"""
    # Convert string date to datetime object if needed
    if isinstance(current_end_date, str):
        try:
            current_end_date = datetime.strptime(current_end_date, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format
            current_end_date = datetime.strptime(current_end_date, '%d/%m/%Y').date()
    
    next_monday = current_end_date + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)
    return next_monday, next_sunday

def is_submission_late(end_date):
    """Check if submission is late, handling both string and datetime objects"""
    # Convert string date to datetime object if needed
    if isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format
            end_date = datetime.strptime(end_date, '%d/%m/%Y').date()
    
    return datetime.now().date() > end_date

# Initialize session state
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "page" not in st.session_state:
    st.session_state.page = "main"
if "transaction_type" not in st.session_state:
    st.session_state.transaction_type = None
if "category" not in st.session_state:
    st.session_state.category = None
if "history" not in st.session_state:
    st.session_state.history = []
if "report_counter" not in st.session_state:
    st.session_state.report_counter = 1
# Initialize date range
if "current_start_date" not in st.session_state:
    start_date = datetime.strptime("03/02/2025", "%d/%m/%Y").date()
    end_date = datetime.strptime("09/02/2025", "%d/%m/%Y").date()
    st.session_state.current_start_date = start_date
    st.session_state.current_end_date = end_date

def reset_state():
    """Reset the session state"""
    # Save current state before resetting if user is authenticated
    if "authenticated" in st.session_state and st.session_state.authenticated:
        save_user_transactions(st.session_state.username, st.session_state.transactions)
        save_user_history(st.session_state.username, st.session_state.history)
    
    st.session_state.transactions = []
    st.session_state.page = "main"
    st.session_state.transaction_type = None
    st.session_state.category = None

def navigate_to_categories(transaction_type):
    st.session_state.page = "categories"
    st.session_state.transaction_type = transaction_type
    st.rerun()

def navigate_to_form(category):
    st.session_state.category = category
    st.session_state.page = "form"
    st.rerun()

def navigate_back():
    if st.session_state.page == "form":
        # Reset meal form state if coming from meal expense form
        if st.session_state.category == ExpenseCategory.MEAL.value:
            if "meal_total_amount" in st.session_state:
                del st.session_state.meal_total_amount
            if "meal_num_people" in st.session_state:
                del st.session_state.meal_num_people
            if "collaborator_names" in st.session_state:
                del st.session_state.collaborator_names
            if "meal_date" in st.session_state:
                del st.session_state.meal_date
        # Reset HR form state if coming from HR form
        elif st.session_state.category == ExpenseCategory.HR.value:
            if "hr_role" in st.session_state:
                del st.session_state.hr_role
            if "hr_date" in st.session_state:
                del st.session_state.hr_date
            if "hr_collaborator" in st.session_state:
                del st.session_state.hr_collaborator
        # Reset purchase form state if coming from purchase form
        elif st.session_state.category == ExpenseCategory.OTHER.value:
            if "purchase_what" in st.session_state:
                del st.session_state.purchase_what
            if "purchase_amount" in st.session_state:
                del st.session_state.purchase_amount
            if "purchase_justification" in st.session_state:
                del st.session_state.purchase_justification
            if "purchase_date" in st.session_state:
                del st.session_state.purchase_date
        # Reset delivery form state if coming from delivery form
        elif st.session_state.category == ExpenseCategory.DELIVERY.value:
            if "delivery_collaborator" in st.session_state:
                del st.session_state.delivery_collaborator
            if "delivery_amount" in st.session_state:
                del st.session_state.delivery_amount
            if "delivery_date" in st.session_state:
                del st.session_state.delivery_date
        # Reset service form state
        elif st.session_state.category == IncomeCategory.SERVICE.value:
            if "service_reference" in st.session_state:
                del st.session_state.service_reference
            if "service_amount" in st.session_state:
                del st.session_state.service_amount
            if "service_date" in st.session_state:
                del st.session_state.service_date
        # Reset delivery income form state
        elif st.session_state.category == IncomeCategory.DELIVERY.value:
            if "delivery_income_collaborator" in st.session_state:
                del st.session_state.delivery_income_collaborator
            if "delivery_income_amount" in st.session_state:
                del st.session_state.delivery_income_amount
            if "delivery_income_date" in st.session_state:
                del st.session_state.delivery_income_date
        st.session_state.page = "categories"
    elif st.session_state.page == "categories":
        st.session_state.page = "main"
        st.session_state.transaction_type = None
    st.rerun()

def show_home_button():
    st.markdown('<div class="home-button">', unsafe_allow_html=True)
    if st.button("🏠 Dynamic Wallet", key="home_button"):
        st.session_state.page = "main"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_main_page():
    """Show the main page with navigation sidebar"""
    # Debug message
    print("DEBUG - show_main_page function called")
    
    # Add sidebar for navigation
    with st.sidebar:
        st.title("Navegação")
        
        # User info
        st.write(f"Logado como: **{st.session_state.username}**")
        
        # Navigation tabs
        if st.button("Início", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()
            
        if st.button("Histórico", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
            
        if st.button("Relatório", use_container_width=True):
            st.session_state.page = "report"
            st.rerun()
            
        # Show admin tab only for admin users
        if st.session_state.is_admin:
            if st.button("Admin", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()
        
        # Add some space
        st.write("")
        st.write("")
        st.write("")
        
        # Logout button at the bottom
        if st.button("Sair", use_container_width=True):
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Set default values
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
    
    # Center the title without icon
    st.markdown(f"""
        <h1 style="text-align: center; margin-bottom: 10px;">DYNAMIC WALLET</h1>
        <div style="text-align: center; font-size: 16px; color: #888888; margin-bottom: 40px;">
            {format_date_range(st.session_state.start_date, st.session_state.end_date)}
        </div>
        <style>
        .amount-title {{
            color: #FFFFFF;
            text-align: center;
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .amount-container {{
            background-color: #262730;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            text-align: center;
        }}
        .amount-container .value {{
            color: #FFFFFF;
            font-size: 24px;
            font-weight: 500;
            margin-bottom: 5px;
        }}
        .amount-container .status {{
            color: #888888;
            font-size: 16px;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Check if submission is late
    if is_submission_late(st.session_state.end_date):
        st.markdown("""
            <div style="text-align: center; color: #ff4b4b; font-size: 18px; margin-bottom: 20px; padding: 10px; border: 1px solid #ff4b4b; border-radius: 5px;">
                ⚠️ Submissão de relatório em atraso!
            </div>
        """, unsafe_allow_html=True)
    
    # Create two columns for buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Saídas", key="expense_button", use_container_width=True):
            st.session_state.page = "categories"
            st.session_state.transaction_type = TransactionType.EXPENSE.value
            st.rerun()
    
    with col2:
        if st.button("Entradas", key="income_button", use_container_width=True):
            st.session_state.page = "categories"
            st.session_state.transaction_type = TransactionType.INCOME.value
            st.rerun()
    
    # Show balance at the bottom
    # Initialize values
    abs_amount = 0
    status_text = ""
    
    if st.session_state.transactions:
        df = create_transaction_df(st.session_state.transactions)
        summary = get_period_summary(df)
        
        # Calculate absolute value and determine status
        abs_amount = abs(summary['net_amount'])
        status_text = "A receber" if summary['net_amount'] < 0 else "A entregar" if summary['net_amount'] > 0 else ""
    
    st.markdown('<div class="amount-title">Saldo</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="amount-container">
        <div class="value">{format_currency(abs_amount)}</div>
        <div class="status">{status_text}</div>
    </div>
    """, unsafe_allow_html=True)

def show_categories():
    """Show the categories page"""
    # Back button in categories
    show_home_button()
    st.subheader("Categorias")
    st.write("Selecione uma categoria para registrar uma transação:")
    
    # Add buttons for different transaction types
    if st.button("Saídas"):
        st.session_state.category = ExpenseCategory.OTHER.value
        navigate_to_form(ExpenseCategory.OTHER.value)
    if st.button("Saídas"):
        st.session_state.category = ExpenseCategory.HR.value
        navigate_to_form(ExpenseCategory.HR.value)
    if st.button("Saídas"):
        st.session_state.category = ExpenseCategory.DELIVERY.value
        navigate_to_form(ExpenseCategory.DELIVERY.value)
    if st.button("Entradas"):
        st.session_state.category = IncomeCategory.SERVICE.value
        navigate_to_form(IncomeCategory.SERVICE.value)
    if st.button("Entradas"):
        st.session_state.category = IncomeCategory.DELIVERY.value
        navigate_to_form(IncomeCategory.DELIVERY.value)

def show_form():
    """Show the form page"""
    st.subheader("Registrar Transação")
    
    # Add form for different transaction types
    if st.session_state.category == ExpenseCategory.OTHER.value:
        # Initialize session state for purchase form
        if "purchase_what" not in st.session_state:
            st.session_state.purchase_what = ""
        if "purchase_amount" not in st.session_state:
            st.session_state.purchase_amount = 0.0
        if "purchase_justification" not in st.session_state:
            st.session_state.purchase_justification = ""
        if "purchase_date" not in st.session_state:
            st.session_state.purchase_date = st.session_state.current_start_date
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.purchase_date,
            min_value=st.session_state.current_start_date,
            max_value=st.session_state.current_end_date,
            key="purchase_date_input"
        )
        if selected_date != st.session_state.purchase_date:
            st.session_state.purchase_date = selected_date
            st.rerun()
        
        # What field
        new_what = st.text_input(
            "O quê?",
            value=st.session_state.purchase_what,
            key="purchase_what_input"
        )
        if new_what != st.session_state.purchase_what:
            st.session_state.purchase_what = new_what
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor da Fatura (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.purchase_amount,
            key="purchase_amount_input"
        )
        if new_amount != st.session_state.purchase_amount:
            st.session_state.purchase_amount = new_amount
            st.rerun()
        
        # Justification field
        new_justification = st.text_area(
            "Justificação",
            value=st.session_state.purchase_justification,
            key="purchase_justification_input"
        )
        if new_justification != st.session_state.purchase_justification:
            st.session_state.purchase_justification = new_justification
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Always display amount for purchases
        st.markdown('<div class="amount-title">Valor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="amount-container">
            <div class="value">{format_currency(st.session_state.purchase_amount)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_purchase", use_container_width=True):
                # Validate fields
                validation_error = None
                if not st.session_state.purchase_what.strip():
                    validation_error = "Por favor, especifique o que foi comprado"
                elif st.session_state.purchase_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                elif not st.session_state.purchase_justification.strip():
                    validation_error = "Por favor, forneça uma justificação"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"{st.session_state.purchase_what} (Valor: {format_currency(st.session_state.purchase_amount)}) - {st.session_state.purchase_justification}"
                    save_transaction(
                        st.session_state.purchase_date,
                        TransactionType.EXPENSE.value,
                        ExpenseCategory.OTHER.value,
                        description,
                        st.session_state.purchase_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.purchase_what
                    del st.session_state.purchase_amount
                    del st.session_state.purchase_justification
                    del st.session_state.purchase_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.category == ExpenseCategory.DELIVERY.value:
        # Initialize session state for delivery form
        if "delivery_collaborator" not in st.session_state:
            st.session_state.delivery_collaborator = ""
        if "delivery_amount" not in st.session_state:
            st.session_state.delivery_amount = 0.0
        if "delivery_date" not in st.session_state:
            st.session_state.delivery_date = st.session_state.current_start_date
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.delivery_date,
            min_value=st.session_state.current_start_date,
            max_value=st.session_state.current_end_date,
            key="delivery_date_input"
        )
        if selected_date != st.session_state.delivery_date:
            st.session_state.delivery_date = selected_date
            st.rerun()
        
        # Collaborator name field
        new_collaborator = st.text_input(
            "Nome do Colaborador",
            value=st.session_state.delivery_collaborator,
            key="delivery_collaborator_input"
        )
        if new_collaborator != st.session_state.delivery_collaborator:
            st.session_state.delivery_collaborator = new_collaborator
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.delivery_amount,
            key="delivery_amount_input"
        )
        if new_amount != st.session_state.delivery_amount:
            st.session_state.delivery_amount = new_amount
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Always display amount for deliveries
        st.markdown('<div class="amount-title">Valor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="amount-container">
            <div class="value">{format_currency(st.session_state.delivery_amount)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_delivery", use_container_width=True):
                # Validate fields
                validation_error = None
                if not st.session_state.delivery_collaborator.strip():
                    validation_error = "Por favor, insira o nome do colaborador"
                elif st.session_state.delivery_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"Entregue a {st.session_state.delivery_collaborator} (Valor: {format_currency(st.session_state.delivery_amount)})"
                    save_transaction(
                        st.session_state.delivery_date,
                        TransactionType.EXPENSE.value,
                        ExpenseCategory.DELIVERY.value,
                        description,
                        st.session_state.delivery_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.delivery_collaborator
                    del st.session_state.delivery_amount
                    del st.session_state.delivery_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.category == IncomeCategory.SERVICE.value:
        # Initialize session state for service form
        if "service_reference" not in st.session_state:
            st.session_state.service_reference = ""
        if "service_amount" not in st.session_state:
            st.session_state.service_amount = 0.0
        if "service_date" not in st.session_state:
            st.session_state.service_date = st.session_state.current_start_date
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.service_date,
            min_value=st.session_state.current_start_date,
            max_value=st.session_state.current_end_date,
            key="service_date_input"
        )
        if selected_date != st.session_state.service_date:
            st.session_state.service_date = selected_date
            st.rerun()
        
        # Reference number field
        new_reference = st.text_input(
            "Número do Serviço",
            value=st.session_state.service_reference,
            key="service_reference_input"
        )
        if new_reference != st.session_state.service_reference:
            st.session_state.service_reference = new_reference
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.service_amount,
            key="service_amount_input"
        )
        if new_amount != st.session_state.service_amount:
            st.session_state.service_amount = new_amount
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Always display amount for services
        st.markdown('<div class="amount-title">Valor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="amount-container">
            <div class="value">{format_currency(st.session_state.service_amount)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_service", use_container_width=True):
                # Validate fields
                validation_error = None
                if not st.session_state.service_reference.strip():
                    validation_error = "Por favor, insira o número do serviço"
                elif st.session_state.service_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"Serviço #{st.session_state.service_reference} (Valor: {format_currency(st.session_state.service_amount)})"
                    save_transaction(
                        st.session_state.service_date,
                        TransactionType.INCOME.value,
                        IncomeCategory.SERVICE.value,
                        description,
                        st.session_state.service_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.service_reference
                    del st.session_state.service_amount
                    del st.session_state.service_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.category == IncomeCategory.DELIVERY.value:
        # Initialize session state for delivery income form
        if "delivery_income_collaborator" not in st.session_state:
            st.session_state.delivery_income_collaborator = ""
        if "delivery_income_amount" not in st.session_state:
            st.session_state.delivery_income_amount = 0.0
        if "delivery_income_date" not in st.session_state:
            st.session_state.delivery_income_date = st.session_state.current_start_date
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.delivery_income_date,
            min_value=st.session_state.current_start_date,
            max_value=st.session_state.current_end_date,
            key="delivery_income_date_input"
        )
        if selected_date != st.session_state.delivery_income_date:
            st.session_state.delivery_income_date = selected_date
            st.rerun()
        
        # Collaborator name field
        new_collaborator = st.text_input(
            "Nome do Colaborador",
            value=st.session_state.delivery_income_collaborator,
            key="delivery_income_collaborator_input"
        )
        if new_collaborator != st.session_state.delivery_income_collaborator:
            st.session_state.delivery_income_collaborator = new_collaborator
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.delivery_income_amount,
            key="delivery_income_amount_input"
        )
        if new_amount != st.session_state.delivery_income_amount:
            st.session_state.delivery_income_amount = new_amount
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Always display amount for delivery income
        st.markdown('<div class="amount-title">Valor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="amount-container">
            <div class="value">{format_currency(st.session_state.delivery_income_amount)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_delivery_income", use_container_width=True):
                # Validate fields
                validation_error = None
                if not st.session_state.delivery_income_collaborator.strip():
                    validation_error = "Por favor, insira o nome do colaborador"
                elif st.session_state.delivery_income_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"Recebido de {st.session_state.delivery_income_collaborator} (Valor: {format_currency(st.session_state.delivery_income_amount)})"
                    save_transaction(
                        st.session_state.delivery_income_date,
                        TransactionType.INCOME.value,
                        IncomeCategory.DELIVERY.value,
                        description,
                        st.session_state.delivery_income_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.delivery_income_collaborator
                    del st.session_state.delivery_income_amount
                    del st.session_state.delivery_income_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        with st.form("transaction_form", clear_on_submit=True):
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            date = st.date_input("Data", datetime.now())
            amount = None
            error = None
            
            amount = st.number_input("Valor (€)", min_value=0.0, step=0.5)
            description = st.text_input("Descrição")
            
            if st.form_submit_button("Submeter"):
                error = None if amount > 0 else "O valor deve ser maior que 0"
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if error:
                st.error(error)
            elif amount is not None:
                save_transaction(date, st.session_state.transaction_type, st.session_state.category, description, amount)
                st.success("Transação registrada com sucesso!")
                st.session_state.page = "main"
                st.rerun()

def save_transaction(date, type_, category, description, amount):
    """Save a transaction to the session state"""
    # Format date as string if it's a date object
    date_str = date.strftime(DATE_FORMAT) if hasattr(date, 'strftime') else date
    
    transaction = {
        "Date": date_str,
        "Type": type_,
        "Category": category,
        "Description": description,
        "Amount": amount,
        "Username": st.session_state.username  # Add username to transaction
    }
    st.session_state.transactions.append(transaction)
    
    # Save transactions to file
    save_user_transactions(st.session_state.username, st.session_state.transactions)
    
    # Auto-save all user data
    auto_save_user_data()

# User data functions
def get_user_data_dir():
    """Get the directory for user data"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users")
    print(f"DEBUG - User data directory: {data_dir}")
    print(f"DEBUG - Current working directory: {os.getcwd()}")
    print(f"DEBUG - __file__: {__file__}")
    print(f"DEBUG - Directory exists: {os.path.exists(data_dir)}")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            print(f"DEBUG - Created directory: {data_dir}")
        except Exception as e:
            print(f"DEBUG - Error creating directory: {str(e)}")
    return data_dir

def get_user_dir(username):
    """Get the directory for a specific user"""
    user_dir = os.path.join(get_user_data_dir(), username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def generate_pdf_report(username, report_data):
    """Generate a PDF report for a user's expense report"""
    # Create a BytesIO object to store the PDF
    buffer = BytesIO()
    
    # Create the PDF document with wider margins to prevent text cutting
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           leftMargin=36, rightMargin=36, 
                           topMargin=36, bottomMargin=36)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add title
    elements.append(Paragraph(f"Relatório de Despesas - {report_data['number']}", title_style))
    elements.append(Spacer(1, 12))
    
    # Add user info
    elements.append(Paragraph(f"Colaborador: {username}", subtitle_style))
    elements.append(Paragraph(f"Período: {report_data['period']}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Add summary
    elements.append(Paragraph("Resumo", subtitle_style))
    summary_data = [
        ["Descrição", "Valor"],
        ["Total Despesas", f"{format_currency(report_data['summary'].get('total_expenses', report_data['summary'].get('total_expense', 0)))}"],
        ["Total Refeições", f"{format_currency(report_data['summary'].get('total_meals', 0))}"],
        ["Total Transportes", f"{format_currency(report_data['summary'].get('total_transport', 0))}"],
        ["Total Outros", f"{format_currency(report_data['summary'].get('total_other', 0))}"],
        ["Saldo Final", f"{format_currency(report_data['summary'].get('net_amount', 0))}"]
    ]
    
    # Adjust column widths for better fit
    summary_table = Table(summary_data, colWidths=[300, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, -1), (1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
        ('LEFTPADDING', (0, 0), (-1, -1), 6),    # Add padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),   # Add padding
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    
    # Add transactions
    if report_data['transactions']:
        elements.append(Paragraph("Detalhes das Transações", subtitle_style))
        
        # Create table data
        transaction_data = [["Data", "Tipo", "Categoria", "Descrição", "Valor"]]
        
        for t in report_data['transactions']:
            transaction_data.append([
                t.get('Date', t.get('date', '')),
                t.get('Type', t.get('type', '')),
                t.get('Category', t.get('category', '')),
                t.get('Description', t.get('description', '')),
                format_currency(t.get('Amount', t.get('amount', 0)))
            ])
        
        # Create the table with adjusted column widths and word wrapping
        transaction_table = Table(transaction_data, colWidths=[70, 70, 90, 180, 70])
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
            ('LEFTPADDING', (0, 0), (-1, -1), 6),    # Add padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),   # Add padding
            ('WORDWRAP', (0, 0), (-1, -1), True),    # Enable word wrapping
        ]))
        elements.append(transaction_table)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def get_pdf_download_link(pdf_data, filename):
    """Generate a download link for a PDF file"""
    b64 = base64.b64encode(pdf_data).decode()
    href = f'''
    <a href="data:application/pdf;base64,{b64}" download="{filename}.pdf" 
       style="display: flex; align-items: center; justify-content: center; 
              width: 32px; height: 32px; background-color: #1E1E1E; 
              border-radius: 4px; transition: all 0.3s; text-decoration: none;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" fill="white"/>
        </svg>
    </a>
    '''
    return href

def auto_save_user_data():
    """Auto-save all user data"""
    if "username" in st.session_state and st.session_state.username:
        username = st.session_state.username
        print(f"DEBUG - Auto-saving data for user {username}")
        print(f"DEBUG - Session state keys: {list(st.session_state.keys())}")
        
        # Save transactions
        if "transactions" in st.session_state:
            save_user_transactions(username, st.session_state.transactions)
            print(f"DEBUG - Saved {len(st.session_state.transactions)} transactions for user {username}")
        
        # Save history
        if "history" in st.session_state:
            save_user_history(username, st.session_state.history)
            print(f"DEBUG - Saved {len(st.session_state.history)} history items for user {username}")
        
        # Save dates
        if all(k in st.session_state for k in ["start_date", "end_date"]):
            save_user_dates(
                username, 
                st.session_state.start_date, 
                st.session_state.end_date,
                st.session_state.report_counter if "report_counter" in st.session_state else 1
            )
            print(f"DEBUG - Saved dates: {st.session_state.start_date} to {st.session_state.end_date}")
        else:
            print(f"DEBUG - Could not save dates, missing keys. Available keys: {list(st.session_state.keys())}")

def main():
    """Main function"""
    # Add custom CSS
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state variables if they don't exist
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    # Debug message
    print(f"DEBUG - Current page: {st.session_state.page}")
    print(f"DEBUG - Authenticated: {st.session_state.authenticated}")
    
    # Check if users.json exists, if not, create it with default users
    if not os.path.exists(get_users_file_path()):
        initialize_default_users()
    
    # Create data directory if it doesn't exist
    os.makedirs(get_user_data_dir(), exist_ok=True)
    
    # Auto-save user data on each rerun
    auto_save_user_data()
    
    # Show appropriate page based on session state
    if not st.session_state.authenticated:
        show_login_page()
    else:
        if st.session_state.page == "login":
            show_login_page()
        elif st.session_state.page == "main":
            show_main_page()
        elif st.session_state.page == "categories":
            show_categories()
        elif st.session_state.page == "form":
            show_form()
        elif st.session_state.page == "admin":
            show_admin_tab()
        elif st.session_state.page == "history":
            show_history_tab()
        elif st.session_state.page == "report":
            show_report_tab()
        else:
            st.error(f"Unknown page: {st.session_state.page}")

def show_admin_tab():
    """Show the admin dashboard"""
    st.subheader("Painel de Colaboradores")
    st.write("Visualizar dados de todos os utilizadores")
    
    # Get list of all users
    users = load_users()
    usernames = [username for username in users.keys() if username != "admin" and not username.startswith("_")]
    
    # Let admin select a user to view
    selected_user = st.selectbox("Selecionar Utilizador", usernames)
    
    if selected_user:
        st.subheader(f"Dados de {selected_user}")
        
        # Create tabs for user data
        user_transactions_tab, user_history_tab = st.tabs(["Relatório", "Histórico"])
        
        with user_transactions_tab:
            # Load user transactions
            transactions = load_user_transactions(selected_user)
            if transactions:
                df = create_transaction_df(transactions)
                
                # Split dataframe by type
                income_df = df[df["Type"] == TransactionType.INCOME.value].copy()
                expense_df = df[df["Type"] == TransactionType.EXPENSE.value].copy()
                
                # Sort each dataframe by date
                income_df = income_df.sort_values("Date", ascending=True)
                expense_df = expense_df.sort_values("Date", ascending=True)
                
                # Format amounts for display
                income_df["Amount"] = income_df["Amount"].apply(format_currency)
                expense_df["Amount"] = expense_df["Amount"].apply(format_currency)
                
                # Format dates to dd/MM
                income_df["Date"] = pd.to_datetime(income_df["Date"]).dt.strftime("%d/%m")
                expense_df["Date"] = pd.to_datetime(expense_df["Date"]).dt.strftime("%d/%m")
                
                # Display income transactions
                if not income_df.empty:
                    st.markdown("<h4 style='font-size: 18px; color: white;'>Entradas</h4>", unsafe_allow_html=True)
                    for _, row in income_df.iterrows():
                        st.markdown(f"""
                        <div style="
                            background-color: #1E1E1E;
                            border-left: 4px solid #4CAF50;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="color: #CCCCCC;">{row['Date']}</span>
                                <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <span style="background-color: rgba(76, 175, 80, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                    {row['Category']}
                                </span>
                            </div>
                            <div style="color: #FFFFFF; margin-top: 0.5rem;">
                                {row['Description']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display expense transactions
                if not expense_df.empty:
                    st.markdown("<h4 style='font-size: 18px; color: white;'>Saídas</h4>", unsafe_allow_html=True)
                    for _, row in expense_df.iterrows():
                        st.markdown(f"""
                        <div style="
                            background-color: #1E1E1E;
                            border-left: 4px solid #ff4b4b;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="color: #CCCCCC;">{row['Date']}</span>
                                <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <span style="background-color: rgba(255, 75, 75, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                    {row['Category']}
                                </span>
                            </div>
                            <div style="color: #FFFFFF; margin-top: 0.5rem;">
                                {row['Description']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Calculate summary statistics
                summary = get_period_summary(df)
                
                # Show summary statistics
                st.write("")
                st.markdown(f"""
                <div style="margin: 20px 0;">
                    <div style="margin-bottom: 15px;">
                        <span style="font-size: 20px; color: white; font-weight: 500;">Resumo:</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <span style="font-size: 16px; color: white;">Total Entradas: </span>
                        <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(summary['total_income'])}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <span style="font-size: 16px; color: white;">Total Saídas: </span>
                        <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(summary['total_expense'])}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <span style="font-size: 16px; color: white;">Saldo: </span>
                        <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(abs(summary['net_amount']))}</span>
                        <span style="font-size: 16px; color: white !important; font-weight: 500;">({'A entregar' if summary['net_amount'] >= 0 else 'A receber'})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"{selected_user} não tem transações")
        
        with user_history_tab:
            # Load user history
            history = load_user_history(selected_user)
            if history:
                for report in history:
                    # Create a container with fixed width columns to prevent overlap
                    st.markdown("""
                    <style>
                    .download-button-container {
                        display: flex;
                        align-items: center;
                        margin-bottom: 10px;
                    }
                    .download-button {
                        flex: 0 0 40px;
                        margin-right: 15px;
                    }
                    .report-title {
                        flex: 1;
                        min-width: 0;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Generate PDF report
                    report_id = f"{selected_user}_{report['number'].replace(' ', '_')}"
                    pdf_data = generate_pdf_report(selected_user, report)
                    download_link = get_pdf_download_link(pdf_data, f"Relatorio_{report_id}")
                    
                    # Create a custom layout with HTML/CSS
                    report_title = f"{report['number']} - {format_currency(abs(report['summary']['net_amount']))} ({'A entregar' if report['summary']['net_amount'] >= 0 else 'A receber'})"
                    
                    st.markdown(f"""
                    <div class="download-button-container">
                        <div class="download-button">{download_link}</div>
                        <div class="report-title">{report_title}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Use the expander without a title since we've already displayed it
                    with st.expander("Ver detalhes"):
                        # Create DataFrame from transactions
                        df_report = create_transaction_df(report['transactions'])
                        
                        # Split and sort transactions by type
                        income_df = df_report[df_report["Type"] == TransactionType.INCOME.value].copy()
                        expense_df = df_report[df_report["Type"] == TransactionType.EXPENSE.value].copy()
                        
                        income_df = income_df.sort_values("Date", ascending=True)
                        expense_df = expense_df.sort_values("Date", ascending=True)
                        
                        # Format amounts and dates
                        income_df["Amount"] = income_df["Amount"].apply(format_currency)
                        expense_df["Amount"] = expense_df["Amount"].apply(format_currency)
                        income_df["Date"] = pd.to_datetime(income_df["Date"]).dt.strftime("%d/%m")
                        expense_df["Date"] = pd.to_datetime(expense_df["Date"]).dt.strftime("%d/%m")
                        
                        # Display income transactions
                        if not income_df.empty:
                            st.markdown("<h4 style='font-size: 18px; color: white;'>Entradas</h4>", unsafe_allow_html=True)
                            for _, row in income_df.iterrows():
                                st.markdown(f"""
                                <div style="
                                    background-color: #1E1E1E;
                                    border-left: 4px solid #4CAF50;
                                    padding: 1rem;
                                    margin: 0.5rem 0;
                                    border-radius: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                        <span style="color: #CCCCCC;">{row['Date']}</span>
                                        <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                                    </div>
                                    <div style="margin-bottom: 0.5rem;">
                                        <span style="background-color: rgba(76, 175, 80, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                            {row['Category']}
                                        </span>
                                    </div>
                                    <div style="color: #FFFFFF; margin-top: 0.5rem;">
                                        {row['Description']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display expense transactions
                        if not expense_df.empty:
                            st.markdown("<h4 style='font-size: 18px; color: white;'>Saídas</h4>", unsafe_allow_html=True)
                            for _, row in expense_df.iterrows():
                                st.markdown(f"""
                                <div style="
                                    background-color: #1E1E1E;
                                    border-left: 4px solid #ff4b4b;
                                    padding: 1rem;
                                    margin: 0.5rem 0;
                                    border-radius: 4px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                        <span style="color: #CCCCCC;">{row['Date']}</span>
                                        <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                                    </div>
                                    <div style="margin-bottom: 0.5rem;">
                                        <span style="background-color: rgba(255, 75, 75, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                            {row['Category']}
                                        </span>
                                    </div>
                                    <div style="color: #FFFFFF; margin-top: 0.5rem;">
                                        {row['Description']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display summary for this report
                        st.markdown(f"""
                        <div style="margin: 20px 0;">
                            <div style="margin-bottom: 15px;">
                                <span style="font-size: 20px; color: white; font-weight: 500;">Resumo:</span>
                            </div>
                            <div style="margin-bottom: 12px;">
                                <span style="font-size: 16px; color: white;">Total Entradas: </span>
                                <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(report['summary']['total_income'])}</span>
                            </div>
                            <div style="margin-bottom: 12px;">
                                <span style="font-size: 16px; color: white;">Total Saídas: </span>
                                <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(report['summary']['total_expense'])}</span>
                            </div>
                            <div style="margin-bottom: 12px;">
                                <span style="font-size: 16px; color: white;">Saldo: </span>
                                <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(abs(report['summary']['net_amount']))}</span>
                                <span style="font-size: 16px; color: white !important; font-weight: 500;">({'A entregar' if report['summary']['net_amount'] >= 0 else 'A receber'})</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info(f"{selected_user} não tem histórico de relatórios")

def show_history_tab():
    """Show the history tab with all submitted reports"""
    # Debug message
    print("DEBUG - show_history_tab function called")
    print(f"DEBUG - Session state keys: {list(st.session_state.keys())}")
    
    st.subheader("Histórico de Relatórios")
    
    if "history" not in st.session_state or not st.session_state.history:
        st.info("Não existem relatórios guardados.")
        print("DEBUG - No history found in session state")
        return

    print(f"DEBUG - Found {len(st.session_state.history)} reports in history")
    
    # Display detailed information for each report
    for report in st.session_state.history:
        print(f"DEBUG - Processing report: {report.get('number', 'Unknown')}")
        
        # Check if report has required keys
        if not all(k in report for k in ["number", "summary", "transactions"]):
            print(f"DEBUG - Report missing required keys: {list(report.keys())}")
            continue
            
        # Check if summary has required keys
        if not all(k in report["summary"] for k in ["net_amount"]):
            print(f"DEBUG - Report summary missing required keys: {list(report['summary'].keys())}")
            continue
        
        # Use just the expander without the PDF button in the regular history tab
        with st.expander(f"{report['number']} - {report['period']}"):
            # Create DataFrame from transactions
            df_transactions = create_transaction_df(report['transactions'])
            
            # Split and sort transactions by type
            income_df = df_transactions[df_transactions["Type"] == TransactionType.INCOME.value].copy()
            expense_df = df_transactions[df_transactions["Type"] == TransactionType.EXPENSE.value].copy()
            
            income_df = income_df.sort_values("Date", ascending=True)
            expense_df = expense_df.sort_values("Date", ascending=True)
            
            # Format amounts
            income_df["Amount"] = income_df["Amount"].apply(lambda x: f"R$ {float(x):.2f}")
            expense_df["Amount"] = expense_df["Amount"].apply(lambda x: f"R$ {float(x):.2f}")
            
            # Display income transactions
            if not income_df.empty:
                st.markdown("<h4 style='font-size: 18px; color: white;'>Entradas</h4>", unsafe_allow_html=True)
                for _, row in income_df.iterrows():
                    st.markdown(f"""
                    <div style="
                        background-color: #1E1E1E;
                        border-left: 4px solid #4CAF50;
                        padding: 1rem;
                        margin: 0.5rem 0;
                        border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span style="color: #CCCCCC;">{row['Date']}</span>
                            <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <span style="background-color: rgba(76, 175, 80, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                {row['Category']}
                            </span>
                        </div>
                        <div style="color: #FFFFFF; margin-top: 0.5rem;">
                            {row['Description']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display expense transactions
            if not expense_df.empty:
                st.markdown("<h4 style='font-size: 18px; color: white;'>Saídas</h4>", unsafe_allow_html=True)
                for _, row in expense_df.iterrows():
                    st.markdown(f"""
                    <div style="
                        background-color: #1E1E1E;
                        border-left: 4px solid #ff4b4b;
                        padding: 1rem;
                        margin: 0.5rem 0;
                        border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span style="color: #CCCCCC;">{row['Date']}</span>
                            <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <span style="background-color: rgba(255, 75, 75, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                {row['Category']}
                            </span>
                        </div>
                        <div style="color: #FFFFFF; margin-top: 0.5rem;">
                            {row['Description']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display summary
            st.markdown(f"""
            <div style="margin: 20px 0;">
                <div style="margin-bottom: 15px;">
                    <span style="font-size: 20px; color: white; font-weight: 500;">Resumo:</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 16px; color: white;">Total Entradas: </span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">R$ {report['summary'].get('total_income', 0):.2f}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 16px; color: white;">Total Saídas: </span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">R$ {report['summary'].get('total_expenses', 0):.2f}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 16px; color: white;">Saldo: </span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">R$ {abs(report['summary'].get('net_amount', 0)):.2f}</span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">({'A entregar' if report['summary'].get('net_amount', 0) >= 0 else 'A receber'})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_report_tab():
    """Show the report tab for submitting weekly reports"""
    # Debug message
    print("DEBUG - show_report_tab function called")
    print(f"DEBUG - Session state keys: {list(st.session_state.keys())}")
    
    # Simple title for the report tab
    st.subheader("Relatório Semanal")
    
    # Get current period dates
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date
    
    # Print date types for debugging
    print(f"DEBUG - start_date type: {type(start_date)}, value: {start_date}")
    print(f"DEBUG - end_date type: {type(end_date)}, value: {end_date}")
    
    # Ensure dates are datetime.date objects
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            try:
                start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
            except ValueError:
                print(f"DEBUG - Could not parse start_date: {start_date}")
                start_date = datetime.date.today() - datetime.timedelta(days=7)
    
    if isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            try:
                end_date = datetime.strptime(end_date, '%d/%m/%Y').date()
            except ValueError:
                print(f"DEBUG - Could not parse end_date: {end_date}")
                end_date = datetime.date.today()
    
    # Update session state with converted dates
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    
    # Display current period
    st.write(f"**Período atual:** {format_date_range(start_date, end_date)}")
    
    # Filter transactions for the current period
    period_transactions = []
    if "transactions" in st.session_state and st.session_state.transactions:
        print(f"DEBUG - Total transactions: {len(st.session_state.transactions)}")
        
        for transaction in st.session_state.transactions:
            # Check if transaction has a date key (either 'Date' or 'date')
            transaction_date = None
            if "Date" in transaction:
                transaction_date = transaction["Date"]
            elif "date" in transaction:
                transaction_date = transaction["date"]
            
            if transaction_date:
                # Convert string date to datetime.date if needed
                if isinstance(transaction_date, str):
                    try:
                        transaction_date = datetime.strptime(transaction_date, '%d/%m/%Y').date()
                    except ValueError:
                        try:
                            transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
                        except ValueError:
                            print(f"DEBUG - Could not parse date: {transaction_date}")
                            continue
                
                # Check if transaction is within the current period
                if start_date <= transaction_date <= end_date:
                    period_transactions.append(transaction)
            else:
                print(f"DEBUG - Transaction without date: {transaction}")
                # Include transactions without dates to avoid losing data
                period_transactions.append(transaction)
    
    print(f"DEBUG - Period transactions: {len(period_transactions)}")
    
    # Display transactions for the current period
    if period_transactions:
        st.write("### Transações do período")
        
        # Display transactions in a nice format
        for transaction in period_transactions:
            transaction_type = transaction.get("Type", "") or transaction.get("type", "")
            category = transaction.get("Category", "") or transaction.get("category", "")
            description = transaction.get("Description", "") or transaction.get("description", "")
            amount = transaction.get("Amount", 0) or transaction.get("amount", 0)
            date_str = transaction.get("Date", "") or transaction.get("date", "")
            
            # Format the transaction display
            if transaction_type == TransactionType.INCOME.value:
                st.markdown(f"""
                <div style='background-color: rgba(0, 128, 0, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <div><strong>Data:</strong> {date_str}</div>
                    <div><strong>Categoria:</strong> {category}</div>
                    <div><strong>Descrição:</strong> {description}</div>
                    <div><strong>Valor:</strong> R$ {amount:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: rgba(255, 0, 0, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <div><strong>Data:</strong> {date_str}</div>
                    <div><strong>Categoria:</strong> {category}</div>
                    <div><strong>Descrição:</strong> {description}</div>
                    <div><strong>Valor:</strong> R$ {amount:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Calculate summary statistics
        total_income = sum(float(t.get("Amount", 0) or t.get("amount", 0)) 
                          for t in period_transactions 
                          if (t.get("Type", "") or t.get("type", "")) == TransactionType.INCOME.value)
        
        total_expenses = sum(float(t.get("Amount", 0) or t.get("amount", 0)) 
                            for t in period_transactions 
                            if (t.get("Type", "") or t.get("type", "")) == TransactionType.EXPENSE.value)
        
        net_amount = total_income - total_expenses
        
        # Display summary
        st.write("### Resumo do período")
        st.write(f"**Total de receitas:** R$ {total_income:.2f}")
        st.write(f"**Total de despesas:** R$ {total_expenses:.2f}")
        st.write(f"**Saldo:** R$ {net_amount:.2f}")
        
        # Submit button
        if st.button("Submeter Relatório"):
            # Validate submission
            today = datetime.date.today()
            
            # Check if end date is in the future
            if end_date > today:
                st.error("Não é possível submeter relatórios para períodos futuros.")
                return
            
            # Check if end date is before a specific date (e.g., 09/02/2025)
            specific_date = datetime.date(2025, 2, 9)
            if end_date < specific_date:
                st.error(f"Não é possível submeter relatórios para períodos anteriores a {specific_date.strftime('%d/%m/%Y')}.")
                return
            
            # Generate report number
            report_number = f"REL{st.session_state.report_counter:03d}"
            
            # Create report object
            report = {
                "number": report_number,
                "period": format_date_range(start_date, end_date),
                "transactions": period_transactions,
                "summary": {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "net_amount": net_amount
                },
                "submission_date": today.strftime('%d/%m/%Y')
            }
            
            # Initialize history if it doesn't exist
            if "history" not in st.session_state:
                print("DEBUG - Initializing history list")
                st.session_state.history = []
            
            # Debug print before adding report
            print(f"DEBUG - History before adding report: {len(st.session_state.history)} items")
            print(f"DEBUG - History type: {type(st.session_state.history)}")
            
            # Append report to history
            st.session_state.history.append(report)
            
            # Debug print after adding report
            print(f"DEBUG - History after adding report: {len(st.session_state.history)} items")
            print(f"DEBUG - Report added: {report_number}")
            
            # Save history to file
            save_user_history(st.session_state.username, st.session_state.history)
            
            # Increment report counter
            st.session_state.report_counter += 1
            
            # Get next period dates
            next_start_date, next_end_date = get_next_week_dates(end_date)
            
            # Update session state with next period dates
            st.session_state.start_date = next_start_date
            st.session_state.end_date = next_end_date
            
            # Save updated dates
            save_user_dates(
                st.session_state.username, 
                st.session_state.start_date, 
                st.session_state.end_date,
                st.session_state.report_counter
            )
            
            # Auto-save all user data
            auto_save_user_data()
            
            # Show success message
            st.success(f"Relatório {report_number} submetido com sucesso!")
            
            # Force rerun to update the UI
            st.rerun()
    else:
        st.info("Não há transações para o período atual.")

def convert_to_serializable(obj):
    """Convert complex data types to JSON serializable types"""
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (pd.DataFrame)):
        return obj.to_dict('records')
    elif isinstance(obj, (np.ndarray)):
        return obj.tolist()
    elif isinstance(obj, (pd.Series)):
        return obj.to_list()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(i) for i in obj]
    else:
        return obj

if __name__ == "__main__":
    try:
        # st.write("Debug - Running in directory:", os.getcwd())
        # st.write("Debug - Files in current directory:", os.listdir())
        
        # Garantir que a senha do usuário Luis seja "1234"
        users = load_users()
        if "Luis" in users:
            users["Luis"]["password"] = hash_password("1234")
            save_users(users)
            print("Senha do usuário Luis definida como '1234'")
        
        main()
    except Exception as e:
        st.error(f"Erro na inicialização: {str(e)}")
        st.write("Traceback:", traceback.format_exc()) 
