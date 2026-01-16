"""
Employee schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmployeeCreate(BaseModel):
    """Create employee schema"""
    employee_id: str
    user_id: int
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[datetime] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Update employee schema"""
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Employee response schema"""
    id: int
    employee_id: str
    user_id: int
    department: Optional[str]
    position: Optional[str]
    salary: Optional[float]
    hire_date: Optional[datetime]
    status: str
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    
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








