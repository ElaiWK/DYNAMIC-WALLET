import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import json
import os
import hashlib
import pickle
import base64
import uuid

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
    
    # Create tabs for login and signup
    login_tab, signup_tab = st.tabs(["Login", "Signup"])
    
    with login_tab:
        # Login form
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
                    
                    # Load user data
                    if "transactions" not in st.session_state:
                        st.session_state.transactions = load_user_transactions(username)
                    
                    if "history" not in st.session_state:
                        st.session_state.history = load_user_history(username)
                    
                    if "history" not in st.session_state:
                        st.session_state.history = []
                
                    st.session_state.user_data_loaded = True
                
                    # Show updated session state
                    # st.write("Debug - Updated session state:", {k: v for k, v in st.session_state.items() if k not in ['login_password']})
                
                    # Force rerun to show the main app
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
    
    with signup_tab:
        # Signup form
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submit_signup = st.form_submit_button("Create Account")
            
            if submit_signup:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    users = load_users()
                    if new_username in users:
                        st.error("Username already exists. Please choose another one.")
                    else:
                        if create_user(new_username, new_password):
                            st.success("Account created successfully! You can now log in.")
                            st.session_state.login_tab = "login"
                        else:
                            st.error("Failed to create account. Please try again.")

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
                        description = f"{meal_type} com {names_str} (Fatura: {format_currency(st.session_state.meal_total_amount)}, Valor por pessoa: {format_currency(calculated_amount)})"
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

# User data functions
def get_user_data_dir():
    """Get the directory for user data"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
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
        return
    
    user_dir = get_user_dir(username)
    transactions_file = os.path.join(user_dir, "transactions.json")
    
    with open(transactions_file, "w") as f:
        json.dump(transactions, f)

def load_user_transactions(username):
    """Load user transactions from a JSON file"""
    if not username:
        return []
    
    user_dir = get_user_dir(username)
    transactions_file = os.path.join(user_dir, "transactions.json")
    
    if os.path.exists(transactions_file):
        with open(transactions_file, "r") as f:
            return json.load(f)
    return []

def save_user_history(username, history):
    """Save user history to a JSON file"""
    if not username:
        return
    
    user_dir = get_user_dir(username)
    history_file = os.path.join(user_dir, "history.json")
    
    with open(history_file, "w") as f:
        json.dump(history, f)

def load_user_history(username):
    """Load user history from a JSON file"""
    if not username:
        return []
    
    user_dir = get_user_dir(username)
    history_file = os.path.join(user_dir, "history.json")
    
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            return json.load(f)
    return []

def main():
    # Debug: Show current authentication state
    # st.sidebar.write("Debug - Auth state:", st.session_state.get("authenticated", False))
    # st.sidebar.write("Debug - Username:", st.session_state.get("username", "None"))
    
    # Initialize session state if not already done
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "username" not in st.session_state:
        st.session_state.username = None
    
    # Show login page if not authenticated
    if not st.session_state.authenticated:
        # st.sidebar.warning("Not authenticated - showing login page")
        show_login_page()
        return
    
    # User is authenticated, show the app
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    
    # Add logout button
    if st.sidebar.button("Logout"):
        # Save user data before logging out
        try:
            if hasattr(st.session_state, "transactions") and hasattr(st.session_state, "history"):
                save_user_transactions(st.session_state.username, st.session_state.transactions)
                save_user_history(st.session_state.username, st.session_state.history)
        except Exception as e:
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
        st.session_state.user_data_loaded = True
    
    # Create tabs - add Admin tab if user is admin
    if st.session_state.get("is_admin", False):
        tab1, tab2, tab3, tab4 = st.tabs(["Registar", "Relatório", "Histórico", "Admin"])
    else:
        tab1, tab2, tab3 = st.tabs(["Registar", "Relatório", "Histórico"])
    
    # Handle tab switching
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Registar"
    
    # Only update active tab when explicitly switching tabs
    if tab2.id and tab2.id != st.session_state.active_tab:
        st.session_state.active_tab = "Relatório"
    elif tab1.id and tab1.id != st.session_state.active_tab:
        st.session_state.active_tab = "Registar"
    elif tab3.id and tab3.id != st.session_state.active_tab:
        st.session_state.active_tab = "Histórico"
    elif st.session_state.get("is_admin", False) and tab4.id and tab4.id != st.session_state.active_tab:
        st.session_state.active_tab = "Admin"
    
    with tab1:
        if st.session_state.page == "main":
            show_main_page()
        elif st.session_state.page == "categories":
            show_categories()
        elif st.session_state.page == "form":
            show_form()
    
    with tab2:
        show_report_tab()
    
    with tab3:
        show_history_tab()
    
    # Show admin tab if user is admin
    if st.session_state.get("is_admin", False):
        with tab4:
            show_admin_tab()
    
    # Add Dynamic Wallet icon in top right
    st.markdown("""
        <style>
        .dynamic-wallet-icon {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            font-size: 24px;
            width: 40px;
            height: 40px;
            line-height: 40px;
            text-align: center;
            background-color: #4CAF50;
            border-radius: 50%;
            cursor: pointer;
        }
        </style>
        <div class="dynamic-wallet-icon" onclick="window.location.href='.'">💰</div>
    """, unsafe_allow_html=True)

def show_admin_tab():
    """Show the admin dashboard"""
    st.subheader("Admin Dashboard")
    st.write("View data for all users")
    
    # Get list of all users
    users = load_users()
    usernames = [username for username in users.keys() if username != "admin" and not username.startswith("_")]
    
    # Let admin select a user to view
    selected_user = st.selectbox("Select User", usernames)
    
    if selected_user:
        st.subheader(f"Data for {selected_user}")
        
        # Create tabs for user data
        user_transactions_tab, user_history_tab = st.tabs(["Transactions", "History"])
        
        with user_transactions_tab:
            # Load user transactions
            transactions = load_user_transactions(selected_user)
            if transactions:
                df_transactions = create_transaction_df(transactions)
                st.dataframe(df_transactions)
            else:
                st.info(f"{selected_user} has no transactions")
        
        with user_history_tab:
            # Load user history
            history = load_user_history(selected_user)
            if history:
                for report in history:
                    with st.expander(f"{report['number']} - {format_currency(abs(report['summary']['net_amount']))} ({'A entregar' if report['summary']['net_amount'] >= 0 else 'A receber'})"):
                        # Create DataFrame from transactions
                        df_report = create_transaction_df(report['transactions'])
                        st.dataframe(df_report)
                        
                        # Show summary
                        st.write("Summary:")
                        st.write(f"Total Income: {format_currency(report['summary']['total_income'])}")
                        st.write(f"Total Expense: {format_currency(report['summary']['total_expense'])}")
                        st.write(f"Net Amount: {format_currency(abs(report['summary']['net_amount']))} {'(A entregar)' if report['summary']['net_amount'] >= 0 else '(A receber)'}")
            else:
                st.info(f"{selected_user} has no history reports")

def show_history_tab():
    st.subheader("Histórico de Relatórios")
    
    if not st.session_state.history:
        st.info("Não existem relatórios guardados.")
        return

    # Display detailed information for each report
    for report in st.session_state.history:
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
    total_income = df[df["Type"] == TransactionType.INCOME.value]["Amount"].sum()
    total_expense = df[df["Type"] == TransactionType.EXPENSE.value]["Amount"].sum()
    net_amount = total_income - total_expense
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_amount': net_amount
    }

def show_report_tab():
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
        filtered_df = df.copy()
        if type_filter != "Todos":
            filtered_df = filtered_df[filtered_df["Type"] == type_filter]
        if category_filter != "Todas":
            filtered_df = filtered_df[filtered_df["Category"] == category_filter]
        
        # Split dataframe by type
        income_df = filtered_df[filtered_df["Type"] == TransactionType.INCOME.value].copy()
        expense_df = filtered_df[filtered_df["Type"] == TransactionType.EXPENSE.value].copy()
        
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
        
        # Add submit button
        st.write("")
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter Relatório", key="submit_report", use_container_width=True):
                # Save current report to history with actual data
                st.session_state.history.append({
                    'number': format_date_range(st.session_state.current_start_date, st.session_state.current_end_date),
                    'transactions': st.session_state.transactions.copy(),
                    'summary': summary,
                    'start_date': st.session_state.current_start_date.strftime(DATE_FORMAT) if hasattr(st.session_state.current_start_date, 'strftime') else st.session_state.current_start_date,
                    'end_date': st.session_state.current_end_date.strftime(DATE_FORMAT) if hasattr(st.session_state.current_end_date, 'strftime') else st.session_state.current_end_date
                })
                
                # Save history to file
                save_user_history(st.session_state.username, st.session_state.history)
                
                # Update to next week's dates
                next_start, next_end = get_next_week_dates(st.session_state.current_end_date)
                st.session_state.current_start_date = next_start
                st.session_state.current_end_date = next_end
                
                # Reset state
                reset_state()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Não existem transações registradas.")

if __name__ == "__main__":
    try:
        # st.write("Debug - Running in directory:", os.getcwd())
        # st.write("Debug - Files in current directory:", os.listdir())
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                # st.write(f"Debug - Created data directory: {data_dir}")
            except Exception as e:
                # st.write(f"Debug - Error creating data directory: {str(e)}")
                pass
        
        # Initialize first_load flag if not present
        if "first_load" not in st.session_state:
            st.session_state.first_load = True
            # Reset all session state on first load
            # st.write("Debug - Reset session state on first load")
            reset_state()
        
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e) 