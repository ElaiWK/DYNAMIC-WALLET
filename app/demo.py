import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="Dynamic Wallet Demo",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "main"
    st.session_state.total_income = 3500.0
    st.session_state.total_expenses = 1200.0
    st.session_state.net_amount = 2300.0
    st.session_state.start_date = datetime.now().date()
    st.session_state.end_date = (datetime.now() + timedelta(days=7)).date()

# Sample transactions
sample_transactions = [
    {"date": "01/03/2025", "type": "EXPENSE", "category": "Meal", "description": "Lunch with team", "amount": 45.50},
    {"date": "02/03/2025", "type": "EXPENSE", "category": "Transportation", "description": "Taxi to client", "amount": 22.00},
    {"date": "03/03/2025", "type": "INCOME", "category": "Salary", "description": "March salary", "amount": 2500.00}
]

# Sample reports
sample_reports = [
    {"period": "24/02/2025 - 01/03/2025", "income": 3000.00, "expenses": 1200.00, "net": 1800.00},
    {"period": "17/02/2025 - 23/02/2025", "income": 2500.00, "expenses": 900.00, "net": 1600.00}
]

def show_main_page():
    st.title("DYNAMIC WALLET")
    st.subheader(f"Period: {st.session_state.start_date.strftime('%d/%m/%Y')} to {st.session_state.end_date.strftime('%d/%m/%Y')}")
    
    # Create two columns for buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Expenses", key="expense_button", use_container_width=True):
            st.session_state.page = "categories"
            st.session_state.transaction_type = "EXPENSE"
            st.rerun()
    
    with col2:
        if st.button("Income", key="income_button", use_container_width=True):
            st.session_state.page = "categories"
            st.session_state.transaction_type = "INCOME"
            st.rerun()
    
    # Show balance
    st.markdown("### Current Balance")
    st.write(f"Total Income: €{st.session_state.total_income:.2f}")
    st.write(f"Total Expenses: €{st.session_state.total_expenses:.2f}")
    st.write(f"Net Amount: €{st.session_state.net_amount:.2f}")
    
    # Navigation buttons
    st.markdown("### Navigation")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("History", key="history_button", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
    
    with col2:
        if st.button("Report", key="report_button", use_container_width=True):
            st.session_state.page = "report"
            st.rerun()
    
    with col3:
        if st.button("Admin", key="admin_button", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()

def show_categories():
    st.title("Select Category")
    
    # Back button
    if st.button("← Back", key="back_button"):
        st.session_state.page = "main"
        st.rerun()
    
    categories = (
        ["Meal", "Transportation", "Accommodation", "HR", "Delivery", "Other"] 
        if st.session_state.transaction_type == "EXPENSE"
        else ["Salary", "Bonus", "Service", "Delivery", "Other"]
    )
    
    # Display category buttons
    for idx, category in enumerate(categories):
        if st.button(category, key=f"category_{idx}", use_container_width=True):
            st.session_state.category = category
            st.session_state.page = "form"
            st.rerun()

def show_form():
    st.title(f"{'Expense' if st.session_state.transaction_type == 'EXPENSE' else 'Income'} - {st.session_state.category}")
    
    # Back button
    if st.button("← Back to Categories", key="back_to_categories"):
        st.session_state.page = "categories"
        st.rerun()
    
    # Simple form for all categories
    date = st.date_input("Date", value=datetime.now().date())
    amount = st.number_input("Amount (€)", min_value=0.0, step=0.5)
    description = st.text_input("Description")
    
    if st.button("Submit", key="submit_form"):
        st.success("Transaction added successfully!")
        st.session_state.page = "main"
        st.rerun()

def show_history_tab():
    st.title("Transaction History")
    
    # Back button
    if st.button("← Back to Main", key="back_to_main"):
        st.session_state.page = "main"
        st.rerun()
    
    # Display transactions
    st.write("### Transactions")
    df = pd.DataFrame(sample_transactions)
    st.dataframe(df)

def show_report_tab():
    st.title("Weekly Report")
    
    # Back button
    if st.button("← Back to Main", key="back_to_main"):
        st.session_state.page = "main"
        st.rerun()
    
    st.write(f"### Period: {st.session_state.start_date.strftime('%d/%m/%Y')} to {st.session_state.end_date.strftime('%d/%m/%Y')}")
    
    # Summary
    st.write("### Financial Summary")
    st.write(f"Total Income: €{st.session_state.total_income:.2f}")
    st.write(f"Total Expenses: €{st.session_state.total_expenses:.2f}")
    st.write(f"Net Amount: €{st.session_state.net_amount:.2f}")
    
    # Generate PDF button
    if st.button("Generate PDF Report"):
        st.success("PDF report generated successfully!")
    
    # Submit report button
    if st.button("Submit Report"):
        st.success("Report submitted successfully!")
        st.session_state.page = "main"
        st.rerun()

def show_admin_tab():
    st.title("Admin Dashboard")
    
    # Back button
    if st.button("← Back to Main", key="back_to_main"):
        st.session_state.page = "main"
        st.rerun()
    
    st.write("### User Management")
    
    # Sample users
    users = ["admin", "Humberto", "Maria", "João"]
    selected_user = st.selectbox("Select User", users)
    
    st.write(f"### Reports for {selected_user}")
    
    for report in sample_reports:
        st.write(f"**Period:** {report['period']}")
        st.write(f"Income: €{report['income']:.2f}")
        st.write(f"Expenses: €{report['expenses']:.2f}")
        st.write(f"Net: €{report['net']:.2f}")
        st.button(f"Download Report - {report['period']}", key=f"download_{report['period']}")
        st.write("---")

# Routing based on page
if st.session_state.page == "main":
    show_main_page()
elif st.session_state.page == "categories":
    show_categories()
elif st.session_state.page == "form":
    show_form()
elif st.session_state.page == "history":
    show_history_tab()
elif st.session_state.page == "report":
    show_report_tab()
elif st.session_state.page == "admin":
    show_admin_tab() 