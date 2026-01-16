"""
Analytics and reporting routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.models.sales import Sale
from app.models.inventory import Inventory
from app.models.employee import Employee, EmployeeAttendance

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics"""
    # Sales statistics (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    total_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.created_at >= thirty_days_ago
    ).scalar() or 0
    
    total_sales_count = db.query(func.count(Sale.id)).filter(
        Sale.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Inventory statistics
    total_products = db.query(func.count(Inventory.id)).scalar() or 0
    low_stock_items = db.query(func.count(Inventory.id)).filter(
        Inventory.quantity <= Inventory.reorder_level
    ).scalar() or 0
    
    # Employee statistics
    total_employees = db.query(func.count(Employee.id)).filter(
        Employee.status == "active"
    ).scalar() or 0
    
    return {
        "sales": {
            "total_revenue": float(total_revenue),
            "total_sales": total_sales_count,
            "period": "30 days"
        },
        "inventory": {
            "total_products": total_products,
            "low_stock_items": low_stock_items
        },
        "employees": {
            "total_active": total_employees
        }
    }


@router.get("/sales/trend")
async def get_sales_trend(
    days: int = Query(30, ge=1, le=365),
    group_by: str = Query("day", regex="^(day|week|month)$"),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get sales trend data for visualization"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = db.query(
        func.date(Sale.created_at).label('date'),
        func.sum(Sale.total_amount).label('revenue'),
        func.count(Sale.id).label('count')
    ).filter(
        Sale.created_at >= start_date,
        Sale.created_at <= end_date
    )
    
    if group_by == "day":
        query = query.group_by(func.date(Sale.created_at))
    elif group_by == "week":
        query = query.group_by(
            extract('year', Sale.created_at),
            extract('week', Sale.created_at)
        )
    elif group_by == "month":
        query = query.group_by(
            extract('year', Sale.created_at),
            extract('month', Sale.created_at)
        )
    
    results = query.order_by('date').all()
    
    return {
        "period": f"{days} days",
        "group_by": group_by,
        "data": [
            {
                "date": str(row.date),
                "revenue": float(row.revenue or 0),
                "count": row.count or 0
            }
            for row in results
        ]
    }


@router.get("/inventory/analysis")
async def get_inventory_analysis(
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get inventory analysis data"""
    # Category distribution
    category_stats = db.query(
        Inventory.category,
        func.count(Inventory.id).label('count'),
        func.sum(Inventory.quantity * Inventory.unit_price).label('value')
    ).group_by(Inventory.category).all()
    
    # Low stock items
    low_stock = db.query(Inventory).filter(
        Inventory.quantity <= Inventory.reorder_level
    ).all()
    
    return {
        "category_distribution": [
            {
                "category": row.category or "Uncategorized",
                "count": row.count,
                "total_value": float(row.value or 0)
            }
            for row in category_stats
        ],
        "low_stock_items": [
            {
                "id": item.id,
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "reorder_level": item.reorder_level
            }
            for item in low_stock
        ]
    }


@router.get("/employees/performance")
async def get_employee_performance(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get employee performance metrics"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Sales by employee
    sales_by_employee = db.query(
        Sale.user_id,
        func.count(Sale.id).label('sales_count'),
        func.sum(Sale.total_amount).label('total_revenue')
    ).filter(
        Sale.created_at >= start_date,
        Sale.created_at <= end_date
    ).group_by(Sale.user_id).all()
    
    # Attendance statistics
    attendance_stats = db.query(
        EmployeeAttendance.employee_id,
        func.count(EmployeeAttendance.id).label('days_present'),
        func.sum(EmployeeAttendance.hours_worked).label('total_hours')
    ).filter(
        EmployeeAttendance.date >= start_date,
        EmployeeAttendance.date <= end_date
    ).group_by(EmployeeAttendance.employee_id).all()
    
    return {
        "period": f"{days} days",
        "sales_performance": [
            {
                "user_id": row.user_id,
                "sales_count": row.sales_count,
                "total_revenue": float(row.total_revenue or 0)
            }
            for row in sales_by_employee
        ],
        "attendance": [
            {
                "employee_id": row.employee_id,
                "days_present": row.days_present,
                "total_hours": float(row.total_hours or 0)
            }
            for row in attendance_stats
        ]
    }


