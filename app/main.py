import streamlit as st
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

# Page config
st.set_page_config(
    page_title="MD Wallet - Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# CRITICAL: Always reset authentication state when the script loads
# This is essential for both local and cloud deployments
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data_loaded' not in st.session_state:
    st.session_state.user_data_loaded = False

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
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                st.write(f"Attempting login for user: {username}")
                
                if authenticate(username, password):
                    st.success(f"Login successful! Welcome, {username}!")
                    
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.is_admin = username == "admin"
                    
                    print(f"DEBUG - Login successful for user: {username}")
                    print(f"DEBUG - Is admin: {st.session_state.is_admin}")
                    
                    # Load user data
                    print(f"DEBUG - Loading user data for: {username}")
                    
                    if "transactions" not in st.session_state:
                        print("DEBUG - Loading transactions")
                        st.session_state.transactions = load_user_transactions(username)
                        print(f"DEBUG - Loaded {len(st.session_state.transactions)} transactions")
                    
                    if "history" not in st.session_state:
                        print("DEBUG - Loading history")
                        st.session_state.history = load_user_history(username)
                        print(f"DEBUG - Loaded {len(st.session_state.history)} history items")
                    
                    if "history" not in st.session_state:
                        st.session_state.history = []
                
                    st.session_state.user_data_loaded = True
                    print("DEBUG - User data loaded flag set to True")
                
                    # Show updated session state
                    # st.write("Debug - Updated session state:", {k: v for k, v in st.session_state.items() if k not in ['login_password']})
                
                    # Force rerun to show the main app
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")

def get_week_dates(date):
    # Get Monday (start) of the week
    monday = date - timedelta(days=date.weekday())
    # Get Sunday (end) of the week
    sunday = monday + timedelta(days=6)
    return monday, sunday

def format_date_range(start_date, end_date):
    return f"De {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"

def get_next_week_dates(current_end_date):
    next_monday = current_end_date + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)
    return next_monday, next_sunday

def is_submission_late(end_date):
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
    # Debug message
    st.write("DEBUG: show_main_page function called")
    
    # Center the title without icon
    st.markdown(f"""
        <h1 style="text-align: center; margin-bottom: 10px;">DYNAMIC WALLET</h1>
        <div style="text-align: center; font-size: 16px; color: #888888; margin-bottom: 40px;">
            {format_date_range(st.session_state.current_start_date, st.session_state.current_end_date)}
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
    if is_submission_late(st.session_state.current_end_date):
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
    # Back button in categories
    st.markdown('<div class="corner-button">', unsafe_allow_html=True)
    if st.button("← Voltar", key="back_button"):
        navigate_back()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("Selecione a Categoria")
    
    categories = (
        [cat.value for cat in ExpenseCategory] 
        if st.session_state.transaction_type == TransactionType.EXPENSE.value
        else [cat.value for cat in IncomeCategory]
    )
    
    # Add custom CSS for category buttons
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            margin: 2px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display category buttons
    for idx, category in enumerate(categories):
        if st.button(category, key=f"category_{idx}", use_container_width=True):
            navigate_to_form(category)

def show_form():
    # Add global CSS for amount display in forms
    st.markdown("""
        <style>
        .amount-title {
            color: #FFFFFF;
            text-align: center;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .amount-container {
            background-color: #262730;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            text-align: center;
        }
        .amount-container .value {
            color: #FFFFFF;
            font-size: 24px;
            font-weight: 500;
            margin-bottom: 5px;
        }
        .amount-container .status {
            color: #888888;
            font-size: 16px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Back button in form
    st.markdown('<div class="corner-button">', unsafe_allow_html=True)
    if st.button("← Voltar para Categorias", key="back_to_categories"):
        navigate_back()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader(f"{'Saída' if st.session_state.transaction_type == TransactionType.EXPENSE.value else 'Entrada'} - {st.session_state.category}")
    
    if st.session_state.category == ExpenseCategory.MEAL.value:
        # Initialize session state for meal form
        if "meal_total_amount" not in st.session_state:
            st.session_state.meal_total_amount = 0.0
        if "meal_num_people" not in st.session_state:
            st.session_state.meal_num_people = 1
        if "collaborator_names" not in st.session_state:
            st.session_state.collaborator_names = [""]
        if "meal_date" not in st.session_state:
            st.session_state.meal_date = st.session_state.current_start_date
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.meal_date,
            min_value=st.session_state.current_start_date,
            max_value=st.session_state.current_end_date,
            key="meal_date_input"
        )
        if selected_date != st.session_state.meal_date:
            st.session_state.meal_date = selected_date
            st.rerun()
        
        # Create two columns for the main inputs
        col1, col2 = st.columns(2)
        
        with col1:
            new_total_amount = st.number_input(
                "Valor da Fatura (€)", 
                min_value=0.0, 
                step=0.5,
                value=st.session_state.meal_total_amount,
                key="total_amount_input"
            )
            if new_total_amount != st.session_state.meal_total_amount:
                st.session_state.meal_total_amount = new_total_amount
                st.rerun()
        
        with col2:
            new_num_people = st.number_input(
                "Número de Colaboradores", 
                min_value=1, 
                step=1,
                value=st.session_state.meal_num_people,
                key="num_people_input"
            )
            if new_num_people != st.session_state.meal_num_people:
                st.session_state.meal_num_people = new_num_people
                # Update collaborator names list
                if len(st.session_state.collaborator_names) < new_num_people:
                    st.session_state.collaborator_names.extend([""] * (new_num_people - len(st.session_state.collaborator_names)))
                else:
                    st.session_state.collaborator_names = st.session_state.collaborator_names[:new_num_people]
                st.rerun()
        
        meal_type = st.selectbox("Tipo", [meal.value for meal in MealType])
        
        # Collaborator name fields
        for i in range(st.session_state.meal_num_people):
            st.session_state.collaborator_names[i] = st.text_input(
                f"Colaborador {i+1}", 
                value=st.session_state.collaborator_names[i],
                key=f"collaborator_{i}"
            )
        
        # Create description with collaborator names
        names_str = ", ".join(st.session_state.collaborator_names) if all(st.session_state.collaborator_names) else f"{st.session_state.meal_num_people} colaboradores"
        description = f"{meal_type} com {names_str} (Fatura: {format_currency(st.session_state.meal_total_amount)})"

        # Add more spacing after collaborator fields
        st.write("")
        st.write("")
        st.write("")
        
        # Calculate and always display amount for meals
        calculated_amount = 0
        if st.session_state.meal_total_amount > 0 and st.session_state.meal_num_people > 0:
            calculated_amount, _ = calculate_meal_expense(
                st.session_state.meal_total_amount, 
                st.session_state.meal_num_people, 
                meal_type
            )
        
        st.markdown('<div class="amount-title">Valor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="amount-container">
            <div class="value">{format_currency(calculated_amount)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_meal", use_container_width=True):
                # Validate all fields are filled
                validation_error = None
                if st.session_state.meal_total_amount <= 0:
                    validation_error = "Por favor, insira um valor válido para a fatura"
                elif not all(name.strip() for name in st.session_state.collaborator_names):
                    validation_error = "Por favor, preencha os nomes de todos os colaboradores"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    amount, error = calculate_meal_expense(
                        st.session_state.meal_total_amount, 
                        st.session_state.meal_num_people, 
                        meal_type
                    )
                    if not error:
                        description = f"{meal_type} com {names_str} (Fatura: {format_currency(st.session_state.meal_total_amount)})"
                        save_transaction(
                            st.session_state.meal_date,
                            TransactionType.EXPENSE.value, 
                            ExpenseCategory.MEAL.value, 
                            description, 
                            amount
                        )
                        st.success("Transação registrada com sucesso!")
                        # Reset form state
                        del st.session_state.meal_total_amount
                        del st.session_state.meal_num_people
                        del st.session_state.collaborator_names
                        del st.session_state.meal_date
                        st.session_state.page = "main"
                        st.rerun()
                    else:
                        st.error(error)
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.category == ExpenseCategory.HR.value:
        # Initialize session state for HR form
        if "hr_role" not in st.session_state:
            st.session_state.hr_role = ""
        if "hr_collaborator" not in st.session_state:
            st.session_state.hr_collaborator = ""
        if "hr_date" not in st.session_state:
            st.session_state.hr_date = st.session_state.current_start_date
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.hr_date,
            min_value=st.session_state.current_start_date,
            max_value=st.session_state.current_end_date,
            key="hr_date_input"
        )
        if selected_date != st.session_state.hr_date:
            st.session_state.hr_date = selected_date
            st.rerun()
        
        # Collaborator name field
        new_collaborator = st.text_input(
            "Nome do Colaborador",
            value=st.session_state.hr_collaborator,
            key="hr_collaborator_input"
        )
        if new_collaborator != st.session_state.hr_collaborator:
            st.session_state.hr_collaborator = new_collaborator
            st.rerun()
        
        # Role selection
        new_role = st.selectbox(
            "Função",
            options=list(HR_RATES.keys()),
            key="hr_role_input"
        )
        if new_role != st.session_state.hr_role:
            st.session_state.hr_role = new_role
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Calculate and always display amount for HR
        amount = HR_RATES.get(st.session_state.hr_role, 0)
        st.markdown('<div class="amount-title">Valor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="amount-container">
            <div class="value">{format_currency(amount)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_hr", use_container_width=True):
                # Validate fields
                validation_error = None
                if not st.session_state.hr_collaborator.strip():
                    validation_error = "Por favor, insira o nome do colaborador"
                elif not st.session_state.hr_role:
                    validation_error = "Por favor, selecione uma função"
                elif HR_RATES[st.session_state.hr_role] <= 0:
                    validation_error = "Por favor, selecione uma função válida"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"{st.session_state.hr_collaborator} - {st.session_state.hr_role} (Taxa: {format_currency(HR_RATES[st.session_state.hr_role])})"
                    save_transaction(
                        st.session_state.hr_date,
                        TransactionType.EXPENSE.value,
                        ExpenseCategory.HR.value,
                        description,
                        HR_RATES[st.session_state.hr_role]
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.hr_role
                    del st.session_state.hr_collaborator
                    del st.session_state.hr_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.category == ExpenseCategory.OTHER.value:
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

def save_user_transactions(username, transactions):
    """Save user transactions to a JSON file"""
    if not username:
        print("DEBUG - No username provided, skipping save_user_transactions")
        return
    
    user_dir = get_user_dir(username)
    transactions_file = os.path.join(user_dir, "transactions.json")
    print(f"DEBUG - Saving transactions to: {transactions_file}")
    print(f"DEBUG - Number of transactions: {len(transactions)}")
    
    # Converter todos os valores numpy antes da serialização
    transactions_converted = convert_to_serializable(transactions)
    
    try:
        with open(transactions_file, "w") as f:
            json.dump(transactions_converted, f)
        print(f"DEBUG - Successfully saved transactions to: {transactions_file}")
    except Exception as e:
        print(f"DEBUG - Error saving transactions: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")

def save_user_dates(username, start_date, end_date, report_counter=1):
    """Save user date range and report counter to a JSON file"""
    if not username:
        return
    
    user_dir = get_user_dir(username)
    dates_file = os.path.join(user_dir, "dates.json")
    
    dates_data = {
        "start_date": start_date,
        "end_date": end_date,
        "report_counter": report_counter
    }
    
    # Converter todos os valores para tipos serializáveis
    dates_data_converted = convert_to_serializable(dates_data)
    
    with open(dates_file, "w") as f:
        json.dump(dates_data_converted, f)

def load_user_dates(username):
    """Load user date range and report counter from a JSON file"""
    if not username:
        return None
    
    user_dir = get_user_dir(username)
    dates_file = os.path.join(user_dir, "dates.json")
    
    dates_data = safe_load_json(dates_file, "corrupted_dates")
    if dates_data:
        # Convert string dates back to datetime objects
        try:
            # Tenta diferentes formatos de data
            start_date_str = dates_data["start_date"]
            end_date_str = dates_data["end_date"]
            
            # Tenta primeiro o formato padrão
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                # Se falhar, verifica se já é um objeto datetime
                if isinstance(start_date_str, (datetime, date)):
                    start_date = start_date_str
                else:
                    print(f"Formato de data inválido para start_date: {start_date_str}")
                    start_date = datetime.now().date()
            
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                # Se falhar, verifica se já é um objeto datetime
                if isinstance(end_date_str, (datetime, date)):
                    end_date = end_date_str
                else:
                    print(f"Formato de data inválido para end_date: {end_date_str}")
                    end_date = datetime.now().date() + timedelta(days=7)
            
            report_counter = int(dates_data.get("report_counter", 1))
            return start_date, end_date, report_counter
        except Exception as e:
            print(f"Error converting dates: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
    
    return None

def safe_load_json(file_path, backup_prefix, default_value=None):
    """Safely load JSON data from a file with error handling"""
    if default_value is None:
        default_value = []
        
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return default_value
        
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            print(f"Arquivo carregado com sucesso: {file_path}")
            return data
    except json.JSONDecodeError as e:
        # Log the error
        print(f"Erro ao carregar arquivo JSON {file_path}: {str(e)}")
        
        # Backup the corrupted file
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        backup_file = os.path.join(dir_path, f"{backup_prefix}_{file_name}_{int(time.time())}")
        try:
            shutil.copy2(file_path, backup_file)
            print(f"Backup do arquivo corrompido criado: {backup_file}")
        except Exception as backup_error:
            print(f"Erro ao criar backup: {str(backup_error)}")
        
        # Create a new empty file
        try:
            with open(file_path, "w") as f:
                json.dump(default_value, f)
            print(f"Novo arquivo vazio criado: {file_path}")
        except Exception as write_error:
            print(f"Erro ao criar novo arquivo: {str(write_error)}")
        
        return default_value
    except Exception as e:
        print(f"Erro desconhecido ao carregar arquivo JSON {file_path}: {str(e)}")
        return default_value

def load_user_transactions(username):
    """Load user transactions from a JSON file"""
    if not username:
        print("DEBUG - No username provided, skipping load_user_transactions")
        return []
    
    user_dir = get_user_dir(username)
    transactions_file = os.path.join(user_dir, "transactions.json")
    print(f"DEBUG - Loading transactions from: {transactions_file}")
    print(f"DEBUG - File exists: {os.path.exists(transactions_file)}")
    
    if os.path.exists(transactions_file):
        try:
            with open(transactions_file, "r") as f:
                transactions = json.load(f)
            print(f"DEBUG - Successfully loaded {len(transactions)} transactions")
            return transactions
        except Exception as e:
            print(f"DEBUG - Error loading transactions: {str(e)}")
            print(f"DEBUG - Traceback: {traceback.format_exc()}")
    
    print("DEBUG - No transactions file found, returning empty list")
    return []

def load_user_history(username):
    """Load user history from a JSON file"""
    if not username:
        print("DEBUG - No username provided, skipping load_user_history")
        return []
    
    user_dir = get_user_dir(username)
    history_file = os.path.join(user_dir, "history.json")
    print(f"DEBUG - Loading history from: {history_file}")
    print(f"DEBUG - File exists: {os.path.exists(history_file)}")
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
            print(f"DEBUG - Successfully loaded {len(history)} history items")
            return history
        except Exception as e:
            print(f"DEBUG - Error loading history: {str(e)}")
            print(f"DEBUG - Traceback: {traceback.format_exc()}")
    
    print("DEBUG - No history file found, returning empty list")
    return []

def save_user_history(username, history):
    """Save user history to a JSON file"""
    if not username:
        print("DEBUG - No username provided, skipping save_user_history")
        return
    
    user_dir = get_user_dir(username)
    history_file = os.path.join(user_dir, "history.json")
    print(f"DEBUG - Saving history to: {history_file}")
    print(f"DEBUG - Number of history items: {len(history)}")
    
    # Converter todos os valores numpy antes da serialização
    history_converted = convert_to_serializable(history)
    
    try:
        with open(history_file, "w") as f:
            json.dump(history_converted, f)
        print(f"DEBUG - Successfully saved history to: {history_file}")
    except Exception as e:
        print(f"DEBUG - Error saving history: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")

def generate_pdf_report(username, report_data):
    """Generate a PDF report for a user's expense report"""
    # Create a BytesIO object to store the PDF
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
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
    
    summary_table = Table(summary_data, colWidths=[300, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, -1), (1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
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
                t['Date'],
                t['Type'],
                t['Category'],
                t['Description'],
                format_currency(t['Amount'])
            ])
        
        # Create the table
        transaction_table = Table(transaction_data, colWidths=[80, 80, 100, 160, 80])
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
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
              width: 32px; height: 32px; background-color: #4CAF50; 
              border-radius: 4px; transition: all 0.3s; text-decoration: none;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" fill="white"/>
        </svg>
    </a>
    '''
    return href

def auto_save_user_data():
    """Automatically save user data if authenticated"""
    if st.session_state.get("authenticated", False) and st.session_state.get("username"):
        try:
            if hasattr(st.session_state, "transactions"):
                save_user_transactions(st.session_state.username, st.session_state.transactions)
                print(f"Transações salvas para o usuário {st.session_state.username}")
            
            if hasattr(st.session_state, "history"):
                save_user_history(st.session_state.username, st.session_state.history)
                print(f"Histórico salvo para o usuário {st.session_state.username}")
            
            # Save current date range and report counter
            if hasattr(st.session_state, "current_start_date") and hasattr(st.session_state, "current_end_date"):
                save_user_dates(
                    st.session_state.username, 
                    st.session_state.current_start_date, 
                    st.session_state.current_end_date,
                    st.session_state.get("report_counter", 1)
                )
                print(f"Datas e contador de relatórios salvos para o usuário {st.session_state.username}")
        except Exception as e:
            print(f"Error in auto-save: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

def main():
    # Debug: Show current authentication state
    # st.write(f"Debug - Authenticated: {st.session_state.get('authenticated', False)}")
    # st.write(f"Debug - Username: {st.session_state.get('username', 'None')}")
    
    # Initialize session state variables if they don't exist
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "first_load" not in st.session_state:
        st.session_state.first_load = True
        
    # Debug: Print session state keys
    print(f"Session state keys: {list(st.session_state.keys())}")
    
    # If not authenticated, show login page
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # User is authenticated, show the app
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    
    # Add logout button
    if st.sidebar.button("Logout"):
        # Save user data before logging out
        print(f"DEBUG - Logout initiated for user: {st.session_state.username}")
        print(f"DEBUG - Session state before logout: {list(st.session_state.keys())}")
        
        try:
            if "transactions" in st.session_state:
                print(f"DEBUG - Saving {len(st.session_state.transactions)} transactions before logout")
                save_user_transactions(st.session_state.username, st.session_state.transactions)
            else:
                print("DEBUG - No transactions in session state to save")
                
            if "history" in st.session_state:
                print(f"DEBUG - Saving {len(st.session_state.history)} history items before logout")
                save_user_history(st.session_state.username, st.session_state.history)
            else:
                print("DEBUG - No history in session state to save")
                
            if "current_start_date" in st.session_state and "current_end_date" in st.session_state:
                print(f"DEBUG - Saving dates before logout: {st.session_state.current_start_date} to {st.session_state.current_end_date}")
                save_user_dates(
                    st.session_state.username, 
                    st.session_state.current_start_date, 
                    st.session_state.current_end_date,
                    st.session_state.get("report_counter", 1)
                )
        except Exception as e:
            print(f"DEBUG - Error saving data during logout: {str(e)}")
            print(f"DEBUG - Traceback: {traceback.format_exc()}")
            st.sidebar.error(f"Error saving data: {str(e)}")
        
        # Clear session state
        for key in list(st.session_state.keys()):
            if key != "first_load":
                del st.session_state[key]
                
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()
    
    # Initialize page state if not already done
    if "page" not in st.session_state:
        st.session_state.page = "main"
    
    # Load user data if not already loaded
    if "user_data_loaded" not in st.session_state or not st.session_state.user_data_loaded:
        st.session_state.transactions = load_user_transactions(st.session_state.username) or []
        st.session_state.history = load_user_history(st.session_state.username) or []
        
        # Load saved date range and report counter if available
        dates_data = load_user_dates(st.session_state.username)
        if dates_data:
            st.session_state.current_start_date, st.session_state.current_end_date, st.session_state.report_counter = dates_data
        elif "current_start_date" not in st.session_state:
            # Initialize date range if not already set
            start_date = datetime.strptime("03/02/2025", "%d/%m/%Y").date()
            end_date = datetime.strptime("09/02/2025", "%d/%m/%Y").date()
            st.session_state.current_start_date = start_date
            st.session_state.current_end_date = end_date
            st.session_state.report_counter = 1
        
        st.session_state.user_data_loaded = True
    
    # Debug: Show loaded data
    st.sidebar.write("Debug - Transactions:", len(st.session_state.transactions))
    st.sidebar.write("Debug - History:", len(st.session_state.history))
    st.sidebar.write("Debug - Current page:", st.session_state.page)
    
    # Auto-save user data periodically
    auto_save_user_data()
    
    # Create tabs - add Admin tab if user is admin
    if st.session_state.get("is_admin", False):
        # Admin só vê o separador "Colaboradores"
        tab4 = st.tabs(["Colaboradores"])[0]
        
        # Mostrar apenas a aba de colaboradores
        with tab4:
            show_admin_tab()
    else:
        # Verificar a página atual e mostrar o conteúdo apropriado
        if st.session_state.page == "categories":
            show_categories()
        elif st.session_state.page == "form":
            show_form()
        else:  # página principal ou qualquer outra
            tab1, tab2, tab3 = st.tabs(["Registar", "Relatório", "Histórico"])
            
            # Debug tab information
            st.sidebar.write("Debug - Tab IDs:", tab1.id, tab2.id, tab3.id)
            
            # Show content directly in each tab
            with tab1:
                show_main_page()
            
            with tab2:
                show_report_tab()
            
            with tab3:
                show_history_tab()

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
                    # Create a container for the expander and PDF button
                    col1, col2 = st.columns([0.9, 0.1])
                    
                    with col1:
                        expander = st.expander(f"{report['number']} - {format_currency(abs(report['summary']['net_amount']))} ({'A entregar' if report['summary']['net_amount'] >= 0 else 'A receber'})")
                    
                    with col2:
                        # Add PDF download button with a more elegant design
                        report_id = f"{selected_user}_{report['number'].replace(' ', '_')}"
                        
                        # Generate PDF report
                        pdf_data = generate_pdf_report(selected_user, report)
                        download_link = get_pdf_download_link(pdf_data, f"Relatorio_{report_id}")
                        
                        st.markdown(f"""
                        <div style="margin-top: 8px;">
                            {download_link}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with expander:
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
    # Debug message
    st.write("DEBUG: show_history_tab function called")
    
    st.subheader("Histórico de Relatórios")
    
    if not st.session_state.history:
        st.info("Não existem relatórios guardados.")
        return

    # Display detailed information for each report
    for report in st.session_state.history:
        # Use just the expander without the PDF button in the regular history tab
        with st.expander(f"{report['number']} - {format_currency(abs(report['summary']['net_amount']))} ({'A entregar' if report['summary']['net_amount'] >= 0 else 'A receber'})"):
            # Create DataFrame from transactions
            df_transactions = create_transaction_df(report['transactions'])
            
            # Split and sort transactions by type
            income_df = df_transactions[df_transactions["Type"] == TransactionType.INCOME.value].copy()
            expense_df = df_transactions[df_transactions["Type"] == TransactionType.EXPENSE.value].copy()
            
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

def get_period_summary(df):
    total_income = float(df[df["Type"] == TransactionType.INCOME.value]["Amount"].sum())
    total_expense = float(df[df["Type"] == TransactionType.EXPENSE.value]["Amount"].sum())
    net_amount = float(total_income - total_expense)
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_amount': net_amount
    }

def show_report_tab():
    # Debug message
    st.write("DEBUG: show_report_tab function called")
    
    # Simple title for the report tab
    st.subheader("Relatório")
    
    if st.session_state.transactions:
        df = create_transaction_df(st.session_state.transactions)
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            type_filter = st.selectbox(
                "Tipo",
                options=["Todos", TransactionType.EXPENSE.value, TransactionType.INCOME.value],
                key="type_filter"
            )
        
        with col2:
            # Filter categories based on selected type
            if type_filter == TransactionType.EXPENSE.value:
                categories = [cat.value for cat in ExpenseCategory]
            elif type_filter == TransactionType.INCOME.value:
                categories = [cat.value for cat in IncomeCategory]
            else:  # "Todos"
                categories = ([cat.value for cat in ExpenseCategory] + 
                            [cat.value for cat in IncomeCategory])
            
            category_filter = st.selectbox(
                "Categoria",
                options=["Todas"] + categories,
                key="category_filter"
            )
        
        # Apply filters
        if type_filter != "Todos":
            df = df[df["Type"] == type_filter]
        
        if category_filter != "Todas":
            df = df[df["Category"] == category_filter]
        
        # Filter by current date range
        df["Date"] = pd.to_datetime(df["Date"], format=DATE_FORMAT)
        df = df[(df["Date"] >= pd.to_datetime(st.session_state.current_start_date, format=DATE_FORMAT)) & 
                (df["Date"] <= pd.to_datetime(st.session_state.current_end_date, format=DATE_FORMAT))]
        
        # Convert back to string for display
        df["Date"] = df["Date"].dt.strftime("%d/%m/%Y")
        
        # Split dataframe by type
        income_df = df[df["Type"] == TransactionType.INCOME.value].copy()
        expense_df = df[df["Type"] == TransactionType.EXPENSE.value].copy()
        
        # Sort each dataframe by date
        income_df = income_df.sort_values("Date", ascending=True)
        expense_df = expense_df.sort_values("Date", ascending=True)
        
        # Format amounts for display
        income_df["Amount"] = income_df["Amount"].apply(format_currency)
        expense_df["Amount"] = expense_df["Amount"].apply(format_currency)
        
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
                <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(summary.get('total_income', 0))}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="font-size: 16px; color: white;">Total Saídas: </span>
                <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(summary.get('total_expense', 0))}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="font-size: 16px; color: white;">Saldo: </span>
                <span style="font-size: 16px; color: white !important; font-weight: 500;">{format_currency(abs(summary.get('net_amount', 0)))}</span>
                <span style="font-size: 16px; color: white !important; font-weight: 500;">({'A entregar' if summary.get('net_amount', 0) >= 0 else 'A receber'})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate report button
        if st.button("Submeter Relatório"):
            # Verificar se a data final é igual ou anterior à data atual
            today = datetime.now().date()
            if st.session_state.current_end_date > today:
                st.error(f"Não é possível submeter relatórios com datas futuras. A data final ({st.session_state.current_end_date.strftime('%Y-%m-%d')}) deve ser igual ou anterior à data atual ({today.strftime('%Y-%m-%d')}).")
            # Verificar se a data final é anterior a 09/02/2025
            elif st.session_state.current_end_date < datetime.strptime("09/02/2025", "%d/%m/%Y").date():
                st.error("Não é possível submeter o relatório ainda. O relatório só pode ser submetido a partir de 09/02/2025.")
            else:
                # Create a unique report number based on the current date
                report_number = f"Relatório {st.session_state.report_counter}"
                st.session_state.report_counter += 1
                
                # Create a report object
                report = {
                    "number": report_number,
                    "period": f"{st.session_state.current_start_date.strftime('%Y-%m-%d')} a {st.session_state.current_end_date.strftime('%Y-%m-%d')}",
                    "transactions": df.to_dict("records"),
                    "summary": summary,
                    'start_date': st.session_state.current_start_date,
                    'end_date': st.session_state.current_end_date
                }
                
                # Converter para tipos serializáveis
                report = convert_to_serializable(report)
                print(f"DEBUG - Created report: {report['number']}")
                
                # Add to history
                if "history" not in st.session_state:
                    st.session_state.history = []
                    print("DEBUG - Initialized empty history list")
                
                print(f"DEBUG - Before adding report, history has {len(st.session_state.history)} items")
                st.session_state.history.append(report)
                print(f"DEBUG - After adding report, history has {len(st.session_state.history)} items")
                
                # Save history to file
                print(f"DEBUG - Saving history with {len(st.session_state.history)} items")
                save_user_history(st.session_state.username, st.session_state.history)
                
                # Remover transações do período atual
                if st.session_state.transactions:
                    # Filtrar transações para manter apenas as que não estão no período atual
                    # ou que não possuem a chave 'date'
                    filtered_transactions = []
                    for t in st.session_state.transactions:
                        # Verificar se a transação tem a chave 'date' ou 'Date'
                        date_key = None
                        if "date" in t:
                            date_key = "date"
                        elif "Date" in t:
                            date_key = "Date"
                            
                        if date_key is None:
                            # Se não tiver nenhuma chave de data, manter a transação
                            filtered_transactions.append(t)
                            print(f"Transação sem data encontrada: {t}")
                            continue
                            
                        # Converter a data da transação para objeto date
                        try:
                            transaction_date = datetime.strptime(t[date_key], "%Y-%m-%d").date()
                            # Verificar se a data está fora do período atual
                            if not (transaction_date >= st.session_state.current_start_date and 
                                   transaction_date <= st.session_state.current_end_date):
                                filtered_transactions.append(t)
                        except (ValueError, TypeError) as e:
                            # Se houver erro ao converter a data, manter a transação
                            filtered_transactions.append(t)
                            print(f"Erro ao processar data da transação: {t}, erro: {str(e)}")
                    
                    # Atualizar as transações
                    st.session_state.transactions = filtered_transactions
                    # Salvar transações atualizadas
                    save_user_transactions(st.session_state.username, st.session_state.transactions)
                
                # Update to next week's dates
                next_start, next_end = get_next_week_dates(st.session_state.current_end_date)
                st.session_state.current_start_date = next_start
                st.session_state.current_end_date = next_end
                
                # Save the updated dates
                save_user_dates(
                    st.session_state.username, 
                    st.session_state.current_start_date, 
                    st.session_state.current_end_date,
                    st.session_state.report_counter
                )
                
                # Auto-save all user data
                auto_save_user_data()
                
                # Mostrar mensagem de sucesso
                st.success("Relatório submetido com sucesso!")
                
                # Forçar recarregamento da página para atualizar as abas
                st.rerun()
    else:
        st.info("Não há transações registradas para o período atual.")

def convert_to_serializable(obj):
    """
    Converte tipos complexos (como NumPy, Pandas, etc.) para tipos Python nativos serializáveis.
    Esta função deve ser usada antes de serializar qualquer objeto para JSON.
    """
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_to_serializable(obj.tolist())
    elif isinstance(obj, pd.DataFrame):
        return convert_to_serializable(obj.to_dict('records'))
    elif isinstance(obj, pd.Series):
        return convert_to_serializable(obj.to_dict())
    elif hasattr(obj, 'strftime'):  # Para objetos datetime
        return obj.strftime('%Y-%m-%d')
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