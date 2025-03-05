# MD Wallet - Expense Tracker

A comprehensive expense and income tracking application built with Streamlit. The app helps users manage their financial transactions with a structured reporting system organized by weekly periods.

## Features

- **Transaction Management**
  - Record expenses in categories: Meals, HR, and Other
  - Record income from services, collaborators, and other sources
  - Automatic calculations for meal allowances and HR rates
  - Input validation and error handling

- **Reporting System**
  - Weekly period tracking (Monday to Sunday)
  - Late submission detection
  - Summary statistics and metrics
  - Transaction history view

- **Data Visualization & Export**
  - Tabular view of transactions
  - Pie chart for expense distribution
  - CSV export functionality

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd md-wallet
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app/main.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Use the application:
   - Select "Record Transaction" to add new expenses or income
   - View "Reports" to see summaries and download transaction data
   - Track your weekly financial activity

## Configuration

- Meal allowance limit is set to €12 per person
- HR rates are predefined for different roles
- All amounts are in Euros (€)

## Data Storage

Currently, the application uses Streamlit's session state for data storage. Data persists only during the active session. When you close the application, the data will be reset.

## Future Enhancements

- User authentication system
- Database integration for permanent storage
- Additional visualization options
- PDF report generation
- Mobile-optimized interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 