from enum import Enum

# Transaction Types
class TransactionType(Enum):
    EXPENSE = "Saída"
    INCOME = "Entrada"

# Expense Categories
class ExpenseCategory(Enum):
    MEAL = "Refeição"
    HR = "Recursos Humanos"
    PURCHASE = "Compra"
    DELIVERED = "Entreguei"

# Income Categories
class IncomeCategory(Enum):
    SERVICE = "Serviço"
    RECEIVED = "Recebi"

# Meal Types
class MealType(Enum):
    LUNCH = "Almoço"
    DINNER = "Jantar"

# HR Rates (€/hour)
HR_RATES = {
    "Júnior": 35,
    "Júnior mais de 10 horas": 40,
    "Sénior": 40,
    "Sénior mais de 10 horas": 50,
    "Condutor": 55,
    "Condutor mais de 10 horas": 65,
    "Operador": 40,
    "Pinturas": 55,
    "Pinturas e Kit": 65,
    "Balões": 45,
    "Balões e Kit": 55,
    "Animador": 80
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