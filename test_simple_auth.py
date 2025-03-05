import streamlit as st
import yaml
from yaml.loader import SafeLoader
import os

# Set page config
st.set_page_config(
    page_title="DYNAMIC WALLET - Login",
    page_icon="💰",
    layout="centered"
)

# Hide Streamlit elements
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'name' not in st.session_state:
    st.session_state.name = None

# Load config file
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'config.yaml')
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
except Exception as e:
    st.error(f"Error loading configuration: {e}")
    st.stop()

def login():
    # Center everything
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Title
        st.markdown("<h1 style='text-align: center; color: #1E88E5; margin-bottom: 30px;'>DYNAMIC WALLET</h1>", unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username in config['credentials']['usernames']:
                    user_data = config['credentials']['usernames'][username]
                    stored_password = user_data['password']
                    
                    # Simple string comparison for testing
                    if username == "admin" and password == "admin123":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.name = user_data['name']
                        st.rerun()
                    elif username == "usuario1" and password == "user123":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.name = user_data['name']
                        st.rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("Username not found")

def dashboard():
    # Add logout button in top right
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()
    
    # Main content
    st.markdown("<h1 style='text-align: center; color: #1E88E5;'>DYNAMIC WALLET</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Welcome, {st.session_state.name}!</h3>", unsafe_allow_html=True)
    st.write("Your financial dashboard will appear here.")

def main():
    # Display login or dashboard based on authentication status
    if not st.session_state.authenticated:
        login()
    else:
        dashboard()

if __name__ == "__main__":
    main() 