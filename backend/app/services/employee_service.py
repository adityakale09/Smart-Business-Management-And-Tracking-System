"""
Employee service with audit logging.

This module centralizes employee operations and related side effects
(such as audit logging), keeping routers minimal.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.user import User
from app.utils.audit_logger import log_create, log_update


def create_employee_with_audit(db: Session, employee_data, current_user: dict, request: Request):
    """Create employee record and write audit entry."""
    try:
        # Check if user exists
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
            full_name=getattr(employee_data, 'full_name', None),
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
        
        # Log employee creation
        log_create(
            db,
            "Employee",
            new_employee.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details={
                "employee_id": new_employee.employee_id,
                "department": new_employee.department,
                "position": new_employee.position,
                "user_id": new_employee.user_id,
            },
            request=request
        )
        
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


def update_employee_with_audit(db: Session, employee_id: int, employee_data, current_user: dict, request: Request):
    """Update employee record and write audit entry."""
    try:
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
        
        # Log employee update
        log_update(
            db,
            "Employee",
            employee.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details=update_data,
            request=request
        )
        
        return employee
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update employee: {str(e)}"
        )
