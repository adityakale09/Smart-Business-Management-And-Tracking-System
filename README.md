# Smart Business Management & Tracking System

A comprehensive business platform integrating sales, inventory, and employee management with real-time tracking and AI-powered analytics.

## 🎯 Objectives

1. **Modular & Scalable**: Adaptable to any business size or type
2. **Role-Based Access Control**: Admin, Manager, Employee, and Vendor roles
3. **AI Automation**: Automate repetitive tasks to improve efficiency
4. **Real-Time Tracking**: Track all financial and operational activities
5. **AI Analytics**: Data-driven decision-making with forecasting capabilities

## 🛠️ Tech Stack

- **Frontend**: React.js with Chart.js/D3.js for visualizations
- **Backend**: Python FastAPI
- **Databases**: PostgreSQL (structured data) + MongoDB (document storage)
- **OS**: Windows compatible

## 📁 Project Structure

```
pro_ject/
├── frontend/          # React.js application
├── backend/           # FastAPI application
├── database/          # Database scripts and migrations
└── docs/              # Documentation
```

## 🚀 Getting Started

### Quick Start

1. **Set up databases** (PostgreSQL and MongoDB)
2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   cp .env.example .env  # Edit with your database credentials
   python main.py
   ```

3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Create your first admin user** via API or Swagger UI at `http://localhost:8000/docs`

For detailed setup instructions, see [SETUP.md](SETUP.md)

### Prerequisites

- Node.js (v16+)
- Python (v3.9+)
- PostgreSQL
- MongoDB

## 🔐 User Roles

- **Admin**: Full system access
- **Manager**: Department management and analytics
- **Employee**: Limited access to assigned tasks
- **Vendor**: External vendor access for inventory

## 📊 Features

- Sales Management & Tracking
- Inventory Management
- Employee Management
- Real-Time Analytics Dashboard
- AI-Powered Forecasting
- Automated Task Management

## 📚 Documentation

- [Setup Guide](SETUP.md) - Detailed installation and configuration instructions
- [API Documentation](docs/API.md) - Complete API reference

## 🔗 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


