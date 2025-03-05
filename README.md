# MD Wallet - Expense Tracker

A comprehensive expense and income tracking application built with Streamlit. The app helps users manage their financial transactions with a structured reporting system organized by weekly periods.

## Features

- **User Authentication**
  - Secure login system with password hashing
  - Predefined user accounts with assigned passwords
  - Admin dashboard for viewing all user data
  - Session persistence for staying logged in

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

3. Log in with your credentials or use the predefined accounts:
   - Regular users: Access transaction recording and reports
   - Admin user: Access additional admin dashboard

4. Use the application:
   - Select "Registar" to add new expenses or income
   - View "Relatório" to see summaries of current period
   - Track your "Histórico" for past submitted reports

## Configuration

- Meal allowance limit is set to €12 per person
- HR rates are predefined for different roles
- All amounts are in Euros (€)
- Default admin credentials: username: `admin`, password: `admin123`

## Data Storage

The application uses a file-based storage system:
- User credentials stored in `data/users.json`
- User transactions stored in `data/users/{username}/transactions.json`
- User history stored in `data/users/{username}/history.json`

## Deployment Options

### 1. Streamlit Cloud

For easy deployment with persistent storage:

1. Push your code to a GitHub repository
2. Sign up at [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Deploy the app with these settings:
   - Main file path: `app/main.py`
   - Python version: 3.9+
   - Requirements: Use requirements.txt

### 2. Heroku

For deployment with persistent storage:

1. Add a `Procfile` with the content:
```
web: streamlit run app/main.py --server.port=$PORT
```

2. Create a Heroku app and deploy:
```bash
heroku create md-wallet
git push heroku main
```

3. For persistent storage, add a Heroku add-on:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

4. Modify the app to use the PostgreSQL database for storage instead of files (requires code changes)

### 3. Docker Deployment

1. Create a Dockerfile:
```
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py"]
```

2. Build and run the Docker container:
```bash
docker build -t md-wallet .
docker run -p 8501:8501 -v $(pwd)/data:/app/data md-wallet
```

## Future Enhancements

- User authentication system
- Database integration for permanent storage
- Additional visualization options
- PDF report generation
- Mobile-optimized interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 