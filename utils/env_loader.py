import os
from dotenv import load_dotenv
import streamlit as st

def load_environment_variables():
    """Load environment variables from .env file."""
    # Get the absolute path to the .env file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, '.env')
    
    # Load environment variables from .env file if it exists
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("Loaded environment variables from .env file")
    else:
        print(".env file not found, using environment variables from system")
    
    # Check if MongoDB URI is available
    if "MONGO_URI" in os.environ:
        print("MongoDB URI found in environment variables")
    elif hasattr(st, "secrets") and "mongo" in st.secrets and "uri" in st.secrets["mongo"]:
        print("MongoDB URI found in Streamlit secrets")
    else:
        print("WARNING: MongoDB URI not found. Using local storage fallback.")
        
    return True 