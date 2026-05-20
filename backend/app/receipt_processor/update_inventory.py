"""
Inventory update logic for receipt processing
"""

from sqlalchemy.orm import Session
from typing import Dict
from app.models.inventory import Inventory
from app.models.receipt import Receipt, ReceiptItem
from app.models.user import User
from datetime import datetime, timezone


class InventoryUpdater:
    """Service for updating inventory based on receipt data"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
    
    def process_receipt(self, receipt_data: Dict, user_id: int, organization_id: int = None) -> Dict:
        """
        Process receipt and update inventory
        
        Args:
            receipt_data: Parsed receipt data
            user_id: ID of user processing the receipt
            organization_id: Organization ID for multi-tenant isolation
            
        Returns:
            Dictionary with processing results
        """
        receipt_type = receipt_data.get('receipt_type', 'purchase')
        items = receipt_data.get('items', [])
        receipt_date = receipt_data.get('receipt_date') or datetime.now(timezone.utc)
        source = receipt_data.get('source', 'Unknown')
        total_amount = receipt_data.get('total_amount', 0.0)
        image_data = receipt_data.get('image_data')
        currency_code = receipt_data.get('currency_code', 'INR')
        category = receipt_data.get('category')
        
        # Create receipt record
        receipt = Receipt(
            receipt_date=receipt_date,
            receipt_type=receipt_type,
            source=source,
            total_amount=total_amount,
            category=category,
            processed_by=user_id,
            image_data=image_data,
            organization_id=organization_id
        )
        self.db.add(receipt)
        self.db.flush()  # Get receipt ID
        
        # Process each item
        processed_items = []
        inventory_updates = []
        
        for item_data in items:
            product_name = item_data.get('product_name', '').strip()
            quantity = item_data.get('quantity', 0)
            unit_price = item_data.get('unit_price', 0.0)
            
            if not product_name or quantity <= 0:
                continue
            
            # Create receipt item record
            receipt_item = ReceiptItem(
                receipt_id=receipt.id,
                product_name=product_name,
                quantity=quantity,
                price_per_unit=unit_price,
                organization_id=organization_id
            )
            self.db.add(receipt_item)
            
            # Update inventory - always add stock for receipt processing
            inventory_result = self._update_inventory(
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                user_id=user_id,
                organization_id=organization_id
            )
            
            processed_items.append({
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'inventory_updated': inventory_result['success'],
                'message': inventory_result['message']
            })
            
            inventory_updates.append(inventory_result)
        
        # Commit all changes
        try:
            self.db.commit()
            self.db.refresh(receipt)
            
            return {
                'success': True,
                'receipt_id': receipt.id,
                'items_processed': len(processed_items),
                'items': processed_items,
                'inventory_updates': inventory_updates,
                'message': f'Receipt processed successfully. {len(processed_items)} items processed.'
            }
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'message': f'Failed to process receipt: {str(e)}',
                'items': processed_items
            }
    
    def _update_inventory(self, product_name: str, quantity: int, unit_price: float, 
                         user_id: int, organization_id: int = None) -> Dict:
        """
        Update inventory for a product - always adds stock from receipt processing
        
        Args:
            product_name: Name of the product
            quantity: Quantity to add
            unit_price: Unit price of the product
            user_id: ID of user making the update
            organization_id: Organization ID for multi-tenant isolation
            
        Returns:
            Dictionary with update result
        """
        try:
            # Find existing inventory item by name (case-insensitive), scoped to org
            query = self.db.query(Inventory).filter(
                Inventory.name.ilike(f'%{product_name}%')
            )
            if organization_id is not None:
                query = query.filter(Inventory.organization_id == int(organization_id))
            inventory = query.first()
            
            if not inventory:
                # Create new inventory item if it doesn't exist
                # Generate SKU from product name
                sku = product_name.upper().replace(' ', '-')[:20]
                # Ensure SKU is unique
                existing_sku = self.db.query(Inventory).filter(Inventory.sku == sku).first()
                if existing_sku:
                    sku = f"{sku}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
                
                inventory = Inventory(
                    sku=sku,
                    name=product_name,
                    quantity=0,
                    unit_price=unit_price,
                    status='active',
                    organization_id=organization_id
                )
                self.db.add(inventory)
                self.db.flush()
            
            # Update quantity - always add stock
            previous_quantity = inventory.quantity
            inventory.quantity += quantity
            update_type = 'restock'
            quantity_change = quantity
            message = f'Added {quantity} units of {product_name}'
            
            # Update unit price if provided (use latest price)
            if unit_price > 0:
                inventory.unit_price = unit_price
            
            # Update last updated timestamp
            inventory.updated_at = datetime.now(timezone.utc)
            
            # Update status based on quantity
            if inventory.quantity <= 0:
                inventory.status = 'out_of_stock'
            elif inventory.quantity <= inventory.reorder_level:
                inventory.status = 'active'
            else:
                inventory.status = 'active'
            
            # Create inventory update history record
            from app.models.inventory import InventoryUpdate
            update_record = InventoryUpdate(
                inventory_id=inventory.id,
                user_id=user_id,
                update_type=update_type,
                quantity_change=quantity_change,
                previous_quantity=previous_quantity,
                new_quantity=inventory.quantity,
                organization_id=organization_id,
                notes=f'Updated from receipt processing: {message}'
            )
            self.db.add(update_record)
            
            return {
                'success': True,
                'product_name': product_name,
                'inventory_id': inventory.id,
                'previous_quantity': previous_quantity,
                'new_quantity': inventory.quantity,
                'message': message
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to update inventory for {product_name}: {str(e)}'
            }


def process_receipt_data(db: Session, receipt_data: Dict, user_id: int, organization_id: int = None) -> Dict:
    """
    Convenience function to process receipt data
    
    Args:
        db: Database session
        receipt_data: Parsed receipt data
        user_id: ID of user processing the receipt
        organization_id: Organization ID for multi-tenant isolation
        
    Returns:
        Dictionary with processing results
    """
    updater = InventoryUpdater(db)
    return updater.process_receipt(receipt_data, user_id, organization_id)

