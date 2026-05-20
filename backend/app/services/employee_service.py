"""
Employee service with audit logging.

This module centralizes employee operations and related side effects
(such as audit logging), keeping routers minimal.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.user import User
from app.utils.audit_logger import log_create, log_update, log_delete


def generate_employee_id(db: Session) -> str:
    """Generate a unique employee ID in EMP001 format."""
    from sqlalchemy import text
    # Use raw SQL for PostgreSQL regexp_replace as SQLAlchemy ORM has limitations
    result = db.execute(
        text("""
            SELECT MAX(CAST(REGEXP_REPLACE(employee_id, '[^0-9]', '', 'g') AS INTEGER))
            FROM employees
            WHERE employee_id ~ '^EMP[0-9]+$'
        """)
    ).scalar()
    
    if result is None:
        next_num = 1
    else:
        next_num = result + 1
    
    return f"EMP{next_num:03d}"


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
        
        # Check if user already has an employee record
        existing_employee = db.query(Employee).filter(
            Employee.user_id == employee_data.user_id
        ).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with ID {employee_data.user_id} already has an employee record"
            )
        
        # Auto-generate employee ID if not provided
        employee_id = employee_data.employee_id
        if not employee_id or not employee_id.strip():
            employee_id = generate_employee_id(db)
        else:
            # Check if provided employee ID already exists
            existing = db.query(Employee).filter(
                Employee.employee_id == employee_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employee ID already exists"
                )
        
        new_employee = Employee(
            employee_id=employee_id,
            user_id=employee_data.user_id,
            full_name=employee_data.full_name or user.full_name,
            department=employee_data.department,
            position=employee_data.position,
            salary=employee_data.salary,
            hire_date=employee_data.hire_date,
            phone=employee_data.phone,
            address=employee_data.address,
            emergency_contact=employee_data.emergency_contact,
            notes=employee_data.notes,
            organization_id=current_user.get("organization_id")
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
                "full_name": new_employee.full_name,
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
        org_id = current_user.get("organization_id")
        query = db.query(Employee).filter(Employee.id == employee_id)
        if org_id is not None:
            query = query.filter(Employee.organization_id == int(org_id))
        employee = query.first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Update fields
        update_data = employee_data.model_dump(exclude_unset=True)
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


def delete_employee_with_audit(db: Session, employee_id: int, current_user: dict, request: Request):
    """Delete employee record and write audit entry."""
    try:
        org_id = current_user.get("organization_id")
        query = db.query(Employee).filter(Employee.id == employee_id)
        if org_id is not None:
            query = query.filter(Employee.organization_id == int(org_id))
        employee = query.first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Store details for audit before deletion
        emp_details = {
            "employee_id": employee.employee_id,
            "full_name": employee.full_name,
            "department": employee.department,
            "position": employee.position,
        }
        
        db.delete(employee)
        db.commit()
        
        # Log employee deletion
        log_delete(
            db,
            "Employee",
            employee_id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details=emp_details,
            request=request
        )
        
        return {"message": f"Employee {employee_id} has been deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete employee: {str(e)}"
        )
