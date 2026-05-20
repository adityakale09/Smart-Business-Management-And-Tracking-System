"""
Employee model
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Employee(Base):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    department = Column(String)
    position = Column(String)
    full_name = Column(String)
    salary = Column(Float)
    hire_date = Column(DateTime(timezone=True))
    status = Column(String, default="active")  # active, on_leave, terminated
    phone = Column(String)
    address = Column(Text)
    emergency_contact = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="employee_profile")
    organization = relationship("Organization", backref="employees")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_employees_org_dept_status", "organization_id", "department", "status"),
        Index("ix_employees_org_status_created", "organization_id", "status", "created_at"),
        Index("ix_employees_department_status", "department", "status"),
        Index("ix_employees_status_created", "status", "created_at"),
    )





class EmployeeAttendance(Base):
    """Employee attendance tracking"""
    __tablename__ = "employee_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))
    hours_worked = Column(Float)
    status = Column(String)  # present, absent, late, half_day
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employee = relationship("Employee", backref="attendance_records")
    organization = relationship("Organization", backref="attendance_records")
    
    # Composite indexes
    __table_args__ = (
        Index("ix_attendance_org_employee_date", "organization_id", "employee_id", "date"),
        Index("ix_attendance_org_status_date", "organization_id", "status", "date"),
        Index("ix_attendance_employee_date", "employee_id", "date"),
        Index("ix_attendance_status_date", "status", "date"),
    )








