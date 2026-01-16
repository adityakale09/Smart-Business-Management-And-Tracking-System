# PostgreSQL Password Fix Guide

## Problem
The PostgreSQL password in `.env` file is incorrect, preventing the application from connecting to the database.

## Quick Fix Steps

### Method 1: Using pgAdmin 4 (Easiest)

1. **Launch pgAdmin 4**
   - Location: `C:\Program Files\PostgreSQL\18\pgAdmin 4\runtime\pgAdmin4.exe`
   - Or search for "pgAdmin" in Windows Start menu

2. **Connect to PostgreSQL Server**
   - If it asks for a password, try entering your remembered password
   - If you're logged in, you'll see the server tree on the left

3. **Reset the postgres user password**
   - Expand `Servers` → `PostgreSQL 18` → `Login/Group Roles`
   - Right-click on `postgres` user
   - Select `Properties`
   - Go to `Definition` tab
   - Enter a new password (e.g., `postgres123`)
   - Click `Save`

4. **Update the .env file**
   - Open `.env` in the backend folder
   - Update this line:
     ```
     POSTGRES_PASSWORD=postgres123
     ```
   - Save the file

5. **Create the database (if it doesn't exist)**
   - In pgAdmin, right-click `Databases`
   - Click `Create` → `Database`
   - Name: `business_management`
   - Click `Save`

### Method 2: Using SQL Command (If you can login)

If you can login with any user, run this SQL command:

```sql
ALTER USER postgres WITH PASSWORD 'postgres123';
```

Then update `.env` file with the new password.

### Method 3: Modify pg_hba.conf (Advanced - requires restart)

1. **Edit pg_hba.conf**
   - Location: `C:\Program Files\PostgreSQL\18\data\pg_hba.conf`
   - Open with Notepad as Administrator
   
2. **Temporarily change authentication to trust**
   - Find lines starting with `host` or `local`
   - Change `md5` or `scram-sha-256` to `trust`
   - Example:
     ```
     # Before
     host    all             all             127.0.0.1/32            scram-sha-256
     # After
     host    all             all             127.0.0.1/32            trust
     ```

3. **Restart PostgreSQL service**
   ```powershell
   Restart-Service postgresql-x64-18
   ```

4. **Connect without password and reset**
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres123';"
   ```

5. **Revert pg_hba.conf changes**
   - Change `trust` back to `scram-sha-256`
   - Restart PostgreSQL service again

6. **Update .env file**
   ```
   POSTGRES_PASSWORD=postgres123
   ```

## After Fixing

1. **Test the connection**
   ```powershell
   cd backend
   .\venv\Scripts\python.exe test_db_connection.py
   ```

2. **Initialize the database**
   ```powershell
   .\venv\Scripts\python.exe init_database.py
   ```

3. **Start the backend server**
   ```powershell
   .\venv\Scripts\python.exe main.py
   ```

4. **Open your browser**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Current Database Status

✅ **MongoDB**: Connected and working
❌ **PostgreSQL**: Authentication failed

Current credentials in .env:
- Username: postgres
- Password: 12345678@aB (INCORRECT)
- Host: localhost
- Port: 5432
- Database: business_management

## Need Help?

If you're still having issues:
1. Make sure PostgreSQL service is running (it is: postgresql-x64-18)
2. Try all the passwords you commonly use
3. You might need to reinstall PostgreSQL if you forgot the password
