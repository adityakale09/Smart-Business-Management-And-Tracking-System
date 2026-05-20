"""
Employee schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmployeeCreate(BaseModel):
    """Create employee schema"""
    employee_id: Optional[str] = None  # Auto-generated if not provided
    user_id: int
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[datetime] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Update employee schema"""
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Employee response schema"""
    id: int
    employee_id: str
    user_id: Optional[int] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[datetime] = None
    status: Optional[str] = "active"
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AttendanceCreate(BaseModel):
    """Create attendance record schema"""
    employee_id: int
    date: datetime
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[str] = "present"


class AttendanceResponse(BaseModel):
    """Attendance response schema"""
    id: int
    employee_id: int
    date: datetime
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    hours_worked: Optional[float]
    status: Optional[str]
    
    class Config:
        from_attributes = True








