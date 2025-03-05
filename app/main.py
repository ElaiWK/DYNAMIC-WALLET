import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

from constants.config import (
    TransactionType,
    ExpenseCategory,
    IncomeCategory,
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

# Initialize session state
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "submitted_reports" not in st.session_state:
    st.session_state.submitted_reports = {}

def main():
    st.title("MD Wallet - Expense Tracker")
    
    # Main navigation
    tab1, tab2 = st.tabs(["Record Transaction", "View Reports"])
    
    with tab1:
        record_transaction()
    
    with tab2:
        view_reports()

def record_transaction():
    st.header("Record Transaction")
    
    # Transaction type selection
    transaction_type = st.radio(
        "Select Transaction Type",
        [TransactionType.EXPENSE.value, TransactionType.INCOME.value],
        horizontal=True
    )
    
    if transaction_type == TransactionType.EXPENSE.value:
        record_expense()
    else:
        record_income()

def record_expense():
    with st.form("expense_form"):
        date = st.date_input("Date", datetime.now())
        category = st.selectbox(
            "Category",
            [cat.value for cat in ExpenseCategory]
        )
        
        # Dynamic fields based on category
        amount = None
        error = None
        
        if category == ExpenseCategory.MEAL.value:
            amount_per_person = st.number_input("Amount per Person (€)", min_value=0.0, step=0.5)
            num_people = st.number_input("Number of People", min_value=1, step=1)
            description = st.text_input("Description")
            
            if st.form_submit_button("Submit"):
                amount, error = calculate_meal_expense(amount_per_person, num_people)
                
        elif category == ExpenseCategory.HR.value:
            role = st.selectbox("Role", list(HR_RATES.keys()))
            hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
            description = f"HR expense for {role}"
            
            if st.form_submit_button("Submit"):
                amount, error = calculate_hr_expense(hours, role)
                
        else:  # Other expense
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.5)
            description = st.text_input("Description")
            
            if st.form_submit_button("Submit"):
                error = None if amount > 0 else "Amount must be greater than 0"
        
        if error:
            st.error(error)
        elif amount is not None:
            save_transaction(date, TransactionType.EXPENSE.value, category, description, amount)
            st.success("Expense recorded successfully!")

def record_income():
    with st.form("income_form"):
        date = st.date_input("Date", datetime.now())
        category = st.selectbox(
            "Category",
            [cat.value for cat in IncomeCategory]
        )
        
        amount = st.number_input("Amount (€)", min_value=0.0, step=0.5)
        
        if category == IncomeCategory.SERVICE.value:
            reference = st.text_input("Service Number")
            description = f"Service #{reference}"
        elif category == IncomeCategory.COLLABORATOR.value:
            collaborator = st.text_input("Collaborator Name")
            description = f"Payment from {collaborator}"
        else:
            description = st.text_input("Description")
        
        if st.form_submit_button("Submit"):
            if amount > 0:
                save_transaction(date, TransactionType.INCOME.value, category, description, amount)
                st.success("Income recorded successfully!")
            else:
                st.error("Amount must be greater than 0")

def save_transaction(date, type_, category, description, amount):
    transaction = {
        "Date": date.strftime(DATE_FORMAT),
        "Type": type_,
        "Category": category,
        "Description": description,
        "Amount": amount
    }
    st.session_state.transactions.append(transaction)

def view_reports():
    st.header("Transaction Reports")
    
    if not st.session_state.transactions:
        st.info("No transactions recorded yet.")
        return
    
    # Create DataFrame
    df = create_transaction_df(st.session_state.transactions)
    
    # Display current period summary
    current_start, current_end = get_week_period()
    st.subheader(f"Current Period ({current_start} to {current_end})")
    
    # Filter transactions for current period
    mask = (pd.to_datetime(df["Date"]) >= pd.Timestamp(current_start)) & \
           (pd.to_datetime(df["Date"]) <= pd.Timestamp(current_end))
    current_df = df[mask]
    
    # Display summary metrics
    summary = get_period_summary(current_df)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Expenses", format_currency(summary["total_expenses"]))
    with col2:
        st.metric("Total Income", format_currency(summary["total_income"]))
    with col3:
        st.metric("Net Amount", format_currency(summary["net_amount"]))
    
    # Display transactions table
    st.subheader("Transactions")
    st.dataframe(
        current_df,
        column_config={
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="€%.2f"
            )
        }
    )
    
    # Download button
    if not current_df.empty:
        csv = current_df.to_csv(index=False)
        st.download_button(
            "Download Report",
            csv,
            f"transactions_{current_start}_{current_end}.csv",
            "text/csv"
        )
    
    # Visualization
    if not current_df.empty:
        st.subheader("Expense Distribution")
        fig = px.pie(
            current_df[current_df["Type"] == TransactionType.EXPENSE.value],
            values="Amount",
            names="Category",
            title="Expenses by Category"
        )
        st.plotly_chart(fig)

if __name__ == "__main__":
    main() 