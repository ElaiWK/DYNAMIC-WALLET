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
    """Create a pandas DataFrame from transactions list."""
    if not transactions:
        return pd.DataFrame(columns=["Date", "Type", "Category", "Description", "Amount"])
    return pd.DataFrame(transactions)

def get_period_summary(df):
    """Calculate summary statistics for a period."""
    if df.empty:
        return {"net_amount": 0}
    
    expenses = df[df["Type"] == "Saída"]["Amount"].sum()
    income = df[df["Type"] == "Entrada"]["Amount"].sum()
    
    return {"net_amount": income - expenses} 