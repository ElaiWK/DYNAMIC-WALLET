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

# Custom CSS
st.markdown("""
<style>
    div.stButton > button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 32px 64px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-size: 24px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .expense-button > button {
        background-color: #ff4b4b !important;
    }
    .expense-button > button:hover {
        background-color: #e64444 !important;
    }
    .income-button > button {
        background-color: #4CAF50 !important;
    }
    .income-button > button:hover {
        background-color: #45a049 !important;
    }
    .balance-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-top: 30px;
        text-align: center;
    }
    div.category-button > button {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        color: #333333;
        padding: 20px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-size: 18px;
        margin: 10px 0;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.3s;
    }
    div.category-button > button:hover {
        border-color: #4CAF50;
        transform: translateX(5px);
    }
    div.back-button > button {
        background-color: #6c757d;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        text-decoration: none;
        font-size: 14px;
        margin-bottom: 20px;
        display: inline-block;
        width: auto;
    }
    .form-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "page" not in st.session_state:
    st.session_state.page = "main"
if "transaction_type" not in st.session_state:
    st.session_state.transaction_type = None
if "category" not in st.session_state:
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
        st.session_state.page = "categories"
    elif st.session_state.page == "categories":
        st.session_state.page = "main"
        st.session_state.transaction_type = None
    st.rerun()

def show_main_page():
    st.title("💰 MD Wallet")
    
    # Create two columns for buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Pague", key="expense_button"):
            navigate_to_categories(TransactionType.EXPENSE.value)
    
    with col2:
        if st.button("Recebi", key="income_button"):
            navigate_to_categories(TransactionType.INCOME.value)
    
    # Show balance at the bottom
    if st.session_state.transactions:
        df = create_transaction_df(st.session_state.transactions)
        summary = get_period_summary(df)
        
        st.markdown("""
        <div class="balance-container">
            <h2>Saldo Total</h2>
            <h1 style="color: {};">{}</h1>
        </div>
        """.format(
            '#4CAF50' if summary['net_amount'] >= 0 else '#ff4b4b',
            format_currency(summary['net_amount'])
        ), unsafe_allow_html=True)

def show_categories():
    # Back button
    if st.button("← Voltar", key="back_button"):
        navigate_back()
    
    st.subheader("Selecione a Categoria")
    
    categories = (
        [cat.value for cat in ExpenseCategory] 
        if st.session_state.transaction_type == TransactionType.EXPENSE.value
        else [cat.value for cat in IncomeCategory]
    )
    
    for idx, category in enumerate(categories):
        if st.button(category, key=f"category_{idx}"):
            navigate_to_form(category)

def show_form():
    # Back button
    if st.button("← Voltar para Categorias", key="back_to_categories"):
        navigate_back()
    
    st.subheader(f"{'Despesa' if st.session_state.transaction_type == TransactionType.EXPENSE.value else 'Receita'} - {st.session_state.category}")
    
    with st.form("transaction_form", clear_on_submit=True):
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        date = st.date_input("Data", datetime.now())
        amount = None
        error = None
        
        if st.session_state.category == ExpenseCategory.MEAL.value:
            amount_per_person = st.number_input("Valor por Pessoa (€)", min_value=0.0, step=0.5)
            num_people = st.number_input("Número de Pessoas", min_value=1, step=1)
            description = st.text_input("Descrição")
            
            if st.form_submit_button("Submeter"):
                amount, error = calculate_meal_expense(amount_per_person, num_people)
                
        elif st.session_state.category == ExpenseCategory.HR.value:
            role = st.selectbox("Função", list(HR_RATES.keys()))
            hours = st.number_input("Horas Trabalhadas", min_value=0.0, step=0.5)
            description = f"Despesa RH para {role}"
            
            if st.form_submit_button("Submeter"):
                amount, error = calculate_hr_expense(hours, role)
                
        elif st.session_state.category == IncomeCategory.SERVICE.value:
            amount = st.number_input("Valor (€)", min_value=0.0, step=0.5)
            reference = st.text_input("Número do Serviço")
            description = f"Serviço #{reference}"
            
            if st.form_submit_button("Submeter"):
                error = None if amount > 0 else "O valor deve ser maior que 0"
                
        elif st.session_state.category == IncomeCategory.COLLABORATOR.value:
            amount = st.number_input("Valor (€)", min_value=0.0, step=0.5)
            collaborator = st.text_input("Nome do Colaborador")
            description = f"Pagamento de {collaborator}"
            
            if st.form_submit_button("Submeter"):
                error = None if amount > 0 else "O valor deve ser maior que 0"
                
        else:  # Other expense or income
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
    transaction = {
        "Date": date.strftime(DATE_FORMAT),
        "Type": type_,
        "Category": category,
        "Description": description,
        "Amount": amount
    }
    st.session_state.transactions.append(transaction)

def main():
    if st.session_state.page == "main":
        show_main_page()
    elif st.session_state.page == "categories":
        show_categories()
    elif st.session_state.page == "form":
        show_form()

if __name__ == "__main__":
    main() 