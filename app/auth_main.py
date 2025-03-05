import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Page config
st.set_page_config(
    page_title="MD Wallet - Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# Apply custom CSS to fix the shaking issue
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .login-container {
        max-width: 500px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

def load_config():
    """Load authentication configuration from file."""
    # Get the absolute path to the config file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'data', 'config.yaml')
    
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

# Initialize session state for authentication
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = None
if "username" not in st.session_state:
    st.session_state.username = None
if "name" not in st.session_state:
    st.session_state.name = None

def main():
    # Load the authentication configuration
    config = load_config()
    
    # Create an authenticator object (for version 0.2.2)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    # If not authenticated, show login form
    if not st.session_state.authentication_status:
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            # Logo and title
            st.image("https://img.freepik.com/free-vector/gradient-perspective-logo-design_23-2149700161.jpg", width=150)
            st.title("MD Wallet")
            st.subheader("Login")
            
            # Display the login form
            name, authentication_status, username = authenticator.login("Login", "main")
            
            # Store authentication status in session state
            st.session_state.authentication_status = authentication_status
            st.session_state.username = username
            st.session_state.name = name
            
            # Handle authentication results
            if st.session_state.authentication_status == False:
                st.error("Usuário/senha incorretos")
            elif st.session_state.authentication_status == None:
                st.warning("Por favor, digite seu usuário e senha")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
    # If authenticated, show the app
    elif st.session_state.authentication_status:
        # Show logout button in sidebar
        with st.sidebar:
            st.write(f"Bem-vindo, {st.session_state.name}")
            authenticator.logout("Logout", "sidebar")
        
        # Simple app content
        st.title("MD Wallet - Expense Tracker")
        st.write("Você está logado como:", st.session_state.name)
        st.success("Autenticação bem-sucedida!")

if __name__ == "__main__":
    main() 