import streamlit as st

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="MD WALLET",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd
import numpy as np
import os
import json
import re
import time
import shutil
import hashlib
import sqlite3
from datetime import datetime, timedelta, date
import base64
import io
from enum import Enum
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

# Custom CSS to fix layout issues and improve spacing
st.markdown("""
<style>
    /* Fix tabs display at the top */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        margin-top: 10px;
    }
    
    /* Make tabs more visible */
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        font-size: 15px;
        font-weight: 500;
        background-color: rgba(0, 0, 0, 0.05);
        border-radius: 4px;
        padding: 5px 10px;
    }
    
    /* Add spacing at the top of the page */
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Make metrics more visible */
    [data-testid="stMetricValue"] {
        font-size: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

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
    """Initialize the database"""
    print("DEBUG - Initializing database...")
    
    # Ensure the data directory exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Connect to database (this will create it if it doesn't exist)
    db_path = os.path.join(data_dir, "wallet.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create user_data table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        data_type TEXT NOT NULL,
        data TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, data_type)
    )
    ''')
    
    # Check if the user_data table was created successfully
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_data'")
        if c.fetchone():
            print("DEBUG - User_data table exists")
        else:
            print("ERROR - Failed to create user_data table")
    except Exception as e:
        print(f"ERROR - Exception checking user_data table: {e}")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("DEBUG - Database initialized successfully")
    
    # Also initialize the default users
    initialize_default_users()

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

def get_user_data_dir():
    """Get the directory for user data"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            print(f"ERROR - Error creating directory: {str(e)}")
    return data_dir

def get_user_dir(username):
    """Get the directory for a specific user"""
    user_dir = os.path.join(get_user_data_dir(), username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    return user_dir

def save_user_data(username, data_type, data):
    """Save user data to database and fallback to file if database fails"""
    print(f"DEBUG - Saving {data_type} for user {username}")
    print(f"DEBUG - Data being saved: {data}")
    
    try:
        # Connect to SQLite database
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        db_path = os.path.join(data_dir, "wallet.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Ensure the table exists (in case we're accessing the DB directly after a fresh install)
        c.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            data_type TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, data_type)
        )
        ''')
        
        # Convert data to JSON string
        data_json = json.dumps(data)
        
        # Check if record exists
        c.execute("SELECT COUNT(*) FROM user_data WHERE username=? AND data_type=?",
                  (username, data_type))
        count = c.fetchone()[0]
        
        if count > 0:
            # Update existing record
            c.execute("UPDATE user_data SET data=?, timestamp=CURRENT_TIMESTAMP WHERE username=? AND data_type=?",
                      (data_json, username, data_type))
        else:
            # Insert new record
            c.execute("INSERT INTO user_data (username, data_type, data) VALUES (?, ?, ?)",
                      (username, data_type, data_json))
        
        conn.commit()
        conn.close()
        print(f"DEBUG - Successfully saved {data_type} to database for user {username}")
        
        # Also save to file as a backup
        save_to_file(username, data_type, data)
        
        return True
    except Exception as e:
        print(f"DEBUG - Error saving {data_type}: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        
        # Fallback to file storage
        return save_to_file(username, data_type, data)

def save_to_file(username, data_type, data):
    """Save user data to file as fallback"""
    try:
        user_dir = get_user_dir(username)
        
        # Create user directory if it doesn't exist
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, f"{data_type}.json")
        
        # Debug info
        print(f"DEBUG - User data directory: {get_user_data_dir()}")
        print(f"DEBUG - Current working directory: {os.getcwd()}")
        print(f"DEBUG - __file__: {__file__}")
        print(f"DEBUG - Directory exists: {os.path.exists(os.path.dirname(file_path))}")
        
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        print(f"DEBUG - Successfully saved {data_type} to file for user {username}")
        
        # Additional debug for common data types
        if data_type == "transactions":
            print(f"DEBUG - Saved {len(data)} transactions for user {username}")
        elif data_type == "history":
            print(f"DEBUG - Saved {len(data)} history items for user {username}")
        elif data_type == "dates":
            start = data.get('start_date', 'unknown')
            end = data.get('end_date', 'unknown')
            print(f"DEBUG - Saved dates: {start} to {end}")
        
        return True
    except Exception as e:
        print(f"ERROR - Failed to save {data_type} to file: {str(e)}")
        return False

def load_from_file(username, data_type, default=None):
    """Load user data from file as fallback"""
    try:
        user_dir = get_user_dir(username)
        file_path = os.path.join(user_dir, f"{data_type}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"DEBUG - Successfully loaded {data_type} from file for user {username}")
            return data
        else:
            print(f"DEBUG - File not found: {file_path}")
            return default
    except Exception as e:
        print(f"ERROR - Failed to load {data_type} from file: {str(e)}")
        return default

def load_user_data(username, data_type, default=None):
    """Load user data from database and fallback to file if database fails"""
    try:
        # Connect to SQLite database
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        db_path = os.path.join(data_dir, "wallet.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Ensure the table exists
        c.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            data_type TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, data_type)
        )
        ''')
        
        # Query for data
        c.execute("SELECT data FROM user_data WHERE username=? AND data_type=?",
                  (username, data_type))
        result = c.fetchone()
        
        conn.close()
        
        if result:
            return json.loads(result[0])
        
        # Fallback to file if no result in database
        print(f"DEBUG - No {data_type} found in database for user {username}, trying file")
        return load_from_file(username, data_type, default)
    except Exception as e:
        print(f"DEBUG - Error loading {data_type} from database: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        
        # Fallback to file storage
        return load_from_file(username, data_type, default)

def save_user_transactions(username, transactions):
    """Save user transactions"""
    print(f"DEBUG - Saving transactions for user {username} with {len(transactions)} items")
    return save_user_data(username, "transactions", transactions)

def load_user_transactions(username):
    """Load user transactions"""
    return load_user_data(username, "transactions", [])

def save_user_history(username, history):
    """Save user history"""
    print(f"DEBUG - Saving history for user {username} with {len(history)} items")
    return save_user_data(username, "history", history)

def load_user_history(username):
    """Load user history"""
    return load_user_data(username, "history", [])

def save_transaction(date, transaction_type, category, description, amount):
    """Save a new transaction to the user's transaction list"""
    username = st.session_state.username
    print(f"DEBUG - Saving transaction for {username}: {category} - {description}, {amount} €")
    
    # If transactions don't exist in the session state, initialize with an empty list
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    # Create a new transaction object
    transaction = {
        "date": date.isoformat() if hasattr(date, 'isoformat') else date,
        "type": transaction_type,
        "category": category,
        "description": description,
        "amount": float(amount)
    }
    
    # Add the transaction to the session state
    st.session_state.transactions.append(transaction)
    
    # Update balance calculations
    if transaction_type == TransactionType.EXPENSE.value:
        st.session_state.total_expenses = st.session_state.get('total_expenses', 0) + float(amount)
    else:
        st.session_state.total_income = st.session_state.get('total_income', 0) + float(amount)
    
    st.session_state.net_amount = st.session_state.get('total_income', 0) - st.session_state.get('total_expenses', 0)
    
    # Save transactions to persistent storage
    save_user_transactions(username, st.session_state.transactions)
    
    # Display success message
    st.success("Transação registrada com sucesso!")
    print(f"DEBUG - Transaction saved successfully: {transaction}")
    
    return True

def save_user_dates(username, start_date, end_date, report_counter=1):
    """Save user date settings"""
    print(f"DEBUG - Saving dates for user {username}")
    
    # Convert dates to strings if they are date objects
    if isinstance(start_date, (datetime, date)):
        start_date = start_date.strftime(DATE_FORMAT)
    if isinstance(end_date, (datetime, date)):
        end_date = end_date.strftime(DATE_FORMAT)
    
    data = {
        "start_date": start_date,
        "end_date": end_date,
        "report_counter": report_counter
    }
    
    return save_user_data(username, "dates", data)

def load_user_dates(username):
    """Load user date settings"""
    dates = load_user_data(username, "dates", None)
    
    if dates:
        # Convert string dates to date objects
        try:
            if isinstance(dates["start_date"], str):
                dates["start_date"] = datetime.strptime(dates["start_date"], DATE_FORMAT).date()
            if isinstance(dates["end_date"], str):
                dates["end_date"] = datetime.strptime(dates["end_date"], DATE_FORMAT).date()
        except Exception as e:
            print(f"ERROR - Failed to parse dates: {str(e)}")
            return None
    
    return dates

# User authentication functions
def get_users_file_path():
    """Get the path to the users.json file"""
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        users_file = os.path.join(data_dir, "users.json")
        print(f"DEBUG - Users file path: {users_file}")
        return users_file
    except Exception as e:
        print(f"ERROR - Failed to get users file path: {str(e)}")
        # If all else fails, use a local path
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")

def save_users(users):
    """Save the users dictionary to a JSON file"""
    try:
        with open(get_users_file_path(), "w") as f:
            json.dump(users, f)
        return True
    except Exception as e:
        print(f"ERROR - Failed to save users: {str(e)}")
        return False

def load_users():
    """Load users from the JSON file"""
    try:
        users_file = get_users_file_path()
        if os.path.exists(users_file):
            try:
                with open(users_file, "r") as f:
                    users = json.load(f)
                return users
            except Exception as e:
                print(f"ERROR - Failed to load users from file: {str(e)}")
                pass
        
        # If file doesn't exist or there was an error, initialize with default users
        return initialize_default_users()
    except Exception as e:
        print(f"ERROR - Critical error in load_users: {str(e)}")
        # Return a minimal set of users as a last resort
        return {
            "admin": {
                "password": hash_password("admin123"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_admin": True
            }
        }

def initialize_default_users():
    """Initialize the system with default users"""
    default_users = {
        "Ângelo": {"password": hash_password("Crfsaf$1141r2"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "is_admin": True},
        "Valeríya": {"password": hash_password("Bw7$pQzX9tLm"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
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
        # Add a test user for easier login during development
        "test": {"password": hash_password("test"), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    }
    print(f"DEBUG - Initializing default users: {list(default_users.keys())}")
    save_users(default_users)
    return default_users

def hash_password(password):
    """Hash a password for storage"""
    result = hashlib.sha256(password.encode()).hexdigest()
    return result

def verify_password(stored_password, provided_password):
    """Verify the provided password against stored hash"""
    provided_hash = hash_password(provided_password)
    return stored_password == provided_hash

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
    """Authenticate a user"""
    try:
        users = load_users()
        print(f"DEBUG - Authentication attempt for user: {username}")
        print(f"DEBUG - Available users: {list(users.keys())}")
        
        if username not in users:
            print(f"DEBUG - User {username} not found")
            return False
        
        stored_password = users[username]["password"]
        provided_hash = hash_password(password)
        
        print(f"DEBUG - Stored password hash: {stored_password}")
        print(f"DEBUG - Provided password hash: {provided_hash}")
        
        result = verify_password(stored_password, password)
        print(f"DEBUG - Authentication result: {result}")
        
        return result
    except Exception as e:
        print(f"ERROR - Authentication error: {str(e)}")
        print(f"DEBUG - Authentication traceback: {traceback.format_exc()}")
        return False

def show_login_page():
    """Show the login page"""
    st.markdown("<h1 style='text-align: center;'>MD Wallet</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Sistema de Gestão de Despesas</p>", unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Nome de Usuário")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")
            
            if submit_button:
                if username and password:
                    print(f"DEBUG - Login attempt for {username}")
                    if username == "test" and password == "test":
                        # Special case for test user
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.is_admin = False
                        st.session_state.page = "main"
                        st.session_state.first_load = True
                        st.rerun()
                    elif username == "admin" and password == "admin":
                        # Special case for admin user
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.is_admin = True
                        st.session_state.page = "main"
                        st.session_state.first_load = True
                        st.rerun()
                    elif authenticate(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.is_admin = (username.lower() == "admin" or username.lower() == "ângelo")
                        st.session_state.page = "main"
                        st.session_state.first_load = True
                        st.rerun()
                    else:
                        st.error("Nome ou senha inválidos. Por favor, tente novamente.")
                else:
                    st.error("Por favor, preencha o nome de usuário e senha.")
    
    # Always show debug information about available users
    with st.expander("Debug - Usuários Disponíveis"):
        # Force-add the test user and admin user if they don't exist
        users = load_users()
        if "test" not in users:
            users["test"] = hash_password("test")
            save_users(users)
            
        if "admin" not in users and "admin".lower() not in [k.lower() for k in users.keys()]:
            users["admin"] = hash_password("admin")
            save_users(users)
            
        st.write("### Usuários disponíveis para login:")
        user_list = list(users.keys())
        for idx, user in enumerate(user_list):
            pwd = "test" if user == "test" else "admin" if user == "admin" else "senha_padrao"
            st.write(f"{idx+1}. **{user}** - Senha: `{pwd}`")
            
        st.write("#### Teste rápido:")
        st.write("- **Usuário normal**: `test` / Senha: `test`")
        st.write("- **Admin**: `admin` / Senha: `admin`")
        st.write("- **Usuário real**: `Humberto` / Senha: `G4h&FmV7cRpZ`")

def load_user_data_for_session(username):
    """Load all user data into session state"""
    # Load transactions
    transactions = load_user_transactions(username)
    st.session_state.transactions = transactions if transactions else []
    
    # Load history
    history = load_user_history(username)
    st.session_state.history = history if history else []
    
    # Load dates
    dates = load_user_dates(username)
    if dates:
        st.session_state.start_date = dates.get("start_date")
        st.session_state.end_date = dates.get("end_date")
        st.session_state.report_counter = dates.get("report_counter", 1)
    else:
        # Set default dates (current week)
        current_start, current_end = get_week_period()
        st.session_state.start_date = current_start
        st.session_state.end_date = current_end
        st.session_state.report_counter = 1
    
    # Calculate totals
    df = create_transaction_df(st.session_state.transactions)
    if not df.empty:
        summary = get_period_summary(df)
        st.session_state.total_income = summary["total_income"]
        st.session_state.total_expenses = summary["total_expenses"]
        st.session_state.net_amount = summary["net_amount"]
    else:
        st.session_state.total_income = 0
        st.session_state.total_expenses = 0
        st.session_state.net_amount = 0
    
    # Mark as loaded
    st.session_state.user_data_loaded = True

def get_week_dates(date):
    # Get Monday (start) of the week
    monday = date - timedelta(days=date.weekday())
    # Get Sunday (end) of the week
    sunday = monday + timedelta(days=6)
    return monday, sunday

def format_date_range(start_date, end_date):
    """Format a date range for display"""
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, DATE_FORMAT).date()
        except ValueError:
            start_date = datetime.now().date()
    
    if isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, DATE_FORMAT).date()
        except ValueError:
            end_date = datetime.now().date() + timedelta(days=6)
    
    # Format as dd/mm/yyyy
    return f"De {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"

def get_next_week_dates(current_end_date):
    """Get the start and end dates for the next week period"""
    next_start = current_end_date + timedelta(days=1)
    next_end = next_start + timedelta(days=6)
    return next_start, next_end

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
    """Reset the application state"""
    # If the user was logged in, save their data before clearing
    if 'username' in st.session_state and st.session_state.username:
        username = st.session_state.username
        print(f"DEBUG - Logging out user: {username}")
        
        # Save any pending transactions
        if 'transactions' in st.session_state:
            save_user_transactions(username, st.session_state.transactions)
            
        # Save history if it exists
        if 'history' in st.session_state:
            save_user_history(username, st.session_state.history)
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Initialize only the essential state variables
    st.session_state.authenticated = False
    st.session_state.page = "login"
    print("DEBUG - User logged out, session cleared")

def logout():
    """Log out the user and reset the application state"""
    reset_state()
    # Make sure we redirect to login page
    st.session_state.page = "login"
    st.session_state.authenticated = False

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
            if "meal_amount_per_person" in st.session_state:
                del st.session_state.meal_amount_per_person
            if "meal_collaborators" in st.session_state:
                del st.session_state.meal_collaborators
            if "meal_type" in st.session_state:
                del st.session_state.meal_type
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
            if "purchase_amount" in st.session_state:
                del st.session_state.purchase_amount
            if "purchase_what" in st.session_state:
                del st.session_state.purchase_what
            if "purchase_justification" in st.session_state:
                del st.session_state.purchase_justification
            if "purchase_date" in st.session_state:
                del st.session_state.purchase_date
        # Reset delivery form state if coming from delivery form
        elif st.session_state.category == ExpenseCategory.DELIVERED.value:
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
    """Show a home button for navigation back to the main page"""
    if st.button("Voltar para Início", key="home_button"):
        st.session_state.page = "main"
        st.rerun()

def show_main_page():
    """Show the main application page with tabs for different functions"""
    st.sidebar.markdown("<h1 style='text-align: center;'>MD Wallet</h1>", unsafe_allow_html=True)
    
    # Show logout button
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()
        
    # Show user info
    st.sidebar.markdown(f"**Usuário**: {st.session_state.username}")
    
    # Check if we need to redirect to a form
    if st.session_state.page == "form":
        show_form()
        return
    elif st.session_state.page == "categories":
        show_categories()
        return
        
    # Show different interfaces based on admin status
    if st.session_state.is_admin:
        show_admin_interface()
    else:
        show_user_interface()

def show_user_interface():
    """Show regular user interface with tabs"""
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Registar", "Relatório", "Histórico"])
    
    with tab1:
        show_register_tab()
    
    with tab2:
        show_report_tab()
    
    with tab3:
        show_history_tab()

def show_admin_interface():
    """Show admin interface with ability to view user data"""
    # Create tabs for admin
    tab1 = st.tabs(["Colaboradores"])
    
    with tab1[0]:
        # Get all users
        users = load_users()
        user_names = [user for user in users.keys() if user != "admin" and user != "test"]
        
        # Select user
        selected_user = st.selectbox("Selecionar colaborador:", user_names)
        
        if selected_user:
            # Create tabs for report and history
            report_tab, history_tab = st.tabs(["Relatório", "Histórico"])
            
            with report_tab:
                show_user_report_tab(selected_user)
            
            with history_tab:
                show_user_history_tab(selected_user)

def show_user_report_tab(username):
    """Show report tab for a specific user (admin view)"""
    # Load user data
    user_transactions = load_user_transactions(username)
    user_dates = load_user_dates(username)
    
    if not user_dates:
        st.warning(f"Não há dados de período para o usuário {username}")
        return
        
    start_date = datetime.strptime(user_dates["start_date"], '%Y-%m-%d').date() if isinstance(user_dates["start_date"], str) else user_dates["start_date"]
    end_date = datetime.strptime(user_dates["end_date"], '%Y-%m-%d').date() if isinstance(user_dates["end_date"], str) else user_dates["end_date"]
    
    # Show date range
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; margin-bottom: 15px; background-color: rgba(70, 70, 70, 0.1);">
        <p style="margin: 0; font-weight: bold;">Período atual: {format_date_range(start_date, end_date)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter transactions for current period
    period_transactions = []
    if user_transactions:
        for transaction in user_transactions:
            transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date() if isinstance(transaction['date'], str) else transaction['date']
            if start_date <= transaction_date <= end_date:
                period_transactions.append(transaction)
    
    # Calculate totals
    total_expenses = sum(t['amount'] for t in period_transactions if t['type'] == TransactionType.EXPENSE.value)
    total_income = sum(t['amount'] for t in period_transactions if t['type'] == TransactionType.INCOME.value)
    net_amount = total_income - total_expenses
    
    # Show metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gastos", f"{total_expenses:.2f} €", delta=None)
    with col2:
        st.metric("Entradas", f"{total_income:.2f} €", delta=None)
    with col3:
        st.metric("Saldo", f"{net_amount:.2f} €", delta=None)
    
    # Show transactions table
    if period_transactions:
        st.subheader("Transações do Período")
        df = pd.DataFrame(period_transactions)
        # Rename columns and format
        df.columns = ["Data", "Tipo", "Categoria", "Descrição", "Valor"]
        df["Data"] = pd.to_datetime(df["Data"]).dt.strftime('%d/%m/%Y')
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"Não há transações registradas para {username} neste período.")

def show_user_history_tab(username):
    """Show history tab for a specific user (admin view)"""
    # Load user history
    history = load_user_history(username)
    
    if not history:
        st.warning(f"Não há histórico para o usuário {username}")
        return
    
    st.subheader(f"Histórico de Relatórios - {username}")
    
    # Display each report in an expander
    for i, report in enumerate(history):
        with st.expander(f"{report['number']} - {report['period']} - Submetido em {report['submission_date']}"):
            col1, col2 = st.columns([0.85, 0.15])
            
            with col1:
                st.markdown(f"### {report['number']} - {report['period']}")
                st.markdown(f"**Data de Submissão:** {report['submission_date']}")
            
            with col2:
                # Add download button for PDF
                if st.button("📥 PDF", key=f"pdf_{i}", use_container_width=True):
                    generate_pdf_report(username, report)
                    
            # Show summary
            st.markdown("#### Resumo")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gastos", f"{report['summary']['total_expenses']:.2f} €")
            with col2:
                st.metric("Entradas", f"{report['summary']['total_income']:.2f} €")
            with col3:
                st.metric("Saldo", f"{report['summary']['net_amount']:.2f} €")
            
            # Show transactions
            if report['transactions']:
                st.markdown("#### Transações")
                df_report = create_transaction_df(report['transactions'])
                st.dataframe(df_report, use_container_width=True)
            else:
                st.info("Não há transações neste relatório.")

def generate_pdf_report(username, report):
    """Generate and offer download of a PDF report"""
    try:
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add title
        elements.append(Paragraph(f"Relatório {report['number']} - {report['period']}", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Colaborador: {username}", subtitle_style))
        elements.append(Paragraph(f"Data de Submissão: {report['submission_date']}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Add summary
        elements.append(Paragraph("Resumo:", subtitle_style))
        summary_data = [
            ["Métrica", "Valor"],
            ["Gastos", f"{report['summary']['total_expenses']:.2f} €"],
            ["Entradas", f"{report['summary']['total_income']:.2f} €"],
            ["Saldo", f"{report['summary']['net_amount']:.2f} €"]
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Add transactions
        if report['transactions']:
            elements.append(Paragraph("Transações:", subtitle_style))
            
            # Prepare table data
            transaction_data = [["Data", "Tipo", "Categoria", "Descrição", "Valor"]]
            
            for t in report['transactions']:
                date = t['date']
                if isinstance(date, str) and date.startswith("20"):  # ISO format
                    date = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
                
                transaction_data.append([
                    date,
                    t['type'],
                    t['category'],
                    t['description'],
                    f"{t['amount']:.2f} €"
                ])
            
            # Create the table
            transactions_table = Table(transaction_data, colWidths=[80, 70, 80, 160, 70])
            transactions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('WORDWRAP', (3, 1), (3, -1), True)  # Enable word wrapping for description
            ]))
            
            elements.append(transactions_table)
        else:
            elements.append(Paragraph("Não há transações neste relatório.", normal_style))
        
        # Build document
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Prepare download button
        import base64
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_{username}_{report["number"]}.pdf">Clique para baixar o PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")

def show_register_tab():
    """Show the registration tab"""
    # Choose expense or income
    st.write("## Registro de Transações")
    
    # Show current week
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; margin-bottom: 15px; background-color: rgba(70, 70, 70, 0.1);">
        <p style="margin: 0; font-weight: bold;">Período atual: {format_date_range(st.session_state.start_date, st.session_state.end_date)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show current balance for this week
    col1, col2, col3 = st.columns(3)
    
    # Get transactions for this week only
    week_transactions = []
    
    if 'transactions' in st.session_state and st.session_state.transactions:
        for transaction in st.session_state.transactions:
            if isinstance(transaction['date'], str):
                transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
            else:
                transaction_date = transaction['date']
                
            if st.session_state.start_date <= transaction_date <= st.session_state.end_date:
                week_transactions.append(transaction)
    
    # Calculate this week's totals
    week_expenses = sum(t['amount'] for t in week_transactions if t['type'] == TransactionType.EXPENSE.value)
    week_income = sum(t['amount'] for t in week_transactions if t['type'] == TransactionType.INCOME.value)
    week_balance = week_income - week_expenses
    
    with col1:
        st.metric(
            "Gastos", 
            f"{week_expenses:.2f} €", 
            delta=None,
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "Entradas", 
            f"{week_income:.2f} €", 
            delta=None,
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Saldo", 
            f"{week_balance:.2f} €", 
            delta=None,
            delta_color="normal" if week_balance >= 0 else "inverse"
        )
    
    # Expense or Income buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Registrar Saída 📤", use_container_width=True):
            navigate_to_categories(TransactionType.EXPENSE.value)
    
    with col2:
        if st.button("Registrar Entrada 📥", use_container_width=True):
            navigate_to_categories(TransactionType.INCOME.value)
            
    # No transaction table on the main page

def show_categories():
    """Show the categories page"""
    st.title("Selecione uma Categoria")
    
    # Add home button
    if st.button("Voltar para Início", key="home_button_categories"):
        st.session_state.page = "main"
        st.rerun()
    
    # Show categories based on transaction type
    if st.session_state.transaction_type == TransactionType.EXPENSE.value:
        for category in ExpenseCategory:
            if st.button(category.value, key=f"cat_{category.name}", use_container_width=True):
                navigate_to_form(category.value)
                st.rerun()
    else:
        for category in IncomeCategory:
            if st.button(category.value, key=f"cat_{category.name}", use_container_width=True):
                navigate_to_form(category.value)
                st.rerun()

def show_report_tab():
    """Show the report tab with transaction summary"""
    st.header("Relatório Semanal")
    
    # Create DataFrame
    df = create_transaction_df(st.session_state.transactions)
    
    # Display current period summary
    date_range = format_date_range(st.session_state.start_date, st.session_state.end_date)
    st.subheader(date_range)
    
    # Filter transactions for current period
    period_transactions = [t for t in st.session_state.transactions 
                          if (st.session_state.start_date.isoformat() <= t["date"] <= st.session_state.end_date.isoformat())]
    
    print(f"DEBUG - Period transactions: {len(period_transactions)}")
    
    # Format like the image provided
    if period_transactions:
        df_period = create_transaction_df(period_transactions)
        summary = get_period_summary(df_period)
        
        # Display transactions in the format shown in the image
        for transaction in period_transactions:
            date_str = transaction["date"].split("T")[0]
            try:
                display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m")
            except:
                display_date = date_str
                
            category = transaction["category"]
            description = transaction["description"]
            amount = transaction["amount"]
            
            border_color = "#ff4b4b" if transaction["type"] == "Saída" else "#4CAF50"
            
            st.markdown(f"""
            <div style="
                background-color: #121212;
                border-left: 4px solid {border_color};
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>{display_date}</span>
                    <span>€{amount:.2f}</span>
                </div>
                <div style="
                    background-color: rgba{border_color.replace('#', '(')},.2);
                    display: inline-block;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;">
                    {category}
                </div>
                <div>{description}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show summary at the bottom
        st.markdown("### Resumo:")
        st.markdown(f"Total Entradas: €{summary['total_income']:.2f}")
        st.markdown(f"Total Saídas: €{summary['total_expenses']:.2f}")
        
        # Display balance with appropriate label
        balance = summary["net_amount"]
        balance_abs = abs(balance)
        status = "a entregar" if balance >= 0 else "a receber"
        
        st.markdown(f"Saldo: €{balance_abs:.2f} ({status})")
        
        # Submit report button
        if st.button("Submeter Relatório", key="submit_report", use_container_width=True):
            submit_report()
    else:
        # Show summary metrics with zeros when no transactions
        st.info("Não há transações registradas para este período. Adicione transações na aba 'Registar'.")
        
        # Show zero summary
        st.markdown("### Resumo:")
        st.markdown("Total Entradas: €0.00")
        st.markdown("Total Saídas: €0.00")
        st.markdown("Saldo: €0.00 (a entregar)")
        
        # Disable submit report button when no transactions
        st.button("Submeter Relatório", key="submit_report", disabled=True, use_container_width=True)

def submit_report():
    """Submit the current week's report and prepare for next week"""
    # Create a report with the current transactions
    report_number = f"Relatório {st.session_state.report_counter}"
    
    # Get only transactions for the current period
    period_transactions = []
    for transaction in st.session_state.transactions:
        if isinstance(transaction['date'], str):
            transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
        else:
            transaction_date = transaction['date']
            
        if st.session_state.start_date <= transaction_date <= st.session_state.end_date:
            period_transactions.append(transaction)
    
    period_df = create_transaction_df(period_transactions)
    period_summary = get_period_summary(period_df)
    
    # Format dates for display
    period_text = format_date_range(st.session_state.start_date, st.session_state.end_date)
    
    # Create report object
    report = {
        "number": report_number,
        "period": period_text,
        "transactions": period_transactions,
        "summary": period_summary,
        "submission_date": datetime.now().strftime("%d/%m/%Y")
    }
    
    # Initialize history list if it doesn't exist
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    # Add report to history
    st.session_state.history.append(report)
    
    # Save history to persistent storage
    save_user_history(st.session_state.username, st.session_state.history)
    
    # Remove the submitted transactions from the current list
    st.session_state.transactions = [t for t in st.session_state.transactions if t not in period_transactions]
    
    # Update date ranges for the next period
    next_start_date, next_end_date = get_next_week_dates(st.session_state.end_date)
    st.session_state.start_date = next_start_date
    st.session_state.end_date = next_end_date
    st.session_state.report_counter += 1
    
    # Save the new dates
    save_user_dates(st.session_state.username, st.session_state.start_date, st.session_state.end_date, st.session_state.report_counter)
    
    # Save the updated transactions
    save_user_transactions(st.session_state.username, st.session_state.transactions)
    
    # Inform the user
    st.success(f"Relatório {report_number} enviado com sucesso!")
    st.rerun()

def show_history_tab():
    """Show the history tab with past reports"""
    st.write("## Histórico de Relatórios")
    
    # Check if there's history data
    if 'history' not in st.session_state or not st.session_state.history:
        st.info("Você ainda não tem relatórios submetidos.")
        return
        
    history = st.session_state.history
    
    # Display each report in an expander
    for report in history:
        with st.expander(f"{report['number']} - {report['period']} - Enviado em {report['submission_date']}"):
            # Show report details
            st.markdown(f"### {report['number']} - {report['period']}")
            st.markdown(f"**Data de Submissão:** {report['submission_date']}")
            
            # Show summary
            st.markdown("#### Resumo")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gastos", f"{report['summary']['total_expenses']:.2f} €")
            with col2:
                st.metric("Entradas", f"{report['summary']['total_income']:.2f} €")
            with col3:
                st.metric("Saldo", f"{report['summary']['net_amount']:.2f} €")
            
            # Show transactions
            if report['transactions']:
                st.markdown("#### Transações")
                df_report = create_transaction_df(report['transactions'])
                st.dataframe(df_report, use_container_width=True)
            else:
                st.info("Não há transações neste relatório.")

def show_form():
    """Show the appropriate form based on the form type"""
    # Add home button
    if st.button("Voltar para Início", key="home_button_form"):
        st.session_state.page = "main"
        st.rerun()
        
    form_type = st.session_state.category
    
    if form_type == ExpenseCategory.MEAL.value:
        show_meal_form()
    elif form_type == ExpenseCategory.HR.value:
        show_hr_form()
    elif form_type == ExpenseCategory.PURCHASE.value:
        show_purchase_form()
    elif form_type == ExpenseCategory.DELIVERED.value:
        show_delivered_form()
    elif form_type == IncomeCategory.SERVICE.value:
        show_service_form()
    elif form_type == IncomeCategory.RECEIVED.value:
        show_received_form()
    else:
        st.error(f"Tipo de formulário desconhecido: {form_type}")

def show_meal_form():
    """Show the meal expense form"""
    st.title("Refeição")
    
    # Initialize state variables if they don't exist
    if 'meal_amount_per_person' not in st.session_state:
        st.session_state.meal_amount_per_person = 0.0
    if 'meal_collaborators' not in st.session_state:
        st.session_state.meal_collaborators = [""] * 10  # Allocate 10 slots for collaborators
    if 'meal_type' not in st.session_state:
        st.session_state.meal_type = ""
        
    # Define update callbacks
    def update_amount(val):
        st.session_state.meal_amount_per_person = val
        
    def update_collab(i, val):
        collaborators = st.session_state.meal_collaborators.copy()
        collaborators[i] = val
        st.session_state.meal_collaborators = collaborators
        
    def update_meal_type(val):
        st.session_state.meal_type = val
    
    with st.form("meal_form", clear_on_submit=False):
        # Date must be within the current week
        date = st.date_input(
            "Data",
            value=datetime.now().date(),
            min_value=st.session_state.start_date,
            max_value=st.session_state.end_date
        )
        
        # Meal type
        meal_type = st.selectbox(
            "Tipo de Refeição",
            ["", "Almoço", "Jantar", "Coffee Break", "Outro"],
            key="meal_type_select",
            on_change=update_meal_type,
            args=(st.session_state.meal_type,)
        )
        
        # Amount per person
        amount_per_person = st.number_input(
            "Valor por Pessoa (€)",
            min_value=0.0,
            step=0.5,
            format="%.2f",
            key="meal_amount_input",
            on_change=update_amount,
            args=(st.session_state.meal_amount_per_person,)
        )
        
        # Collaborator inputs (dynamic up to 10)
        st.write("Participantes:")
        
        # Create a 2-column layout for collaborators
        cols = st.columns(2)
        for i in range(10):
            with cols[i % 2]:
                st.text_input(
                    f"Colaborador {i+1}",
                    value=st.session_state.meal_collaborators[i],
                    key=f"collab_{i}",
                    on_change=update_collab,
                    args=(i, st.session_state.meal_collaborators[i])
                )
        
        # Calculate and display the result in real-time
        valid_collaborators = [c for c in st.session_state.meal_collaborators if c]
        num_collaborators = len(valid_collaborators)
        
        amount = amount_per_person * num_collaborators if num_collaborators > 0 else 0
        
        # Format the display of collaborators
        if valid_collaborators:
            collaborator_text = ", ".join(valid_collaborators)
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Participantes: {num_collaborators}</p>
                <p style="margin-bottom: 5px;">Nomes: {collaborator_text}</p>
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: {amount:.2f} €</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Participantes: 0</p>
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: 0.00 €</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Submit button
        submit = st.form_submit_button("Submeter")
        
        if submit:
            if amount > 0 and num_collaborators > 0 and meal_type:
                # Create a description with meal type and collaborators
                collaborator_text = ", ".join(valid_collaborators)
                description = f"{meal_type} com {num_collaborators} pessoas: {collaborator_text}"
                
                # Save transaction
                save_transaction(date, TransactionType.EXPENSE.value, ExpenseCategory.MEAL.value, description, amount)
                
                # Reset form
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente")

def show_hr_form():
    """Show the HR expense form"""
    st.title("Recursos Humanos")
    
    # Initialize state variables if they don't exist
    if 'hr_collaborator_name' not in st.session_state:
        st.session_state.hr_collaborator_name = ""
    if 'hr_role' not in st.session_state:
        st.session_state.hr_role = ""
        
    # Define update callbacks
    def update_name(val):
        st.session_state.hr_collaborator_name = val
        
    def update_role(val):
        st.session_state.hr_role = val
    
    with st.form("hr_form", clear_on_submit=False):
        # Date must be within the current week
        date = st.date_input(
            "Data",
            value=datetime.now().date(),
            min_value=st.session_state.start_date,
            max_value=st.session_state.end_date
        )
        
        # HR details
        collaborator_name = st.text_input(
            "Nome do Colaborador",
            key="hr_name_input",
            on_change=update_name,
            args=(st.session_state.hr_collaborator_name,)
        )
        
        role = st.selectbox(
            "Função", 
            [""] + list(HR_RATES.keys()),
            key="hr_role_select",
            on_change=update_role,
            args=(st.session_state.hr_role,)
        )
        
        # Calculate and display the result in real-time
        if role and role in HR_RATES:
            amount = HR_RATES[role]
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: {amount:.2f} €</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: 0.00 €</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Submit button
        submit = st.form_submit_button("Submeter")
        
        if submit:
            if collaborator_name and role and role in HR_RATES:
                amount = HR_RATES[role]
                description = f"{collaborator_name} - {role} (Taxa: €{amount:.2f})"
                save_transaction(date, TransactionType.EXPENSE.value, ExpenseCategory.HR.value, description, amount)
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente")

def show_purchase_form():
    """Show the purchase expense form"""
    st.title("Compra")
    
    # Initialize state variables if they don't exist
    if 'purchase_amount' not in st.session_state:
        st.session_state.purchase_amount = 0.0
    if 'purchase_what' not in st.session_state:
        st.session_state.purchase_what = ""
    if 'purchase_justification' not in st.session_state:
        st.session_state.purchase_justification = ""
        
    # Define update callbacks
    def update_amount(val):
        st.session_state.purchase_amount = val
        
    def update_what(val):
        st.session_state.purchase_what = val
        
    def update_justification(val):
        st.session_state.purchase_justification = val
    
    with st.form("purchase_form"):
        # Date must be within the current week
        date = st.date_input(
            "Data",
            value=datetime.now().date(),
            min_value=st.session_state.start_date,
            max_value=st.session_state.end_date
        )
        
        # Purchase details
        what = st.text_input(
            "O quê?",
            key="purchase_what_input",
            on_change=update_what,
            args=(st.session_state.purchase_what,)
        )
        
        justification = st.text_area(
            "Justificação",
            key="purchase_justification_input",
            on_change=update_justification,
            args=(st.session_state.purchase_justification,)
        )
        
        amount = st.number_input(
            "Valor (€)", 
            min_value=0.0, 
            step=0.5,
            key="purchase_amount_input",
            on_change=update_amount,
            args=(st.session_state.purchase_amount,)
        )
        
        # Display result in real-time
        if st.session_state.purchase_amount > 0:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: {st.session_state.purchase_amount:.2f} €</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: 0.00 €</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Submit button
        submit = st.form_submit_button("Submeter")
        
        if submit:
            if amount > 0 and what and justification:
                description = f"{what}: {justification}"
                save_transaction(date, TransactionType.EXPENSE.value, ExpenseCategory.OTHER.value, description, amount)
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente")

def show_delivered_form():
    """Show the delivered expense form"""
    st.title("Entreguei")
    
    with st.form("delivered_form"):
        # Date must be within the current week
        date = st.date_input(
            "Data",
            value=datetime.now().date(),
            min_value=st.session_state.start_date,
            max_value=st.session_state.end_date
        )
        
        # Delivered details
        recipient = st.text_input("Para quem?")
        justification = st.text_area("Justificação")
        amount = st.number_input("Valor (€)", min_value=0.0, step=0.5)
        
        # Display result field (even if zero)
        result_placeholder = st.empty()
        
        if amount > 0:
            result_placeholder.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: {amount:.2f} €</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            result_placeholder.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: 0.00 €</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Submit button
        submit = st.form_submit_button("Submeter")
        
        if submit:
            if amount > 0 and recipient and justification:
                description = f"{recipient}: {justification}"
                save_transaction(date, TransactionType.EXPENSE.value, ExpenseCategory.DELIVERED.value, description, amount)
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente")

def show_service_form():
    """Show the service income form"""
    st.title("Serviço")
    
    with st.form("service_form"):
        # Date must be within the current week
        date = st.date_input(
            "Data",
            value=datetime.now().date(),
            min_value=st.session_state.start_date,
            max_value=st.session_state.end_date
        )
        
        # Service details
        client = st.text_input("Cliente")
        service_description = st.text_area("Descrição do serviço")
        amount = st.number_input("Valor (€)", min_value=0.0, step=0.5)
        
        # Display result field (even if zero)
        result_placeholder = st.empty()
        
        if amount > 0:
            result_placeholder.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: {amount:.2f} €</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            result_placeholder.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: 0.00 €</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Submit button
        submit = st.form_submit_button("Submeter")
        
        if submit:
            if amount > 0 and client and service_description:
                description = f"{client}: {service_description}"
                save_transaction(date, TransactionType.INCOME.value, IncomeCategory.SERVICE.value, description, amount)
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente")

def show_received_form():
    """Show the received income form"""
    st.title("Recebi")
    
    with st.form("received_form"):
        # Date must be within the current week
        date = st.date_input(
            "Data",
            value=datetime.now().date(),
            min_value=st.session_state.start_date,
            max_value=st.session_state.end_date
        )
        
        # Received details
        source = st.text_input("De quem?")
        reason = st.text_area("Motivo")
        amount = st.number_input("Valor (€)", min_value=0.0, step=0.5)
        
        # Display result field (even if zero)
        result_placeholder = st.empty()
        
        if amount > 0:
            result_placeholder.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: {amount:.2f} €</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            result_placeholder.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: transparent;">
                <p style="margin-bottom: 5px; font-weight: bold;">Valor Total: 0.00 €</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Submit button
        submit = st.form_submit_button("Submeter")
        
        if submit:
            if amount > 0 and source and reason:
                description = f"{source}: {reason}"
                save_transaction(date, TransactionType.INCOME.value, IncomeCategory.RECEIVED.value, description, amount)
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente")

def main():
    """Main application function"""
    # Database is initialized early
    init_db()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state variables if they don't exist
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if 'page' not in st.session_state:
        st.session_state.page = "login"
        
    if 'first_load' not in st.session_state:
        st.session_state.first_load = True
        
    try:
        # Main application flow
        if not st.session_state.authenticated:
            # Show login page
            show_login_page()
        else:
            # Initialize user data if first load
            if st.session_state.first_load:
                load_user_data_for_session(st.session_state.username)
                st.session_state.first_load = False
                
            # Show main page or specific form/category page
            if st.session_state.page == "main":
                show_main_page()
            elif st.session_state.page == "form":
                show_form()
            elif st.session_state.page == "categories":
                show_categories()
            
            # Auto-save user data periodically
            if 'username' in st.session_state and st.session_state.username:
                auto_save_user_data(st.session_state.username)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        print(f"ERROR - Exception in main: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 
