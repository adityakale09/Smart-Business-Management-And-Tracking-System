# Inventory Module - Quick Reference Guide

## 🎯 Quick Actions

### For Managers/Admins

| Action | Steps | Result |
|--------|-------|--------|
| **Add Product** | Click "Add Product" button → Fill form → Submit | New product added to inventory |
| **Edit Product** | Click blue edit icon → Modify fields → Update | Product details updated |
| **Delete Product** | Click red delete icon → Confirm | Product removed from system |
| **Restock Item** | Click green restock icon → Enter quantity → Confirm | Stock increased, audit trail created |

### For All Users (Employee+)

| Action | Steps | Result |
|--------|-------|--------|
| **Search Products** | Type in search box | Filter by name or SKU |
| **View Low Stock** | Toggle "Show low stock only" | See items needing restock |
| **View Details** | Look at table columns | See all product information |

---

## 🎨 UI Elements Guide

### Status Badges

| Badge | Color | Meaning |
|-------|-------|---------|
| 🟢 Active | Green | Stock level is healthy (quantity > reorder level) |
| 🟡 Low Stock | Yellow/Orange | Stock is below reorder level (quantity ≤ reorder level) |
| 🔴 Out of Stock | Red | No stock available (quantity = 0) |

### Action Buttons

| Button | Icon | Color | Function | Access |
|--------|------|-------|----------|--------|
| Restock | 📦 | Green | Add quantity to stock | Manager+ |
| Edit | ✏️ | Blue | Update product details | Manager+ |
| Delete | 🗑️ | Red | Remove product | Manager+ |

---

## 📋 Form Fields Reference

### Add/Edit Product Form

| Field | Type | Required | Editable | Notes |
|-------|------|----------|----------|-------|
| **SKU** | Text | ✅ Yes | ❌ No (after creation) | Unique identifier |
| **Product Name** | Text | ✅ Yes | ✅ Yes | Display name |
| **Description** | Textarea | ❌ No | ✅ Yes | Product details |
| **Category** | Text | ❌ No | ✅ Yes | Product category |
| **Quantity** | Number | ✅ Yes | ✅ Yes | Current stock |
| **Reorder Level** | Number | ✅ Yes | ✅ Yes | Alert threshold (default: 10) |
| **Unit Price** | Number | ✅ Yes | ✅ Yes | Price per unit ($) |
| **Supplier** | Text | ❌ No | ✅ Yes | Supplier name |
| **Location** | Text | ❌ No | ✅ Yes | Storage location |

### Restock Form

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Quantity to Add** | Number | ✅ Yes | Must be > 0 |
| **Notes** | Textarea | ❌ No | Reason for restock |

---

## 🔄 Automatic Status Updates

The system automatically updates product status based on quantity:

```
If quantity = 0        → Status = "out_of_stock" (🔴)
If quantity ≤ reorder  → Status = "low_stock" (🟡)
If quantity > reorder  → Status = "active" (🟢)
```

This happens automatically when:
- Creating a new product
- Updating a product
- Restocking a product
- Making a sale (from Sales module)

---

## 🔐 Permission Requirements

| Action | Minimum Role | Can Access |
|--------|--------------|------------|
| **View Inventory** | Employee | Employee, Manager, Admin |
| **Create Product** | Manager | Manager, Admin |
| **Edit Product** | Manager | Manager, Admin |
| **Delete Product** | Manager | Manager, Admin |
| **Restock Product** | Manager | Manager, Admin |

---

## 📊 Search & Filter Features

### Search Box
- Searches in: Product Name, SKU
- Real-time filtering (no submit needed)
- Case-insensitive
- Matches partial text

### Low Stock Filter
- Shows only items with: `quantity ≤ reorder_level`
- Toggle on/off with checkbox
- Works with search (can combine)

---

## ⚠️ Common Scenarios

### Scenario 1: Adding First Time Stock
1. Click "Add Product"
2. Enter SKU (e.g., "PROD-001")
3. Enter name (e.g., "Laptop")
4. Enter unit price (e.g., "999.99")
5. Enter initial quantity (e.g., "50")
6. Set reorder level (e.g., "10")
7. Submit
8. ✅ Product created with "active" status

### Scenario 2: Restocking Low Item
1. See item with 🟡 Low Stock badge
2. Click green restock button
3. Current stock shows (e.g., "Current Stock: 5")
4. Enter quantity to add (e.g., "20")
5. Preview shows "New Stock Level: 25"
6. (Optional) Add notes: "Weekly restock"
7. Confirm
8. ✅ Stock updated, status changes to 🟢 Active

### Scenario 3: Updating Price
1. Click blue edit button on item
2. Change "Unit Price" field
3. (Optional) Update other fields
4. Click "Update Product"
5. ✅ Price updated, reflects in table

### Scenario 4: Removing Discontinued Item
1. Click red delete button
2. Confirm dialog appears: "Are you sure?"
3. Click "OK"
4. ✅ Product removed from inventory

---

## 🐛 Troubleshooting

### Can't See Action Buttons?
- **Cause**: You're logged in as Employee
- **Solution**: Manager or Admin role required for write operations

### SKU Already Exists Error?
- **Cause**: Trying to create product with duplicate SKU
- **Solution**: Use unique SKU for each product

### Can't Update SKU?
- **Cause**: SKU is immutable after creation
- **Solution**: Delete and recreate product with new SKU

### Product Not Updating?
- **Cause**: Network error or permission issue
- **Solution**: Check console for errors, verify Manager+ role

---

## 💡 Best Practices

### Product Creation
- ✅ Use meaningful SKUs (e.g., "ELECT-LAP-001")
- ✅ Set appropriate reorder levels
- ✅ Include supplier information for reordering
- ✅ Add location for warehouse management

### Restock Operations
- ✅ Always add notes for audit trail
- ✅ Verify quantity before confirming
- ✅ Check supplier invoices match restock amount

### Status Management
- ✅ Review low stock items daily
- ✅ Set reorder levels based on sales velocity
- ✅ Update reorder levels seasonally if needed

### Data Maintenance
- ✅ Keep product information current
- ✅ Update prices when supplier costs change
- ✅ Remove discontinued items promptly
- ✅ Use categories consistently

---

## 📈 Metrics to Monitor

Check these regularly for business insights:

1. **Low Stock Count**: Number of 🟡 items
2. **Out of Stock Count**: Number of 🔴 items
3. **Total Inventory Value**: Sum of (quantity × unit_price)
4. **Restock Frequency**: How often items need restocking
5. **Stock Turnover**: How fast inventory moves

*(Note: Advanced analytics coming in Analytics module)*

---

## 🔗 Related Modules

- **Sales Module**: Automatically reduces inventory on sale
- **Receipts Module**: Can auto-update inventory from receipt scan
- **Analytics Module**: Shows inventory performance metrics
- **Employees Module**: Tracks who made inventory changes

---

## 📞 Need Help?

### Common Questions

**Q: Can I bulk import products?**
A: Not yet - manual entry only. Bulk import in future enhancement.

**Q: Can I export inventory to Excel?**
A: Not yet - planned for future release.

**Q: What happens to sales if I delete a product?**
A: Deletion is prevented if product has sales history.

**Q: Can employees restock items?**
A: No - Manager role or higher required.

**Q: Where can I see restock history?**
A: Currently stored in database. History view coming in future release.

---

*Quick Reference Guide*
*Module: Inventory Management v2.0*
*Last Updated: 2024*
