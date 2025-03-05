import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

from constants.config import (
    TransactionType,
    ExpenseCategory,
    IncomeCategory,
    MealType,
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
        padding: 24px 48px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-size: 20px;
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
    .meal-submit-button > button {
        background-color: #ff4b4b !important;
    }
    .meal-submit-button > button:hover {
        background-color: #e64444 !important;
    }
    .balance-container {
        padding: 15px;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-top: 20px;
        text-align: center;
    }
    .balance-container h1 {
        font-size: 28px;
        margin: 0;
    }
    .balance-container h2 {
        font-size: 18px;
        margin-bottom: 5px;
    }
    .balance-container p {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
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
        # Reset meal form state if coming from meal expense form
        if st.session_state.category == ExpenseCategory.MEAL.value:
            if "meal_total_amount" in st.session_state:
                del st.session_state.meal_total_amount
            if "meal_num_people" in st.session_state:
                del st.session_state.meal_num_people
            if "collaborator_names" in st.session_state:
                del st.session_state.collaborator_names
            if "meal_date" in st.session_state:
                del st.session_state.meal_date
        # Reset HR form state if coming from HR form
        elif st.session_state.category == ExpenseCategory.HR.value:
            if "hr_role" in st.session_state:
                del st.session_state.hr_role
            if "hr_date" in st.session_state:
                del st.session_state.hr_date
            if "hr_collaborator" in st.session_state:
                del st.session_state.hr_collaborator
        # Reset purchase form state if coming from purchase form
        elif st.session_state.category == ExpenseCategory.OTHER.value:
            if "purchase_what" in st.session_state:
                del st.session_state.purchase_what
            if "purchase_amount" in st.session_state:
                del st.session_state.purchase_amount
            if "purchase_justification" in st.session_state:
                del st.session_state.purchase_justification
            if "purchase_date" in st.session_state:
                del st.session_state.purchase_date
        # Reset delivery form state if coming from delivery form
        elif st.session_state.category == ExpenseCategory.DELIVERY.value:
            if "delivery_collaborator" in st.session_state:
                del st.session_state.delivery_collaborator
            if "delivery_amount" in st.session_state:
                del st.session_state.delivery_amount
            if "delivery_date" in st.session_state:
                del st.session_state.delivery_date
        # Reset service form state
        elif st.session_state.category == IncomeCategory.SERVICE.value:
            if "service_reference" in st.session_state:
                del st.session_state.service_reference
            if "service_amount" in st.session_state:
                del st.session_state.service_amount
            if "service_date" in st.session_state:
                del st.session_state.service_date
        # Reset delivery income form state
        elif st.session_state.category == IncomeCategory.DELIVERY.value:
            if "delivery_income_collaborator" in st.session_state:
                del st.session_state.delivery_income_collaborator
            if "delivery_income_amount" in st.session_state:
                del st.session_state.delivery_income_amount
            if "delivery_income_date" in st.session_state:
                del st.session_state.delivery_income_date
        st.session_state.page = "categories"
    elif st.session_state.page == "categories":
        st.session_state.page = "main"
        st.session_state.transaction_type = None
    st.rerun()

def show_main_page():
    # Center the title without icon
    st.markdown("""
        <h1 style="text-align: center; margin-bottom: 40px;">DYNAMIC WALLET</h1>
    """, unsafe_allow_html=True)
    
    # Create two columns for buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Saídas", key="expense_button", use_container_width=True):
            st.session_state.page = "categories"
            st.session_state.transaction_type = TransactionType.EXPENSE.value
            st.rerun()
    
    with col2:
        if st.button("Entradas", key="income_button", use_container_width=True):
            st.session_state.page = "categories"
            st.session_state.transaction_type = TransactionType.INCOME.value
            st.rerun()
    
    # Show balance at the bottom
    if st.session_state.transactions:
        df = create_transaction_df(st.session_state.transactions)
        summary = get_period_summary(df)
        
        # Calculate absolute value and determine status
        abs_amount = abs(summary['net_amount'])
        status_text = "A receber" if summary['net_amount'] < 0 else "A entregar" if summary['net_amount'] > 0 else ""
        
        st.markdown("""
        <div class="balance-container">
            <h2>Saldo Total</h2>
            <h1 style="color: {};">{}</h1>
            <p>{}</p>
        </div>
        """.format(
            '#ff4b4b' if summary['net_amount'] < 0 else '#4CAF50',
            format_currency(abs_amount),
            status_text
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
    
    st.subheader(f"{'Saída' if st.session_state.transaction_type == TransactionType.EXPENSE.value else 'Entrada'} - {st.session_state.category}")
    
    if st.session_state.category == ExpenseCategory.MEAL.value:
        # Initialize session state for meal form
        if "meal_total_amount" not in st.session_state:
            st.session_state.meal_total_amount = 0.0
        if "meal_num_people" not in st.session_state:
            st.session_state.meal_num_people = 1
        if "collaborator_names" not in st.session_state:
            st.session_state.collaborator_names = [""]
        if "meal_date" not in st.session_state:
            st.session_state.meal_date = datetime.now().date()
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.meal_date,
            key="meal_date_input"
        )
        if selected_date != st.session_state.meal_date:
            st.session_state.meal_date = selected_date
            st.rerun()
        
        # Create two columns for the main inputs
        col1, col2 = st.columns(2)
        
        with col1:
            new_total_amount = st.number_input(
                "Valor da Fatura (€)", 
                min_value=0.0, 
                step=0.5,
                value=st.session_state.meal_total_amount,
                key="total_amount_input"
            )
            if new_total_amount != st.session_state.meal_total_amount:
                st.session_state.meal_total_amount = new_total_amount
                st.rerun()
        
        with col2:
            new_num_people = st.number_input(
                "Número de Colaboradores", 
                min_value=1, 
                step=1,
                value=st.session_state.meal_num_people,
                key="num_people_input"
            )
            if new_num_people != st.session_state.meal_num_people:
                st.session_state.meal_num_people = new_num_people
                # Update collaborator names list
                if len(st.session_state.collaborator_names) < new_num_people:
                    st.session_state.collaborator_names.extend([""] * (new_num_people - len(st.session_state.collaborator_names)))
                else:
                    st.session_state.collaborator_names = st.session_state.collaborator_names[:new_num_people]
                st.rerun()
        
        meal_type = st.selectbox("Tipo", [meal.value for meal in MealType])
        
        # Collaborator name fields
        for i in range(st.session_state.meal_num_people):
            st.session_state.collaborator_names[i] = st.text_input(
                f"Colaborador {i+1}", 
                value=st.session_state.collaborator_names[i],
                key=f"collaborator_{i}"
            )
        
        # Create description with collaborator names
        names_str = ", ".join(st.session_state.collaborator_names) if all(st.session_state.collaborator_names) else f"{st.session_state.meal_num_people} colaboradores"
        description = f"{meal_type} com {names_str} (Fatura: {format_currency(st.session_state.meal_total_amount)})"

        # Add more spacing after collaborator fields
        st.write("")
        st.write("")
        st.write("")
        
        # Calculate and always display amount
        calculated_amount = 0
        if st.session_state.meal_total_amount > 0 and st.session_state.meal_num_people > 0:
            calculated_amount, _ = calculate_meal_expense(
                st.session_state.meal_total_amount, 
                st.session_state.meal_num_people, 
                meal_type
            )
        
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <h2 style="color: #4CAF50; font-size: 24px; text-align: center; margin: 0;">{format_currency(calculated_amount)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_meal"):
                # Validate all fields are filled
                validation_error = None
                if st.session_state.meal_total_amount <= 0:
                    validation_error = "Por favor, insira um valor válido para a fatura"
                elif not all(name.strip() for name in st.session_state.collaborator_names):
                    validation_error = "Por favor, preencha os nomes de todos os colaboradores"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    amount, error = calculate_meal_expense(
                        st.session_state.meal_total_amount, 
                        st.session_state.meal_num_people, 
                        meal_type
                    )
                    if not error:
                        description = f"{meal_type} com {names_str} (Fatura: {format_currency(st.session_state.meal_total_amount)}, Valor por pessoa: {format_currency(calculated_amount)})"
                        save_transaction(
                            st.session_state.meal_date,
                            TransactionType.EXPENSE.value, 
                            ExpenseCategory.MEAL.value, 
                            description, 
                            amount
                        )
                        st.success("Transação registrada com sucesso!")
                        # Reset form state
                        del st.session_state.meal_total_amount
                        del st.session_state.meal_num_people
                        del st.session_state.collaborator_names
                        del st.session_state.meal_date
                        st.session_state.page = "main"
                        st.rerun()
                    else:
                        st.error(error)
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.category == ExpenseCategory.HR.value:
        # Initialize session state for HR form
        if "hr_role" not in st.session_state:
            st.session_state.hr_role = ""
        if "hr_collaborator" not in st.session_state:
            st.session_state.hr_collaborator = ""
        if "hr_date" not in st.session_state:
            st.session_state.hr_date = datetime.now().date()
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.hr_date,
            key="hr_date_input"
        )
        if selected_date != st.session_state.hr_date:
            st.session_state.hr_date = selected_date
            st.rerun()
        
        # Collaborator name field
        new_collaborator = st.text_input(
            "Nome do Colaborador",
            value=st.session_state.hr_collaborator,
            key="hr_collaborator_input"
        )
        if new_collaborator != st.session_state.hr_collaborator:
            st.session_state.hr_collaborator = new_collaborator
            st.rerun()
        
        # Role selection
        new_role = st.selectbox(
            "Função",
            options=list(HR_RATES.keys()),
            key="hr_role_input"
        )
        if new_role != st.session_state.hr_role:
            st.session_state.hr_role = new_role
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Calculate and display amount
        amount = HR_RATES[st.session_state.hr_role]
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <h2 style="color: #4CAF50; font-size: 24px; text-align: center; margin: 0;">{format_currency(amount)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_hr"):
                # Validate fields
                validation_error = None
                if not st.session_state.hr_collaborator.strip():
                    validation_error = "Por favor, insira o nome do colaborador"
                elif not st.session_state.hr_role:
                    validation_error = "Por favor, selecione uma função"
                elif HR_RATES[st.session_state.hr_role] <= 0:
                    validation_error = "Por favor, selecione uma função válida"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"{st.session_state.hr_collaborator} - {st.session_state.hr_role} (Taxa: {format_currency(HR_RATES[st.session_state.hr_role])})"
                    save_transaction(
                        st.session_state.hr_date,
                        TransactionType.EXPENSE.value,
                        ExpenseCategory.HR.value,
                        description,
                        HR_RATES[st.session_state.hr_role]
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.hr_role
                    del st.session_state.hr_collaborator
                    del st.session_state.hr_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.category == ExpenseCategory.OTHER.value:
        # Initialize session state for purchase form
        if "purchase_what" not in st.session_state:
            st.session_state.purchase_what = ""
        if "purchase_amount" not in st.session_state:
            st.session_state.purchase_amount = 0.0
        if "purchase_justification" not in st.session_state:
            st.session_state.purchase_justification = ""
        if "purchase_date" not in st.session_state:
            st.session_state.purchase_date = datetime.now().date()
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.purchase_date,
            key="purchase_date_input"
        )
        if selected_date != st.session_state.purchase_date:
            st.session_state.purchase_date = selected_date
            st.rerun()
        
        # What field
        new_what = st.text_input(
            "O quê?",
            value=st.session_state.purchase_what,
            key="purchase_what_input"
        )
        if new_what != st.session_state.purchase_what:
            st.session_state.purchase_what = new_what
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor da Fatura (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.purchase_amount,
            key="purchase_amount_input"
        )
        if new_amount != st.session_state.purchase_amount:
            st.session_state.purchase_amount = new_amount
            st.rerun()
        
        # Justification field
        new_justification = st.text_area(
            "Justificação",
            value=st.session_state.purchase_justification,
            key="purchase_justification_input"
        )
        if new_justification != st.session_state.purchase_justification:
            st.session_state.purchase_justification = new_justification
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Display amount
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <h2 style="color: #4CAF50; font-size: 24px; text-align: center; margin: 0;">{format_currency(st.session_state.purchase_amount)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_purchase"):
                # Validate fields
                validation_error = None
                if not st.session_state.purchase_what.strip():
                    validation_error = "Por favor, especifique o que foi comprado"
                elif st.session_state.purchase_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                elif not st.session_state.purchase_justification.strip():
                    validation_error = "Por favor, forneça uma justificação"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"{st.session_state.purchase_what} (Valor: {format_currency(st.session_state.purchase_amount)}) - {st.session_state.purchase_justification}"
                    save_transaction(
                        st.session_state.purchase_date,
                        TransactionType.EXPENSE.value,
                        ExpenseCategory.OTHER.value,
                        description,
                        st.session_state.purchase_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.purchase_what
                    del st.session_state.purchase_amount
                    del st.session_state.purchase_justification
                    del st.session_state.purchase_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.category == ExpenseCategory.DELIVERY.value:
        # Initialize session state for delivery form
        if "delivery_collaborator" not in st.session_state:
            st.session_state.delivery_collaborator = ""
        if "delivery_amount" not in st.session_state:
            st.session_state.delivery_amount = 0.0
        if "delivery_date" not in st.session_state:
            st.session_state.delivery_date = datetime.now().date()
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.delivery_date,
            key="delivery_date_input"
        )
        if selected_date != st.session_state.delivery_date:
            st.session_state.delivery_date = selected_date
            st.rerun()
        
        # Collaborator name field
        new_collaborator = st.text_input(
            "Nome do Colaborador",
            value=st.session_state.delivery_collaborator,
            key="delivery_collaborator_input"
        )
        if new_collaborator != st.session_state.delivery_collaborator:
            st.session_state.delivery_collaborator = new_collaborator
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.delivery_amount,
            key="delivery_amount_input"
        )
        if new_amount != st.session_state.delivery_amount:
            st.session_state.delivery_amount = new_amount
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Display amount
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <h2 style="color: #4CAF50; font-size: 24px; text-align: center; margin: 0;">{format_currency(st.session_state.delivery_amount)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_delivery"):
                # Validate fields
                validation_error = None
                if not st.session_state.delivery_collaborator.strip():
                    validation_error = "Por favor, insira o nome do colaborador"
                elif st.session_state.delivery_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"Entregue a {st.session_state.delivery_collaborator} (Valor: {format_currency(st.session_state.delivery_amount)})"
                    save_transaction(
                        st.session_state.delivery_date,
                        TransactionType.EXPENSE.value,
                        ExpenseCategory.DELIVERY.value,
                        description,
                        st.session_state.delivery_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.delivery_collaborator
                    del st.session_state.delivery_amount
                    del st.session_state.delivery_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.category == IncomeCategory.SERVICE.value:
        # Initialize session state for service form
        if "service_reference" not in st.session_state:
            st.session_state.service_reference = ""
        if "service_amount" not in st.session_state:
            st.session_state.service_amount = 0.0
        if "service_date" not in st.session_state:
            st.session_state.service_date = datetime.now().date()
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.service_date,
            key="service_date_input"
        )
        if selected_date != st.session_state.service_date:
            st.session_state.service_date = selected_date
            st.rerun()
        
        # Reference number field
        new_reference = st.text_input(
            "Número do Serviço",
            value=st.session_state.service_reference,
            key="service_reference_input"
        )
        if new_reference != st.session_state.service_reference:
            st.session_state.service_reference = new_reference
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.service_amount,
            key="service_amount_input"
        )
        if new_amount != st.session_state.service_amount:
            st.session_state.service_amount = new_amount
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Display amount
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <h2 style="color: #4CAF50; font-size: 24px; text-align: center; margin: 0;">{format_currency(st.session_state.service_amount)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_service"):
                # Validate fields
                validation_error = None
                if not st.session_state.service_reference.strip():
                    validation_error = "Por favor, insira o número do serviço"
                elif st.session_state.service_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"Serviço #{st.session_state.service_reference} (Valor: {format_currency(st.session_state.service_amount)})"
                    save_transaction(
                        st.session_state.service_date,
                        TransactionType.INCOME.value,
                        IncomeCategory.SERVICE.value,
                        description,
                        st.session_state.service_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.service_reference
                    del st.session_state.service_amount
                    del st.session_state.service_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.category == IncomeCategory.DELIVERY.value:
        # Initialize session state for delivery income form
        if "delivery_income_collaborator" not in st.session_state:
            st.session_state.delivery_income_collaborator = ""
        if "delivery_income_amount" not in st.session_state:
            st.session_state.delivery_income_amount = 0.0
        if "delivery_income_date" not in st.session_state:
            st.session_state.delivery_income_date = datetime.now().date()
        
        # Date input at the top
        selected_date = st.date_input(
            "Data",
            value=st.session_state.delivery_income_date,
            key="delivery_income_date_input"
        )
        if selected_date != st.session_state.delivery_income_date:
            st.session_state.delivery_income_date = selected_date
            st.rerun()
        
        # Collaborator name field
        new_collaborator = st.text_input(
            "Nome do Colaborador",
            value=st.session_state.delivery_income_collaborator,
            key="delivery_income_collaborator_input"
        )
        if new_collaborator != st.session_state.delivery_income_collaborator:
            st.session_state.delivery_income_collaborator = new_collaborator
            st.rerun()
        
        # Amount field
        new_amount = st.number_input(
            "Valor (€)",
            min_value=0.0,
            step=0.5,
            value=st.session_state.delivery_income_amount,
            key="delivery_income_amount_input"
        )
        if new_amount != st.session_state.delivery_income_amount:
            st.session_state.delivery_income_amount = new_amount
            st.rerun()
        
        # Add spacing
        st.write("")
        st.write("")
        st.write("")
        
        # Display amount
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <h2 style="color: #4CAF50; font-size: 24px; text-align: center; margin: 0;">{format_currency(st.session_state.delivery_income_amount)}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Add space before submit button
        
        # Add submit button
        submit_button_container = st.container()
        with submit_button_container:
            st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
            if st.button("Submeter", key="submit_delivery_income"):
                # Validate fields
                validation_error = None
                if not st.session_state.delivery_income_collaborator.strip():
                    validation_error = "Por favor, insira o nome do colaborador"
                elif st.session_state.delivery_income_amount <= 0:
                    validation_error = "Por favor, insira um valor válido"
                
                if validation_error:
                    st.error(validation_error)
                else:
                    description = f"Recebido de {st.session_state.delivery_income_collaborator} (Valor: {format_currency(st.session_state.delivery_income_amount)})"
                    save_transaction(
                        st.session_state.delivery_income_date,
                        TransactionType.INCOME.value,
                        IncomeCategory.DELIVERY.value,
                        description,
                        st.session_state.delivery_income_amount
                    )
                    st.success("Transação registrada com sucesso!")
                    # Reset form state
                    del st.session_state.delivery_income_collaborator
                    del st.session_state.delivery_income_amount
                    del st.session_state.delivery_income_date
                    st.session_state.page = "main"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        with st.form("transaction_form", clear_on_submit=True):
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            date = st.date_input("Data", datetime.now())
            amount = None
            error = None
            
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
    # Create tabs
    tab1, tab2 = st.tabs(["Registar", "Relatório"])
    
    with tab1:
        # Reset to main page when Registar tab is selected
        if tab1:
            st.session_state.page = "main"
            st.session_state.transaction_type = None
        
        if st.session_state.page == "main":
            show_main_page()
        elif st.session_state.page == "categories":
            show_categories()
        elif st.session_state.page == "form":
            show_form()
    
    with tab2:
        # Simple title for the report tab
        st.subheader("Relatório")
        
        if st.session_state.transactions:
            df = create_transaction_df(st.session_state.transactions)
            
            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                type_filter = st.selectbox(
                    "Tipo",
                    options=["Todos", TransactionType.EXPENSE.value, TransactionType.INCOME.value],
                    key="type_filter"
                )
            
            with col2:
                categories = ([cat.value for cat in ExpenseCategory] + 
                            [cat.value for cat in IncomeCategory])
                category_filter = st.selectbox(
                    "Categoria",
                    options=["Todas"] + categories,
                    key="category_filter"
                )
            
            # Apply filters
            filtered_df = df.copy()
            if type_filter != "Todos":
                filtered_df = filtered_df[filtered_df["Type"] == type_filter]
            if category_filter != "Todas":
                filtered_df = filtered_df[filtered_df["Category"] == category_filter]
            
            # Split dataframe by type
            income_df = filtered_df[filtered_df["Type"] == TransactionType.INCOME.value].copy()
            expense_df = filtered_df[filtered_df["Type"] == TransactionType.EXPENSE.value].copy()
            
            # Sort each dataframe by date
            income_df = income_df.sort_values("Date", ascending=True)
            expense_df = expense_df.sort_values("Date", ascending=True)
            
            # Format amounts for display
            income_df["Amount"] = income_df["Amount"].apply(format_currency)
            expense_df["Amount"] = expense_df["Amount"].apply(format_currency)
            
            # Format dates to dd/MM
            income_df["Date"] = pd.to_datetime(income_df["Date"]).dt.strftime("%d/%m")
            expense_df["Date"] = pd.to_datetime(expense_df["Date"]).dt.strftime("%d/%m")
            
            # Clean up descriptions by removing redundant valor information
            def clean_description(row):
                desc = row["Description"]
                amount = row["Amount"]
                # Remove the valor part if it matches the final amount
                if f"Valor: {amount}" in desc:
                    desc = desc.replace(f" (Valor: {amount})", "")
                return desc
            
            # Only apply clean_description if DataFrames are not empty
            if not income_df.empty:
                income_df["Description"] = income_df.apply(clean_description, axis=1)
            if not expense_df.empty:
                expense_df["Description"] = expense_df.apply(clean_description, axis=1)
            
            # Display income transactions if they exist
            if not income_df.empty:
                st.markdown("<h4 style='font-size: 18px;'>Entradas</h4>", unsafe_allow_html=True)
                for _, row in income_df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background-color: #1E1E1E;
                            border-left: 4px solid #4CAF50;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="color: #CCCCCC;">{row['Date']}</span>
                                <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <span style="background-color: rgba(76, 175, 80, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                    {row['Category']}
                                </span>
                            </div>
                            <div style="color: #FFFFFF; margin-top: 0.5rem;">
                                {row['Description']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Display expense transactions if they exist
            if not expense_df.empty:
                st.markdown("<h4 style='font-size: 18px;'>Saídas</h4>", unsafe_allow_html=True)
                for _, row in expense_df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background-color: #1E1E1E;
                            border-left: 4px solid #ff4b4b;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="color: #CCCCCC;">{row['Date']}</span>
                                <span style="font-weight: 500; color: #FFFFFF;">{row['Amount']}</span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <span style="background-color: rgba(255, 75, 75, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9em; color: #FFFFFF;">
                                    {row['Category']}
                                </span>
                            </div>
                            <div style="color: #FFFFFF; margin-top: 0.5rem;">
                                {row['Description']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Calculate summary statistics
            total_income = df[df["Type"] == TransactionType.INCOME.value]["Amount"].sum()
            total_expense = df[df["Type"] == TransactionType.EXPENSE.value]["Amount"].sum()
            net_amount = total_income - total_expense
            
            # Show summary statistics
            st.write("")
            
            # Create a more visible summary section with line-by-line format
            st.markdown("""
            <div style="margin: 20px 0;">
                <div style="margin-bottom: 15px;">
                    <span style="font-size: 20px; color: white; font-weight: 500;">Resumo:</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 16px; color: white;">Total Entradas: </span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">{}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 16px; color: white;">Total Saídas: </span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">{}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 16px; color: white;">Saldo: </span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">{}</span>
                    <span style="font-size: 16px; color: white !important; font-weight: 500;">({})</span>
                </div>
            </div>
            """.format(
                format_currency(total_income),
                format_currency(total_expense),
                format_currency(abs(net_amount)),
                'A entregar' if net_amount >= 0 else 'A receber'
            ), unsafe_allow_html=True)
            
            # Add submit button
            st.write("")
            submit_button_container = st.container()
            with submit_button_container:
                st.markdown('<div class="meal-submit-button">', unsafe_allow_html=True)
                if st.button("Submeter Relatório", key="submit_report"):
                    pass  # Functionality to be added later
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Não existem transações registradas.")

if __name__ == "__main__":
    main() 