from enum import Enum

# Transaction Types
class TransactionType(Enum):
    EXPENSE = "Despesa"
    INCOME = "Receita"

# Expense Categories
class ExpenseCategory(Enum):
    MEAL = "Refeição"
    HR = "Recursos Humanos"
    OTHER = "Outro"

# Income Categories
class IncomeCategory(Enum):
    SERVICE = "Serviço"
    COLLABORATOR = "Recebi de um colaborador"
    OTHER = "Outro"

# HR Rates (€/hour)
HR_RATES = {
    "Senior Developer": 45,
    "Mid Developer": 35,
    "Junior Developer": 25,
    "Project Manager": 50,
    "Designer": 40
}

# Meal Limits
MAX_MEAL_ALLOWANCE_PER_PERSON = 12  # €

# Date Format
DATE_FORMAT = "%Y-%m-%d"

# CSV Export Headers
TRANSACTION_HEADERS = [
    "Date",
    "Type",
    "Category",
    "Description",
    "Amount",
    "Reference",
    "Number of People",
    "Hours",
    "Role"
] 