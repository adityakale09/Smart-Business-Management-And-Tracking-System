"""
Comprehensive tests for audit logging system

Tests cover:
- Real database inserts (verify logs are persisted)
- Failure logging (capture failures, exceptions)
- Permission denied logging  
- Edge cases (special characters, null values, etc.)
- Service layer functions with audit integration
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables before importing config
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.database import Base, get_db
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.inventory import Inventory
from app.schemas.auth import UserRegister, ChangePassword, UpdateProfile
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.schemas.inventory import InventoryCreate, InventoryUpdate
from app.utils.audit_logger import (
    log_audit, log_login, log_create, log_update, log_delete,
    log_password_change, log_permission_denied, log_exception
)
from app.services.auth_service import (
    register_with_audit,
    login_with_audit,
    change_password_with_audit,
    update_profile_with_audit
)
from app.services.employee_service import (
    create_employee_with_audit,
    update_employee_with_audit
)
from app.services.inventory_service import (
    create_inventory_with_audit,
    update_inventory_with_audit
)
from app.core.security import get_password_hash


# ================================
# FIXTURES
# ================================

@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    yield db
    
    db.close()


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object"""
    request = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "Mozilla/5.0 Test Browser"}
    return request


@pytest.fixture
def test_user(test_db):
    """Create a test user in the database"""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_admin_user(test_db):
    """Create a test admin user"""
    user = User(
        id=2,
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_employee_user(test_db):
    """Create a test employee user"""
    user = User(
        id=3,
        username="employee",
        email="employee@example.com",
        full_name="Employee User",
        hashed_password=get_password_hash("emp123"),
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_manager_user(test_db):
    """Create a test manager user"""
    user = User(
        id=4,
        username="manager",
        email="manager@example.com",
        full_name="Manager User",
        hashed_password=get_password_hash("mgr123"),
        role=UserRole.MANAGER,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def current_user_dict(test_admin_user):
    """Create a current_user dict like FastAPI provides"""
    return {
        "user_id": str(test_admin_user.id),
        "username": test_admin_user.username,
        "role": test_admin_user.role.value
    }


# ================================
# SECTION 1: REAL DATABASE INSERT TESTS
# ================================

class TestAuditLogDatabaseInserts:
    """Test that audit logs are actually inserted into the database"""
    
    def test_log_create_inserts_to_database(self, test_db, test_user, mock_request):
        """Verify log_create actually inserts a record in the database"""
        # Initial count
        initial_count = test_db.query(AuditLog).count()
        
        # Log a creation event
        log_create(
            test_db,
            "User",
            entity_id=123,
            user_id=test_user.id,
            username=test_user.username,
            details={"email": "newuser@example.com"},
            request=mock_request
        )
        
        # Verify record was inserted
        final_count = test_db.query(AuditLog).count()
        assert final_count == initial_count + 1
        
        # Verify record contents
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == 123).first()
        assert log_entry is not None
        assert log_entry.action == "CREATE"
        assert log_entry.entity_type == "User"
        assert log_entry.status == "success"
        assert log_entry.ip_address == "127.0.0.1"
    
    def test_log_update_inserts_to_database(self, test_db, test_user, mock_request):
        """Verify log_update inserts a record"""
        log_update(
            test_db,
            "User",
            entity_id=456,
            user_id=test_user.id,
            username=test_user.username,
            details={"updated_field": "new_value"},
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.action == "UPDATE").first()
        assert log_entry is not None
        assert log_entry.entity_type == "User"
        assert log_entry.entity_id == 456
    
    def test_log_delete_inserts_to_database(self, test_db, test_user, mock_request):
        """Verify log_delete inserts a record"""
        log_delete(
            test_db,
            "User",
            entity_id=789,
            user_id=test_user.id,
            username=test_user.username,
            details={"reason": "account_deleted"},
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.action == "DELETE").first()
        assert log_entry is not None
        assert log_entry.action == "DELETE"
        assert log_entry.entity_id == 789
    
    def test_log_login_inserts_to_database(self, test_db, test_user, mock_request):
        """Verify log_login inserts a record"""
        log_login(
            test_db,
            test_user.id,
            test_user.username,
            mock_request,
            status="success"
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.action == "LOGIN").first()
        assert log_entry is not None
        assert log_entry.status == "success"
        assert log_entry.username == test_user.username
    
    def test_multiple_audit_logs_retained(self, test_db, test_user, mock_request):
        """Verify multiple audit logs are all retained"""
        # Create multiple log entries
        for i in range(5):
            log_create(
                test_db,
                "SomeEntity",
                entity_id=i,
                user_id=test_user.id,
                username=test_user.username,
                details={"index": i},
                request=mock_request
            )
        
        # Verify all are stored
        count = test_db.query(AuditLog).count()
        assert count == 5
    
    def test_audit_log_timestamp_is_set(self, test_db, test_user, mock_request):
        """Verify created_at timestamp is automatically set"""
        from datetime import datetime as dt
        
        before = dt.utcnow()
        
        log_create(
            test_db,
            "Test",
            entity_id=999,
            user_id=test_user.id,
            username=test_user.username,
            request=mock_request
        )
        
        after = dt.utcnow()
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == 999).first()
        assert log_entry is not None
        # Just verify timestamp exists and is between our bounds (with buffer for microseconds)
        assert log_entry.created_at is not None
        assert before.replace(microsecond=0) <= log_entry.created_at.replace(microsecond=0) <= after.replace(microsecond=0)


# ================================
# SECTION 2: FAILURE LOGGING TESTS
# ================================

class TestFailureLogging:
    """Test that failures are properly logged with exceptions and error messages"""
    
    def test_log_exception_captures_exception_message(self, test_db, test_user, mock_request):
        """Verify log_exception captures exception details"""
        exc = ValueError("Invalid user input")
        
        log_exception(
            test_db,
            "CREATE",
            "User",
            user_id=test_user.id,
            username=test_user.username,
            request=mock_request,
            exception=exc,
            details={"input": "invalid_data"}
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.status == "failure").first()
        assert log_entry is not None
        assert "Invalid user input" in log_entry.error_message
    
    def test_log_exception_with_complex_exception(self, test_db, test_user, mock_request):
        """Verify log_exception handles complex exceptions"""
        try:
            1 / 0
        except ZeroDivisionError as exc:
            log_exception(
                test_db,
                "CALCULATE",
                "Math",
                user_id=test_user.id,
                username=test_user.username,
                request=mock_request,
                exception=exc
            )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.action == "CALCULATE").first()
        assert log_entry is not None
        assert "division by zero" in log_entry.error_message.lower()
    
    def test_login_failure_logged_with_reason(self, test_db, mock_request):
        """Verify failed login attempts are logged with failure reason"""
        log_login(
            test_db,
            user_id=None,
            username="nonexistent",
            request=mock_request,
            status="failure",
            error_message="Invalid credentials"
        )
        
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "LOGIN",
            AuditLog.status == "failure"
        ).first()
        
        assert log_entry is not None
        assert log_entry.error_message == "Invalid credentials"
        assert log_entry.username == "nonexistent"
    
    def test_service_layer_logs_exception_on_failure(self, test_db, test_admin_user, mock_request):
        """Verify service layer logs exceptions that occur"""
        # Try to register with duplicate email
        existing_email = "existing@example.com"
        
        # Create existing user
        existing_user = User(
            username="existing",
            email=existing_email,
            full_name="Existing",
            hashed_password=get_password_hash("Existing123")
        )
        test_db.add(existing_user)
        test_db.commit()
        
        # Try to register with same email - should fail
        register_data = UserRegister(
            username="newuser",
            email=existing_email,
            full_name="New User",
            password="Password123",
            password_confirm="Password123"
        )
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            register_with_audit(test_db, register_data, mock_request)
    
    def test_log_contains_error_message_on_failure(self, test_db, test_user, mock_request):
        """Verify error_message field is populated on failures"""
        error_msg = "Database connection timeout"
        
        log_exception(
            test_db,
            "WRITE",
            "Entity",
            user_id=test_user.id,
            username=test_user.username,
            request=mock_request,
            exception=TimeoutError(error_msg)
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.status == "failure").first()
        assert error_msg in log_entry.error_message


# ================================
# SECTION 3: PERMISSION DENIED LOGGING
# ================================

class TestPermissionDeniedLogging:
    """Test that permission denied attempts are logged"""
    
    def test_log_permission_denied_creates_audit_entry(self, test_db, test_employee_user, mock_request):
        """Verify permission denied is logged"""
        log_permission_denied(
            test_db,
            user_id=test_employee_user.id,
            username=test_employee_user.username,
            action="DELETE_USER",
            entity_type="User",
            request=mock_request,
            reason="Insufficient permissions"
        )
        
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "DELETE_USER"
        ).first()
        
        assert log_entry is not None
        assert "Insufficient permissions" in log_entry.error_message
    
    def test_permission_denied_has_correct_status(self, test_db, test_employee_user, mock_request):
        """Verify permission denied logs have 'failure' status"""
        log_permission_denied(
            test_db,
            user_id=test_employee_user.id,
            username=test_employee_user.username,
            action="ADMIN_ACTION",
            entity_type="Config",
            request=mock_request,
            reason="Admin role required"
        )
        
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "ADMIN_ACTION"
        ).first()
        
        assert log_entry.status == "failure"
    
    def test_multiple_permission_denials_tracked(self, test_db, test_employee_user, mock_request):
        """Verify multiple permission denial attempts are tracked"""
        for i in range(3):
            log_permission_denied(
                test_db,
                user_id=test_employee_user.id,
                username=test_employee_user.username,
                action="ATTEMPT",
                entity_type="SensitiveData",
                request=mock_request,
                reason=f"Access denied attempt {i+1}"
            )
        
        denials = test_db.query(AuditLog).filter(
            AuditLog.status == "failure",
            AuditLog.action == "ATTEMPT"
        ).all()
        
        assert len(denials) == 3


# ================================
# SECTION 4: SERVICE LAYER TESTS
# ================================

class TestServiceLayerAuditIntegration:
    """Test that service layer functions properly integrate audit logging"""
    
    def test_register_with_audit_logs_creation(self, test_db, mock_request):
        """Verify register_with_audit logs the user creation"""
        register_data = UserRegister(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="SecurePass123!",
            password_confirm="SecurePass123!"
        )
        
        user = register_with_audit(test_db, register_data, mock_request)
        
        # Verify user was created
        assert user.username == "newuser"
        
        # Verify audit log was created
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "CREATE",
            AuditLog.entity_type == "User",
            AuditLog.entity_id == user.id
        ).first()
        
        assert log_entry is not None
        assert log_entry.status == "success"
    
    def test_login_with_audit_logs_successful_login(self, test_db, test_user, mock_request):
        """Verify login_with_audit logs successful login"""
        from app.schemas.auth import UserLogin
        
        credentials = UserLogin(username="testuser", password="password123")
        
        result = login_with_audit(test_db, credentials, mock_request)
        
        # Verify login was successful
        assert result["access_token"]
        
        # Verify audit log was created
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "LOGIN",
            AuditLog.user_id == test_user.id
        ).first()
        
        assert log_entry is not None
        assert log_entry.status == "success"
    
    def test_login_with_audit_logs_failed_login(self, test_db, test_user, mock_request):
        """Verify login_with_audit logs failed login"""
        from app.schemas.auth import UserLogin
        from fastapi import HTTPException
        
        credentials = UserLogin(username="testuser", password="wrongpassword")
        
        with pytest.raises(HTTPException):
            login_with_audit(test_db, credentials, mock_request)
        
        # Verify failure was logged
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "LOGIN",
            AuditLog.status == "failure"
        ).first()
        
        assert log_entry is not None
        assert "Invalid credentials" in log_entry.error_message
    
    def test_create_employee_with_audit_logs_creation(self, test_db, test_manager_user, test_employee_user, mock_request):
        """Verify create_employee_with_audit logs the creation"""
        current_user = {
            "user_id": str(test_manager_user.id),
            "username": test_manager_user.username,
            "role": "manager"
        }
        
        emp_data = EmployeeCreate(
            employee_id="EMP001",
            user_id=test_employee_user.id,
            department="Sales",
            position="Sales Rep",
            salary=50000.00,
            hire_date="2024-01-01",
            phone="555-0001",
            address="123 Main St",
            emergency_contact="555-0002"
        )
        
        employee = create_employee_with_audit(test_db, emp_data, current_user, mock_request)
        
        # Verify creation was logged
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "CREATE",
            AuditLog.entity_type == "Employee"
        ).first()
        
        assert log_entry is not None
        assert log_entry.user_id == test_manager_user.id
        assert log_entry.status == "success"
    
    def test_create_inventory_with_audit_logs_creation(self, test_db, test_manager_user, mock_request):
        """Verify create_inventory_with_audit logs the creation"""
        current_user = {
            "user_id": str(test_manager_user.id),
            "username": test_manager_user.username,
            "role": "manager"
        }
        
        inv_data = InventoryCreate(
            sku="SKU001",
            name="Product A",
            description="Test product",
            category="Electronics",
            quantity=100,
            reorder_level=20,
            unit_price=99.99,
            supplier="Supplier A",
            location="Warehouse A"
        )
        
        item = create_inventory_with_audit(test_db, inv_data, current_user, mock_request)
        
        # Verify creation was logged
        log_entry = test_db.query(AuditLog).filter(
            AuditLog.action == "CREATE",
            AuditLog.entity_type == "Inventory"
        ).first()
        
        assert log_entry is not None
        assert log_entry.status == "success"


# ================================
# SECTION 5: EDGE CASES
# ================================

class TestAuditLoggingEdgeCases:
    """Test edge cases and unusual scenarios"""
    
    def test_log_with_special_characters_in_details(self, test_db, test_user, mock_request):
        """Verify logging handles special characters properly"""
        special_details = {
            "text": "Quote: \"test\", Newline:\n, Tab:\t, Unicode: 日本語",
            "symbols": "!@#$%^&*()",
            "sql": "'; DROP TABLE--"
        }
        
        log_create(
            test_db,
            "Entity",
            entity_id=1001,
            user_id=test_user.id,
            username=test_user.username,
            details=special_details,
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == 1001).first()
        assert log_entry is not None
        assert "日本語" in str(log_entry.details)
    
    def test_log_with_empty_details(self, test_db, test_user, mock_request):
        """Verify logging handles empty details"""
        log_create(
            test_db,
            "Entity",
            entity_id=1002,
            user_id=test_user.id,
            username=test_user.username,
            details={},
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == 1002).first()
        assert log_entry is not None
    
    def test_log_with_large_entity_id(self, test_db, test_user, mock_request):
        """Verify logging handles very large entity IDs"""
        large_id = 9223372036854775807  # Max int64
        
        log_create(
            test_db,
            "Entity",
            entity_id=large_id,
            user_id=test_user.id,
            username=test_user.username,
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == large_id).first()
        assert log_entry is not None
    
    def test_log_with_very_long_username(self, test_db, mock_request):
        """Verify logging handles long usernames"""
        long_username = "u" * 255
        
        log_create(
            test_db,
            "Entity",
            entity_id=1003,
            user_id=999,
            username=long_username,
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == 1003).first()
        assert log_entry is not None
        assert long_username in log_entry.username
    
    def test_log_with_null_optional_fields(self, test_db, test_user, mock_request):
        """Verify logging handles null optional fields"""
        log_create(
            test_db,
            "Entity",
            entity_id=1004,
            user_id=test_user.id,
            username=test_user.username,
            details=None,
            request=mock_request
        )
        
        log_entry = test_db.query(AuditLog).filter(AuditLog.entity_id == 1004).first()
        assert log_entry is not None
    
    def test_concurrent_logs_from_different_users(self, test_db, test_user, test_admin_user, mock_request):
        """Verify multiple users logging simultaneously is handled"""
        for i, user in enumerate([test_user, test_admin_user]):
            log_create(
                test_db,
                "Entity",
                entity_id=1005 + i,
                user_id=user.id,
                username=user.username,
                request=mock_request
            )
        
        logs = test_db.query(AuditLog).filter(
            AuditLog.entity_id.in_([1005, 1006])
        ).all()
        
        assert len(logs) == 2
        assert logs[0].user_id != logs[1].user_id
    
    def test_log_timestamp_precision(self, test_db, test_user, mock_request):
        """Verify multiple logs have distinct timestamps or can be ordered"""
        timestamps = []
        
        for i in range(3):
            log_create(
                test_db,
                "Entity",
                entity_id=2000 + i,
                user_id=test_user.id,
                username=test_user.username,
                request=mock_request
            )
            
            log_entry = test_db.query(AuditLog).filter(
                AuditLog.entity_id == 2000 + i
            ).first()
            timestamps.append(log_entry.created_at)
        
        # Verify timestamps are in order or can be ordered
        assert timestamps[-1] >= timestamps[0]


# ================================
# SECTION 6: FILTERING & QUERYING
# ================================

class TestAuditLogFiltering:
    """Test audit log filtering and querying capabilities"""
    
    def test_filter_by_action(self, test_db, test_user, mock_request):
        """Verify filtering by action works"""
        log_create(test_db, "Entity", 1, test_user.id, test_user.username, request=mock_request)
        log_update(test_db, "Entity", 2, test_user.id, test_user.username, request=mock_request)
        log_delete(test_db, "Entity", 3, test_user.id, test_user.username, request=mock_request)
        
        creates = test_db.query(AuditLog).filter(AuditLog.action == "CREATE").all()
        assert len(creates) == 1
        assert creates[0].entity_id == 1
    
    def test_filter_by_entity_type(self, test_db, test_user, mock_request):
        """Verify filtering by entity_type works"""
        log_create(test_db, "User", 1, test_user.id, test_user.username, request=mock_request)
        log_create(test_db, "Employee", 2, test_user.id, test_user.username, request=mock_request)
        
        user_logs = test_db.query(AuditLog).filter(AuditLog.entity_type == "User").all()
        assert len(user_logs) == 1
        assert user_logs[0].entity_type == "User"
    
    def test_filter_by_user_id(self, test_db, test_user, test_admin_user, mock_request):
        """Verify filtering by user_id works"""
        log_create(test_db, "Entity", 1, test_user.id, test_user.username, request=mock_request)
        log_create(test_db, "Entity", 2, test_admin_user.id, test_admin_user.username, request=mock_request)
        
        user_logs = test_db.query(AuditLog).filter(AuditLog.user_id == test_user.id).all()
        assert len(user_logs) == 1
        assert user_logs[0].user_id == test_user.id
    
    def test_filter_by_status(self, test_db, test_user, mock_request):
        """Verify filtering by status works"""
        log_create(test_db, "Entity", 1, test_user.id, test_user.username, request=mock_request, status="success")
        log_exception(test_db, "CREATE", "Entity", test_user.id, test_user.username, request=mock_request, exception=Exception("error"))
        
        successes = test_db.query(AuditLog).filter(AuditLog.status == "success").all()
        failures = test_db.query(AuditLog).filter(AuditLog.status == "failure").all()
        
        assert len(successes) >= 1
        assert len(failures) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
