from datetime import datetime, timedelta
import pandas as pd
from constants.config import (
    MAX_MEAL_ALLOWANCE_PER_PERSON,
    HR_RATES,
    DATE_FORMAT
)

def get_week_period(date=None):
    """Get the start and end dates of the week for a given date."""
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, DATE_FORMAT)
    
    start_date = date - timedelta(days=date.weekday())
    end_date = start_date + timedelta(days=6)
    return start_date.date(), end_date.date()

def is_late_submission(transaction_date):
    """Check if a transaction is being submitted after its period ended."""
    current_date = datetime.now().date()
    _, period_end = get_week_period(transaction_date)
    return current_date > period_end

def calculate_meal_expense(total_amount, num_people, meal_type):
    """Calculate meal expense with validation."""
    max_allowed = num_people * MAX_MEAL_ALLOWANCE_PER_PERSON
    actual_amount = min(total_amount, max_allowed)
    return actual_amount, None

def calculate_hr_expense(role):
    """
    Calculate HR expense based on role's fixed rate.
    
    Args:
        role (str): The role from HR_RATES
        
    Returns:
        tuple: (amount, error_message)
    """
    if role not in HR_RATES:
        return 0, "Função inválida"
    
    return HR_RATES[role], None

def format_currency(amount):
    """Format amount as currency."""
    return f"€{amount:.2f}"

def create_transaction_df(transactions):
    """Create a pandas DataFrame from transactions list, handling different key formats."""
    if not transactions:
        return pd.DataFrame(columns=["Date", "Type", "Category", "Description", "Amount"])
    
    # Normalize transaction keys
    normalized_transactions = []
    for t in transactions:
        normalized = {}
        
        # Handle Date/date
        if "Date" in t:
            normalized["Date"] = t["Date"]
        elif "date" in t:
            normalized["Date"] = t["date"]
        else:
            normalized["Date"] = "Unknown"
            
        # Handle Type/type
        if "Type" in t:
            normalized["Type"] = t["Type"]
        elif "type" in t:
            normalized["Type"] = t["type"]
        else:
            normalized["Type"] = "Unknown"
            
        # Handle Category/category
        if "Category" in t:
            normalized["Category"] = t["Category"]
        elif "category" in t:
            normalized["Category"] = t["category"]
        else:
            normalized["Category"] = "Unknown"
            
        # Handle Description/description
        if "Description" in t:
            normalized["Description"] = t["Description"]
        elif "description" in t:
            normalized["Description"] = t["description"]
        else:
            normalized["Description"] = ""
            
        # Handle Amount/amount
        if "Amount" in t:
            normalized["Amount"] = float(t["Amount"])
        elif "amount" in t:
            normalized["Amount"] = float(t["amount"])
        else:
            normalized["Amount"] = 0.0
            
        normalized_transactions.append(normalized)
    
    return pd.DataFrame(normalized_transactions)

def get_period_summary(df):
    """Calculate summary statistics for a period."""
    if df.empty:
        return {
            "total_income": 0,
            "total_expense": 0,
            "total_expenses": 0,  # Duplicado para compatibilidade
            "net_amount": 0,
            "total_meals": 0,
            "total_transport": 0,
            "total_other": 0
        }
    
    # Calcular totais por tipo
    expenses = df[df["Type"] == "Saída"]["Amount"].sum()
    income = df[df["Type"] == "Entrada"]["Amount"].sum()
    
    # Calcular totais por categoria de despesa
    meals = df[(df["Type"] == "Saída") & (df["Category"] == "Refeição")]["Amount"].sum() if "Category" in df.columns else 0
    transport = df[(df["Type"] == "Saída") & (df["Category"] == "Transporte")]["Amount"].sum() if "Category" in df.columns else 0
    other = df[(df["Type"] == "Saída") & (df["Category"] == "Outro")]["Amount"].sum() if "Category" in df.columns else 0
    
    return {
        "total_income": income,
        "total_expense": expenses,
        "total_expenses": expenses,  # Duplicado para compatibilidade
        "net_amount": income - expenses,
        "total_meals": meals,
        "total_transport": transport,
        "total_other": other
    } 