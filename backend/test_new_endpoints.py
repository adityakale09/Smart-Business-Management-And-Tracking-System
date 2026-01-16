"""
Test script for new endpoints
Run this to verify all new features work correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login and get token"""
    print("\n" + "="*60)
    print("TEST 1: Login")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("\n✅ Login successful!")
        return token
    else:
        print("\n❌ Login failed!")
        return None


def test_change_password(token):
    """Test password change"""
    print("\n" + "="*60)
    print("TEST 2: Change Password")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/auth/change-password",
        headers=headers,
        json={
            "current_password": "admin123",
            "new_password": "newpass456"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Password changed successfully!")
        
        # Change it back
        print("\n[Changing password back to original...]")
        requests.post(
            f"{BASE_URL}/api/auth/change-password",
            headers=headers,
            json={
                "current_password": "newpass456",
                "new_password": "admin123"
            }
        )
        print("✅ Password restored")
    else:
        print("❌ Password change failed!")


def test_get_users(token):
    """Test list users (Admin only)"""
    print("\n" + "="*60)
    print("TEST 3: List All Users (Admin)")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/users", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"Total Users: {len(users)}")
        for user in users[:3]:  # Show first 3
            print(f"  - {user['username']} ({user['role']})")
        print("✅ User list retrieved successfully!")
    else:
        print(f"Response: {response.json()}")
        print("❌ Failed to get users!")


def test_update_profile(token):
    """Test profile update"""
    print("\n" + "="*60)
    print("TEST 4: Update Profile")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/api/auth/me",
        headers=headers,
        json={
            "email": "admin@updated.com",
            "full_name": "Updated Admin Name"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Profile updated successfully!")
    else:
        print(f"Response: {response.json()}")
        print("❌ Profile update failed!")


def test_invoice_download(token):
    """Test invoice PDF generation"""
    print("\n" + "="*60)
    print("TEST 5: Download Invoice PDF")
    print("="*60)
    
    # First, get a sale ID
    headers = {"Authorization": f"Bearer {token}"}
    sales_response = requests.get(f"{BASE_URL}/api/sales/", headers=headers)
    
    if sales_response.status_code == 200 and len(sales_response.json()) > 0:
        sale_id = sales_response.json()[0]["id"]
        
        # Download invoice
        response = requests.get(
            f"{BASE_URL}/api/sales/{sale_id}/invoice",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            # Save PDF
            filename = f"invoice_{sale_id}.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ Invoice downloaded: {filename}")
        else:
            print("❌ Invoice download failed!")
    else:
        print("⚠️  No sales found to generate invoice")


def test_export_sales_csv(token):
    """Test sales CSV export"""
    print("\n" + "="*60)
    print("TEST 6: Export Sales to CSV")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/sales/export/csv",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        filename = "sales_export.csv"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ CSV exported: {filename}")
    else:
        print("❌ CSV export failed!")


def test_export_inventory_excel(token):
    """Test inventory Excel export"""
    print("\n" + "="*60)
    print("TEST 7: Export Inventory to Excel")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/inventory/export/excel",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        filename = "inventory_export.xlsx"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ Excel exported: {filename}")
    else:
        print("❌ Excel export failed!")


def check_audit_logs(token):
    """Check if audit logs are being created"""
    print("\n" + "="*60)
    print("TEST 8: Verify Audit Logging")
    print("="*60)
    print("Checking database for audit logs...")
    print("⚠️  You need to manually check the database:")
    print("   SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 5;")


def main():
    print("\n" + "="*60)
    print("TESTING NEW ENDPOINTS")
    print("="*60)
    print("Make sure the backend is running on http://localhost:8000")
    
    # Test login first
    token = test_login()
    
    if not token:
        print("\n❌ Cannot continue without valid token!")
        return
    
    # Run all tests
    test_change_password(token)
    test_get_users(token)
    test_update_profile(token)
    test_invoice_download(token)
    test_export_sales_csv(token)
    test_export_inventory_excel(token)
    check_audit_logs(token)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60)
    print("\nGenerated files:")
    print("  - invoice_*.pdf")
    print("  - sales_export.csv")
    print("  - inventory_export.xlsx")


if __name__ == "__main__":
    main()
