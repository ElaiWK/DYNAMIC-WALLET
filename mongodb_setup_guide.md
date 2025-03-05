# MongoDB Atlas Setup Guide for MD Wallet

This guide will help you set up a free MongoDB Atlas database to store your application data. MongoDB Atlas is a cloud-based database service that offers a free tier with 512MB of storage, which is more than enough for this application.

## Step 1: Create a MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account using your email address
3. Complete the registration process

## Step 2: Create a Free Cluster

1. After logging in, click "Build a Database"
2. Select the "FREE" tier option
3. Choose a cloud provider (AWS, Google Cloud, or Azure) and a region closest to your users
4. Click "Create Cluster" (this may take a few minutes to provision)

## Step 3: Set Up Database Access

1. In the left sidebar, click "Database Access" under "Security"
2. Click "Add New Database User"
3. Create a username and password (make sure to save these credentials)
4. Set "Database User Privileges" to "Read and write to any database"
5. Click "Add User"

## Step 4: Set Up Network Access

1. In the left sidebar, click "Network Access" under "Security"
2. Click "Add IP Address"
3. To allow access from anywhere (for development), click "Allow Access from Anywhere"
4. Click "Confirm"

## Step 5: Get Your Connection String

1. In the left sidebar, click "Database" under "Deployments"
2. Click "Connect" on your cluster
3. Select "Connect your application"
4. Copy the connection string (it will look like: `mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority`)
5. Replace `<username>` and `<password>` with the credentials you created in Step 3
6. Replace `<dbname>` with `dynamic_wallet_db`

## Step 6: Configure Your Application

### For Local Development:

1. Create a `.env` file in the root directory of your project
2. Add the following line to the file:
   ```
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/dynamic_wallet_db?retryWrites=true&w=majority
   ```
3. Replace `<username>`, `<password>`, and `<cluster>` with your actual values

### For Streamlit Cloud Deployment:

1. Go to your Streamlit Cloud dashboard
2. Select your app
3. Click on "Secrets"
4. Add the following to your secrets:
   ```yaml
   mongo:
     uri: "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/dynamic_wallet_db?retryWrites=true&w=majority"
   ```
5. Replace `<username>`, `<password>`, and `<cluster>` with your actual values

## Step 7: Test Your Connection

1. Run your application locally
2. Add some transactions and navigate between tabs
3. Check your MongoDB Atlas dashboard to see if data is being stored

## Troubleshooting

If you encounter any issues connecting to MongoDB Atlas:

1. **Connection Errors**: Make sure your IP address is allowed in the Network Access settings
2. **Authentication Errors**: Verify your username and password are correct
3. **Database Not Found**: Make sure you've replaced `<dbname>` with `dynamic_wallet_db`
4. **Data Not Saving**: Check the application logs for any error messages

## Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/en/stable/)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management) 