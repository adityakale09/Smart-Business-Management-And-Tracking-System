# Database Setup and Troubleshooting Guide

## Quick Setup

### 1. Create the Database

**PostgreSQL:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE business_management;

# Exit
\q
```

**MongoDB:**
- MongoDB database will be created automatically when first accessed
- No manual creation needed

### 2. Create .env File

Create a `.env` file in the `backend` directory with your database credentials:

```env
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=business_management

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=business_management

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
HOST=0.0.0.0
PORT=8000

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Test Database Connection

Before starting the server, test your database connections:

```bash
cd backend
python test_db_connection.py
```

This will:
- Show your current database configuration
- Test PostgreSQL connection
- Test MongoDB connection
- Provide troubleshooting steps if connections fail

### 4. Start the Server

```bash
python main.py
```

The server will:
- Test database connections on startup
- Create all necessary tables automatically
- Show detailed connection status

## Troubleshooting

### PostgreSQL Connection Issues

**Error: "connection refused" or "could not connect"**

1. **Check if PostgreSQL is running:**
   ```bash
   # Windows
   services.msc  # Look for "postgresql" service
   
   # Linux/Mac
   sudo systemctl status postgresql
   # or
   sudo service postgresql status
   ```

2. **Start PostgreSQL if not running:**
   ```bash
   # Windows - Use Services app or:
   net start postgresql-x64-XX
   
   # Linux/Mac
   sudo systemctl start postgresql
   # or
   sudo service postgresql start
   ```

3. **Verify database exists:**
   ```bash
   psql -U postgres -l
   # Look for "business_management" in the list
   ```

4. **Create database if missing:**
   ```bash
   psql -U postgres
   CREATE DATABASE business_management;
   \q
   ```

5. **Test connection manually:**
   ```bash
   psql -h localhost -U postgres -d business_management
   ```

### MongoDB Connection Issues

**Error: "connection refused" or "could not connect"**

1. **Check if MongoDB is running:**
   ```bash
   # Windows
   services.msc  # Look for "MongoDB" service
   
   # Linux/Mac
   sudo systemctl status mongod
   # or
   sudo service mongod status
   ```

2. **Start MongoDB if not running:**
   ```bash
   # Windows - Use Services app or:
   net start MongoDB
   
   # Linux/Mac
   sudo systemctl start mongod
   # or
   sudo service mongod start
   ```

3. **Test connection manually:**
   ```bash
   mongosh mongodb://localhost:27017
   ```

### Common Issues

**Issue: "Field required" errors when submitting forms**

This usually means:
1. Database connection is failing silently
2. Tables haven't been created
3. Database credentials are incorrect

**Solution:**
1. Run `python test_db_connection.py` to verify connections
2. Check server startup logs for database errors
3. Verify `.env` file exists and has correct credentials
4. Check `/api/health` endpoint: `http://localhost:8000/api/health`

**Issue: Server starts but API calls fail**

1. Check database connection status:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check server logs for error messages

3. Verify database tables exist:
   ```bash
   psql -U postgres -d business_management -c "\dt"
   ```

## Health Check Endpoint

You can check database status anytime by calling:

```bash
curl http://localhost:8000/api/health
```

Or visit in browser: `http://localhost:8000/api/health`

This returns:
```json
{
  "status": "healthy",
  "postgresql": {
    "connected": true,
    "message": "PostgreSQL connection successful"
  },
  "mongodb": {
    "connected": true,
    "message": "MongoDB connection successful"
  }
}
```

## Next Steps

Once database connections are working:

1. Start the backend server: `python main.py`
2. Check health endpoint to confirm connections
3. Create your first user via API or Swagger UI
4. Start using the application!

