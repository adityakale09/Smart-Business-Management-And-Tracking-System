"""
Invoice generation utility for sales
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from io import BytesIO
from typing import Dict, Any


def generate_invoice_pdf(sale_data: Dict[str, Any], product_info: Dict[str, Any]) -> bytes:
    """
    Generate a PDF invoice for a sale
    
    Args:
        sale_data: Sale information (transaction_id, customer_name, quantity, unit_price, etc.)
        product_info: Product information (name, sku, category)
        
    Returns:
        bytes: PDF file content
    """
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
    )
    
    normal_style = styles['Normal']
    right_align_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
    )
    
    # Add company header
    company_name = Paragraph("<b>Smart Business Management System</b>", title_style)
    elements.append(company_name)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add invoice title
    invoice_title = Paragraph(f"<b>INVOICE</b>", heading_style)
    elements.append(invoice_title)
    elements.append(Spacer(1, 0.1*inch))
    
    # Invoice details
    invoice_info = [
        ["Transaction ID:", sale_data.get('transaction_id', 'N/A')],
        ["Invoice Date:", datetime.now().strftime("%B %d, %Y")],
        ["Payment Method:", sale_data.get('payment_method', 'N/A').upper()],
    ]
    
    invoice_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Customer details
    customer_header = Paragraph("<b>Bill To:</b>", heading_style)
    elements.append(customer_header)
    
    customer_name = Paragraph(sale_data.get('customer_name', 'Walk-in Customer'), normal_style)
    elements.append(customer_name)
    elements.append(Spacer(1, 0.3*inch))
    
    # Product table
    product_header = Paragraph("<b>Items:</b>", heading_style)
    elements.append(product_header)
    elements.append(Spacer(1, 0.1*inch))
    
    # Product data
    data = [
        ['Item', 'SKU', 'Quantity', 'Unit Price', 'Total'],
        [
            product_info.get('name', 'Product'),
            product_info.get('sku', 'N/A'),
            str(sale_data.get('quantity', 0)),
            f"₹{sale_data.get('unit_price', 0):.2f}",
            f"₹{sale_data.get('total_amount', 0):.2f}",
        ]
    ]
    
    # Create table
    table = Table(data, colWidths=[2.5*inch, 1.2*inch, 0.8*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Total
    total_data = [
        ['', '', '', 'Subtotal:', f"₹{sale_data.get('total_amount', 0):.2f}"],
        ['', '', '', 'Tax (0%):', '₹0.00'],
        ['', '', '', '<b>Grand Total:</b>', f"<b>₹{sale_data.get('total_amount', 0):.2f}</b>"],
    ]
    
    total_table = Table(total_data, colWidths=[2.5*inch, 1.2*inch, 0.8*inch, 1*inch, 1*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (3, 0), (3, 1), 'Helvetica'),
        ('FONTNAME', (3, 2), (3, 2), 'Helvetica-Bold'),
        ('FONTNAME', (4, 0), (4, 1), 'Helvetica'),
        ('FONTNAME', (4, 2), (4, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 2), (4, 2), 12),
        ('TEXTCOLOR', (3, 2), (4, 2), colors.HexColor('#1a1a1a')),
        ('LINEABOVE', (3, 2), (4, 2), 2, colors.black),
    ]))
    
    elements.append(total_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Notes
    if sale_data.get('notes'):
        notes_header = Paragraph("<b>Notes:</b>", heading_style)
        elements.append(notes_header)
        notes = Paragraph(sale_data.get('notes', ''), normal_style)
        elements.append(notes)
        elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = Paragraph(
        "<i>Thank you for your business!</i><br/>"
        "This is a computer-generated invoice.",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
        )
    )
    elements.append(Spacer(1, 0.5*inch))
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
