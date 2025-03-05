# MD Wallet Database Setup Guide

## Current Setup
Currently, MD Wallet uses a file-based storage system where:
- User data is stored in JSON files in the `data/users/` directory
- Authentication information is stored in `data/config.yaml`

This works for local development but is not suitable for online deployment.

## Database Options for Online Deployment

### 1. SQL Database (Recommended for structured data)

#### Option A: PostgreSQL
- **Pros**: Robust, reliable, excellent for structured data
- **Hosting**: Heroku, AWS RDS, DigitalOcean
- **Cost**: Free tier available on some platforms, then $5-15/month

#### Option B: MySQL/MariaDB
- **Pros**: Widely used, good community support
- **Hosting**: AWS RDS, DigitalOcean, PlanetScale
- **Cost**: Similar to PostgreSQL

### 2. NoSQL Database (Good for flexible schema)

#### Option A: MongoDB
- **Pros**: Flexible schema, good for JSON-like data
- **Hosting**: MongoDB Atlas
- **Cost**: Free tier available, then $9+/month

#### Option B: Firebase Firestore
- **Pros**: Easy to set up, real-time capabilities
- **Hosting**: Google Cloud
- **Cost**: Free tier with generous limits, then pay-as-you-go

## Implementation Steps

### 1. Choose a Database Provider
For a small application like MD Wallet, these are good options:
- **MongoDB Atlas**: Free tier with 512MB storage
- **Supabase**: PostgreSQL with free tier
- **PlanetScale**: MySQL with free tier
- **Firebase**: Document database with free tier

### 2. Set Up Database Connection
Add a database connection file to your project:

```python
# utils/database.py
import os
from pymongo import MongoClient
# Or for SQL:
# import psycopg2
# Or for Firebase:
# import firebase_admin

# Example for MongoDB
def get_database():
    # Get connection string from environment variable
    connection_string = os.environ.get("MONGODB_URI")
    client = MongoClient(connection_string)
    return client["md_wallet_db"]

# Example functions
def save_user_transactions(username, transactions):
    db = get_database()
    db.transactions.update_one(
        {"username": username},
        {"$set": {"transactions": transactions}},
        upsert=True
    )

def load_user_transactions(username):
    db = get_database()
    result = db.transactions.find_one({"username": username})
    return result["transactions"] if result else []
```

### 3. Update Authentication System
For user authentication, consider:
- Continuing with streamlit-authenticator but storing credentials in the database
- Using a service like Auth0, Firebase Auth, or Supabase Auth

### 4. Environment Variables
Store database credentials as environment variables, not in code:

```python
# .env file (don't commit to git)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### 5. Deployment Options

#### Option A: Streamlit Cloud
- Free hosting for public apps
- Connect to your database
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)

#### Option B: Heroku
- Easy deployment
- Free tier available (with limitations)
- [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)

#### Option C: AWS, GCP, or Azure
- More complex but more powerful
- Free tiers available
- Better for production applications

## Security Considerations

1. **Never store database credentials in your code**
2. **Use environment variables for sensitive information**
3. **Implement proper authentication and authorization**
4. **Enable database encryption**
5. **Set up regular backups**

## Migration Plan

1. Create the database schema
2. Write migration scripts to move data from files to database
3. Update application code to use the database
4. Test thoroughly
5. Deploy to your chosen platform

## Need Help?

If you need assistance with setting up a specific database or deploying your application, please let me know which option you prefer, and I can provide more detailed instructions. 