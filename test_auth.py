import streamlit as st
import yaml
import os
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Page config
st.set_page_config(
    page_title="Test Authentication",
    page_icon="🔒",
    layout="wide"
)

# Get the absolute path to the config file
base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'data', 'config.yaml')

st.write(f"Config path: {config_path}")
st.write(f"File exists: {os.path.exists(config_path)}")

try:
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    st.write("Config loaded successfully")
    st.write(f"Config keys: {list(config.keys())}")
    
    # Create an authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    
    # Initialize session state
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "name" not in st.session_state:
        st.session_state.name = None
    
    st.write(f"Current authentication status: {st.session_state.authentication_status}")
    
    # If not authenticated, show login form
    if not st.session_state.authentication_status:
        st.title("Login Test")
        
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
    
    # If authenticated, show welcome message
    elif st.session_state.authentication_status:
        st.success(f"Bem-vindo, {st.session_state.name}!")
        
        # Show logout button
        authenticator.logout("Logout", "main")
        
except Exception as e:
    st.error(f"Error: {e}")
    st.exception(e) 