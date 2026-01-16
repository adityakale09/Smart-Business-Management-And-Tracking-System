"""
Generate dummy data for testing and development
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.inventory import Inventory, InventoryUpdate
from app.models.receipt import Receipt, ReceiptItem, ReceiptType
from app.models.user import User
from app.models import Base


# Sample product names
PRODUCT_NAMES = [
    "Laptop Computer", "Wireless Mouse", "USB Cable", "Keyboard", "Monitor 27\"",
    "HDD 1TB", "SSD 256GB", "RAM 8GB", "Graphics Card", "Motherboard",
    "Power Supply", "Cooling Fan", "Webcam HD", "Microphone", "Headphones",
    "Speakers", "USB Drive 32GB", "USB Drive 64GB", "External HDD 2TB", "DVD Drive",
    "Network Cable", "Router WiFi", "Ethernet Adapter", "Bluetooth Dongle", "Printer Ink"
]

CATEGORIES = ["Electronics", "Computer Parts", "Accessories", "Storage", "Peripherals"]

SUPPLIERS = ["TechSupply Inc", "ElectroParts Co", "Global Tech", "Computer Depot", "Parts Warehouse"]

STORE_NAMES = ["Retail Store A", "Retail Store B", "Online Store", "Wholesale Supplier", "Tech Mart"]


def generate_inventory_items(db: Session, count: int = 20, user_id: int = 1):
    """Generate random inventory items"""
    items = []
    
    for i in range(count):
        product_name = random.choice(PRODUCT_NAMES)
        
        # Ensure unique product names
        existing = db.query(Inventory).filter(Inventory.name == product_name).first()
        if existing:
            product_name = f"{product_name} {i+1}"
        
        sku = f"SKU-{random.randint(1000, 9999)}-{i+1}"
        
        # Check if SKU exists
        existing_sku = db.query(Inventory).filter(Inventory.sku == sku).first()
        if existing_sku:
            sku = f"SKU-{random.randint(10000, 99999)}-{i+1}"
        
        quantity = random.randint(0, 500)
        unit_price = round(random.uniform(10.0, 1000.0), 2)
        reorder_level = random.randint(10, 50)
        
        item = Inventory(
            sku=sku,
            name=product_name,
            description=f"Description for {product_name}",
            category=random.choice(CATEGORIES),
            quantity=quantity,
            reorder_level=reorder_level,
            unit_price=unit_price,
            supplier=random.choice(SUPPLIERS),
            location=random.choice(["Warehouse A", "Warehouse B", "Store Floor"]),
            status="active" if quantity > reorder_level else "active"
        )
        
        db.add(item)
        items.append(item)
    
    try:
        db.commit()
        for item in items:
            db.refresh(item)
        print(f"[+] Generated {count} inventory items")
        return items
    except Exception as e:
        db.rollback()
        print(f"[-] Failed to generate inventory items: {str(e)}")
        return []


def generate_receipts(db: Session, count: int = 10, user_id: int = 1):
    """Generate sample receipts"""
    receipts = []
    inventory_items = db.query(Inventory).all()
    
    if not inventory_items:
        print("[-] No inventory items found. Please generate inventory items first.")
        return []
    
    receipt_types = [ReceiptType.PURCHASE, ReceiptType.SALE]
    
    for i in range(count):
        receipt_type = random.choice(receipt_types)
        receipt_date = datetime.now() - timedelta(days=random.randint(0, 30))
        source = random.choice(STORE_NAMES)
        
        # Create receipt
        receipt = Receipt(
            receipt_date=receipt_date,
            receipt_type=receipt_type,
            source=source,
            total_amount=0.0,
            processed_by=user_id
        )
        db.add(receipt)
        db.flush()
        
        # Add items to receipt
        num_items = random.randint(1, 5)
        total_amount = 0.0
        
        for j in range(num_items):
            item = random.choice(inventory_items)
            quantity = random.randint(1, 10)
            unit_price = item.unit_price * random.uniform(0.9, 1.1)  # Slight variation
            total_price = quantity * unit_price
            
            receipt_item = ReceiptItem(
                receipt_id=receipt.id,
                product_name=item.name,
                quantity=quantity,
                price_per_unit=unit_price
            )
            db.add(receipt_item)
            total_amount += total_price
            
            # Update inventory
            if receipt_type == ReceiptType.PURCHASE:
                item.quantity += quantity
                update_type = 'restock'
                quantity_change = quantity
            else:
                # Sale - ensure we don't go negative
                if item.quantity < quantity:
                    quantity = item.quantity
                item.quantity -= quantity
                update_type = 'sale'
                quantity_change = -quantity
            
            item.updated_at = receipt_date
            
            # Create inventory update record
            previous_quantity = item.quantity + (-quantity_change if receipt_type == ReceiptType.PURCHASE else quantity_change)
            update_record = InventoryUpdate(
                inventory_id=item.id,
                user_id=user_id,
                update_type=update_type,
                quantity_change=quantity_change,
                previous_quantity=previous_quantity,
                new_quantity=item.quantity,
                notes=f"Generated from dummy receipt #{receipt.id}",
                created_at=receipt_date
            )
            db.add(update_record)
        
        receipt.total_amount = round(total_amount, 2)
        receipts.append(receipt)
    
    try:
        db.commit()
        for receipt in receipts:
            db.refresh(receipt)
        print(f"[+] Generated {count} receipts")
        return receipts
    except Exception as e:
        db.rollback()
        print(f"[-] Failed to generate receipts: {str(e)}")
        return []


def seed_database():
    """Main function to seed the database with dummy data"""
    db = SessionLocal()
    
    try:
        # Check if there's at least one user
        user = db.query(User).first()
        if not user:
            print("[-] No users found. Please create a user first.")
            return {"success": False, "message": "No users found. Please create a user first."}
        
        user_id = user.id
        
        print("[*] Starting database seeding...")
        
        # Generate inventory items
        inventory_items = generate_inventory_items(db, count=20, user_id=user_id)
        
        # Generate receipts
        receipts = generate_receipts(db, count=10, user_id=user_id)
        
        print("[+] Database seeding completed successfully!")
        
        return {
            "success": True,
            "message": f"Database seeded with {len(inventory_items)} inventory items and {len(receipts)} receipts",
            "inventory_items": len(inventory_items),
            "receipts": len(receipts)
        }
        
    except Exception as e:
        db.rollback()
        print(f"[-] Database seeding failed: {str(e)}")
        return {"success": False, "message": f"Database seeding failed: {str(e)}"}
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed database
    result = seed_database()
    print(result)

