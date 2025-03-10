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
    
    # Return date objects, handling both datetime and date inputs
    if hasattr(start_date, 'date'):
        return start_date.date(), end_date.date()
    else:
        return start_date, end_date

def is_late_submission(transaction_date):
    """Check if a transaction is being submitted after its period ended."""
    current_date = datetime.now().date()
    _, period_end = get_week_period(transaction_date)
    return current_date > period_end

def calculate_meal_expense(amount_per_person, num_people):
    """Calculate meal expense with validation."""
    if amount_per_person > MAX_MEAL_ALLOWANCE_PER_PERSON:
        return num_people * MAX_MEAL_ALLOWANCE_PER_PERSON, None
    total = amount_per_person * num_people
    return total, None

def calculate_hr_expense(hours, role):
    """Calculate HR expense based on role and hours."""
    if role not in HR_RATES:
        return None, "Função inválida selecionada"
    rate = HR_RATES[role]
    total = hours * rate
    return total, None

def format_currency(amount):
    """Format amount as currency."""
    return f"€{amount:.2f}"

def create_transaction_df(transactions):
    """Create a pandas DataFrame from transactions list."""
    if not transactions:
        return pd.DataFrame(columns=["date", "type", "category", "description", "amount"])
    
    # Convert to DataFrame and ensure lowercase column names
    df = pd.DataFrame(transactions)
    
    # Rename columns if they are not lowercase
    column_mapping = {
        'Date': 'date',
        'Type': 'type',
        'Category': 'category',
        'Description': 'description',
        'Amount': 'amount'
    }
    
    # Apply mapping to any columns that exist in the mapping
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)
    
    return df

def get_period_summary(df):
    """Get a summary of the transactions for the current period."""
    if df.empty:
        return {
            "total_expenses": 0,
            "total_income": 0,
            "net_amount": 0
        }
    
    # Ensure the column names exist
    if "type" not in df.columns:
        print(f"DEBUG - DataFrame columns: {df.columns}")
        # Try to fix column names or use reasonable defaults
        return {
            "total_expenses": 0,
            "total_income": 0,
            "net_amount": 0
        }
    
    expenses = df[df["type"] == "Saída"]["amount"].sum()
    income = df[df["type"] == "Entrada"]["amount"].sum()
    
    return {
        "total_expenses": expenses,
        "total_income": income,
        "net_amount": income - expenses
    } 