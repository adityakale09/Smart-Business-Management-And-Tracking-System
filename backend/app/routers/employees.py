"""
Employee management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
from app.services.employee_service import (
    create_employee_with_audit,
    update_employee_with_audit
)

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Create a new employee record"""
    return create_employee_with_audit(db, employee_data, current_user, request)


from fastapi import Query
from sqlalchemy import or_

@router.get("/", response_model=dict)
async def get_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get all employees with pagination and search"""
    try:
        query = db.query(Employee)
        if department:
            query = query.filter(Employee.department == department)
        if status_filter:
            query = query.filter(Employee.status == status_filter)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Employee.employee_id.ilike(search_term),
                    Employee.department.ilike(search_term),
                    Employee.position.ilike(search_term)
                )
            )

        total = query.count()
        employees = query.offset((page - 1) * page_size).limit(page_size).all()

        items = [
            EmployeeResponse.model_validate(emp).model_dump(mode="json")
            for emp in employees
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve employees: {str(e)}"
        )


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
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Update an employee record"""
    return update_employee_with_audit(db, employee_id, employee_data, current_user, request)


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








