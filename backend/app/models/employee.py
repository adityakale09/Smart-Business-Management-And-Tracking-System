"""
Employee model
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Employee(Base):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    department = Column(String)
    position = Column(String)
    full_name = Column(String)
    salary = Column(Float)
    hire_date = Column(DateTime)
    status = Column(String, default="active")  # active, on_leave, terminated
    phone = Column(String)
    address = Column(Text)
    emergency_contact = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="employee_profile")


class EmployeeAttendance(Base):
    """Employee attendance tracking"""
    __tablename__ = "employee_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(DateTime, nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    hours_worked = Column(Float)
    status = Column(String)  # present, absent, late, half_day
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    employee = relationship("Employee", backref="attendance_records")








