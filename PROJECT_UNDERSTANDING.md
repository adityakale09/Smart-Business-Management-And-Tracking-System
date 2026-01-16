# 🚀 Project Understanding - Smart Business Management System

## 📌 Overview

This is a **full-stack business management application** that helps businesses track:
- Sales and revenue
- Inventory (with OCR receipt scanning)
- Employee management  
- Analytics and AI-powered forecasting

## 🏗️ Architecture

### Backend (FastAPI - Python)
- **Framework**: FastAPI (modern, fast Python web framework)
- **Port**: 8000
- **Location**: `backend/` folder
- **Main file**: `backend/main.py`

**Key Features:**
- RESTful API with auto-generated documentation (Swagger UI)
- JWT authentication with role-based access control
- OCR for receipt processing (Tesseract)
- AI/ML forecasting with scikit-learn
- Async support with Motor (MongoDB) and SQLAlchemy (PostgreSQL)

**API Endpoints:**
- `/api/auth` - Authentication (login, register, token refresh)
- `/api/sales` - Sales management
- `/api/inventory` - Inventory tracking
- `/api/employees` - Employee management
- `/api/analytics` - Business analytics & reports
- `/api/ai` - AI automation features
- `/api/receipts` - OCR receipt processing

### Frontend (React + Vite)
- **Framework**: React 18 with Vite
- **Port**: 5173 (dev server)
- **Location**: `frontend/` folder
- **State Management**: Zustand
- **Charts**: Chart.js, D3.js, Recharts

**Pages:**
- Login page
- Dashboard (overview)
- Sales management
- Inventory management
- Employees management
- Analytics & Reports
- Receipt upload & processing

### Databases

#### PostgreSQL (Primary Database)
- **Purpose**: Structured data storage
- **Port**: 5432
- **Database**: `business_management`
- **Status**: ❌ **NEEDS PASSWORD FIX**

**Tables:**
- `users` - User authentication and roles
- `employees` - Employee information
- `inventory` - Product inventory
- `sales` - Sales transactions
- `receipts` - Receipt metadata

#### MongoDB (Document Store)
- **Purpose**: Document storage (images, logs, analytics)
- **Port**: 27017
- **Database**: `business_management`
- **Status**: ✅ **WORKING**

**Collections:**
- Analytics data
- Receipt images
- AI model data
- Logs

## 👥 User Roles

1. **Admin** - Full system access, user management
2. **Manager** - Department oversight, reports, analytics
3. **Employee** - Limited access to assigned tasks
4. **Vendor** - External access for inventory management

## 📦 Tech Stack Summary

### Backend Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - PostgreSQL ORM
- `pymongo` / `motor` - MongoDB drivers
- `python-jose` - JWT tokens
- `passlib` - Password hashing
- `pytesseract` - OCR engine
- `pdf2image` - PDF to image conversion
- `openai` - AI integration
- `pandas` / `numpy` / `scikit-learn` - Data analysis & ML
- `redis` / `celery` - Background tasks

### Frontend Dependencies
- `react` / `react-dom` - UI library
- `react-router-dom` - Routing
- `axios` - HTTP client
- `chart.js` / `d3` / `recharts` - Charts
- `zustand` - State management
- `react-hook-form` - Form handling
- `lucide-react` - Icons

## 🔧 Current Status

### ✅ What's Working:
1. Python virtual environment created
2. All backend dependencies installed (24 packages)
3. MongoDB connection successful
4. Project structure complete
5. All code files present and organized

### ❌ What's Not Working:
1. **PostgreSQL authentication failed**
   - Current password in `.env`: `12345678@aB`
   - Error: "password authentication failed for user postgres"
   - **Action needed**: Reset PostgreSQL password

### 📋 What Hasn't Been Tested Yet:
1. Frontend setup (npm install)
2. Database initialization (tables creation)
3. API endpoints
4. Frontend-backend integration

## 🚀 How to Run (Once PostgreSQL is Fixed)

### 1. Fix PostgreSQL Password
See `FIX_POSTGRES.md` for detailed instructions.

**Quick fix using pgAdmin:**
1. Open pgAdmin 4
2. Reset postgres user password
3. Update `.env` file with new password
4. Create `business_management` database

### 2. Initialize Database
```powershell
cd backend
.\venv\Scripts\python.exe init_database.py
```

This will:
- Create all required tables in PostgreSQL
- Set up MongoDB collections
- Create initial admin user (optional)

### 3. Start Backend Server
```powershell
cd backend
.\venv\Scripts\python.exe main.py
```

Access points:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health

### 4. Start Frontend Development Server
```powershell
cd frontend
npm install  # First time only
npm run dev
```

Access: http://localhost:5173

## 📁 Important Files

### Configuration
- `backend/.env` - Environment variables (DATABASE CREDENTIALS)
- `backend/app/core/config.py` - App settings
- `frontend/vite.config.js` - Vite configuration

### Database
- `database/init.sql` - Initial database schema
- `backend/init_database.py` - Database initialization script
- `backend/test_db_connection.py` - Connection test utility

### Documentation
- `README.md` - Project overview
- `SETUP.md` - Setup instructions
- `DATABASE_SETUP.md` - Database setup guide
- `docs/API.md` - API documentation
- `backend/FIX_POSTGRES.md` - PostgreSQL fix guide (CREATED NOW)

## 🎯 Next Steps

### Immediate (Required):
1. ✅ Understand project structure (DONE)
2. ✅ Install backend dependencies (DONE)
3. ✅ Test database connections (DONE - MongoDB OK, PostgreSQL needs fix)
4. ❌ **Fix PostgreSQL password** (NEEDS YOUR ACTION)
5. ⏳ Initialize database tables
6. ⏳ Install frontend dependencies
7. ⏳ Start both servers

### After Basic Setup:
1. Create first admin user
2. Test authentication
3. Upload sample data
4. Test receipt OCR
5. Configure AI/OpenAI API key (if using AI features)

## 🔑 Default Credentials (After Setup)

The first admin user will need to be created via:
- API endpoint: `POST /api/auth/register`
- Or via Swagger UI: http://localhost:8000/docs
- Or via init script with seed data

## 📊 Features Overview

### Core Features:
✅ User authentication & authorization
✅ Sales tracking and management
✅ Inventory management
✅ Employee management
✅ Receipt OCR processing
✅ Analytics dashboard
✅ Real-time data updates

### Advanced Features:
✅ AI-powered sales forecasting
✅ Automated task management
✅ Role-based permissions
✅ Real-time notifications (WebSockets ready)
✅ RESTful API with documentation
✅ MongoDB for flexible data storage

## 🐛 Known Issues

1. **PostgreSQL Password**: Main blocker - see FIX_POSTGRES.md
2. **OCR Dependencies**: May need Tesseract OCR installed separately
3. **OpenAI API**: Requires API key in .env for AI features

## 💡 Tips

- Use the Swagger UI at `/docs` for testing API endpoints
- Check `/api/health` to verify both databases are connected
- MongoDB will auto-create collections on first use
- PostgreSQL tables must be created via init_database.py

## 📞 Support Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- React Docs: https://react.dev/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- MongoDB Docs: https://www.mongodb.com/docs/
