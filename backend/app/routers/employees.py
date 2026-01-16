"""
Employee management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    AttendanceCreate, AttendanceResponse
)
from app.models.employee import Employee, EmployeeAttendance

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Create a new employee record"""
    try:
        # Check if user exists
        from app.models.user import User
        user = db.query(User).filter(User.id == employee_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {employee_data.user_id} does not exist"
            )
        
        # Check if employee ID already exists
        existing = db.query(Employee).filter(
            Employee.employee_id == employee_data.employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        
        # Check if user already has an employee record
        existing_employee = db.query(Employee).filter(
            Employee.user_id == employee_data.user_id
        ).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with ID {employee_data.user_id} already has an employee record"
            )
        
        new_employee = Employee(
            employee_id=employee_data.employee_id,
            user_id=employee_data.user_id,
            department=employee_data.department,
            position=employee_data.position,
            salary=employee_data.salary,
            hire_date=employee_data.hire_date,
            phone=employee_data.phone,
            address=employee_data.address,
            emergency_contact=employee_data.emergency_contact
        )
        
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        
        return new_employee
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        if "connection" in error_msg.lower() or "database" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please check your database configuration."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create employee: {error_msg}"
        )


@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get all employees"""
    query = db.query(Employee)
    
    if department:
        query = query.filter(Employee.department == department)
    
    if status_filter:
        query = query.filter(Employee.status == status_filter)
    
    employees = query.offset(skip).limit(limit).all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get a specific employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Employees can only view their own profile unless they're manager/admin
    if current_user["role"] == "employee":
        user_employee = db.query(Employee).filter(
            Employee.user_id == int(current_user["user_id"])
        ).first()
        if not user_employee or user_employee.id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Update an employee record"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update fields
    update_data = employee_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee


@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_data: AttendanceCreate,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Create attendance record"""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == attendance_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Employees can only create their own attendance
    if current_user["role"] == "employee":
        if employee.user_id != int(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create attendance for yourself"
            )
    
    new_attendance = EmployeeAttendance(
        employee_id=attendance_data.employee_id,
        date=attendance_data.date,
        check_in=attendance_data.check_in,
        check_out=attendance_data.check_out,
        status=attendance_data.status
    )
    
    # Calculate hours worked if both check_in and check_out are provided
    if attendance_data.check_in and attendance_data.check_out:
        delta = attendance_data.check_out - attendance_data.check_in
        new_attendance.hours_worked = delta.total_seconds() / 3600
    
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return new_attendance


@router.get("/attendance/{employee_id}", response_model=List[AttendanceResponse])
async def get_employee_attendance(
    employee_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get attendance records for an employee"""
    # Check permissions
    if current_user["role"] == "employee":
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee or employee.user_id != int(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    query = db.query(EmployeeAttendance).filter(
        EmployeeAttendance.employee_id == employee_id
    )
    
    if start_date:
        query = query.filter(EmployeeAttendance.date >= start_date)
    if end_date:
        query = query.filter(EmployeeAttendance.date <= end_date)
    
    attendance = query.order_by(EmployeeAttendance.date.desc()).all()
    return attendance








