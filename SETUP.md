# Setup Guide - Smart Business Management & Tracking System

## Prerequisites

Before setting up the project, ensure you have the following installed:

1. **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
2. **Python** (v3.9 or higher) - [Download](https://www.python.org/downloads/)
3. **PostgreSQL** - [Download](https://www.postgresql.org/download/)
4. **MongoDB** - [Download](https://www.mongodb.com/try/download/community)
5. **Git** (optional) - [Download](https://git-scm.com/downloads)

## Step 1: Database Setup

### PostgreSQL Setup

1. Install PostgreSQL and start the service
2. Create a new database:
   ```sql
   CREATE DATABASE business_management;
   ```
3. Note your PostgreSQL credentials (username, password, host, port)

### MongoDB Setup

1. Install MongoDB and start the service
2. MongoDB will run on `localhost:27017` by default
3. No initial database creation needed - it will be created automatically

## Step 2: Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the `backend` directory:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file with your database credentials:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=business_management
   
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB=business_management
   
   SECRET_KEY=your-secret-key-here-change-in-production
   ```

7. Run the backend server:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

## Step 3: Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file (optional, defaults are set):
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## Step 4: Initial User Setup

1. Use the API to create your first admin user:
   ```bash
   curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@example.com",
       "username": "admin",
       "password": "admin123",
       "full_name": "Admin User",
       "role": "admin"
     }'
   ```

2. Or use the Swagger UI at `http://localhost:8000/docs` to register a user

## Step 5: Access the Application

1. Open your browser and navigate to `http://localhost:3000`
2. Login with your credentials
3. Start managing your business!

## Troubleshooting

### Backend Issues

- **Database connection error**: Check PostgreSQL/MongoDB services are running
- **Port already in use**: Change the PORT in `.env` file
- **Module not found**: Ensure virtual environment is activated and dependencies are installed

### Frontend Issues

- **API connection error**: Check backend is running and CORS settings
- **Build errors**: Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in backend `.env`
2. Use a strong `SECRET_KEY`
3. Configure proper CORS origins
4. Use environment variables for all sensitive data
5. Set up proper database backups
6. Use a reverse proxy (nginx) for the frontend
7. Use a production WSGI server (gunicorn) for the backend

## Support

For issues or questions, refer to the main README.md file.



