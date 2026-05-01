"""
Sales invoice response service.

This module encapsulates invoice PDF response construction for sales.
"""

from io import BytesIO

from fastapi.responses import StreamingResponse

from app.utils.invoice_generator import generate_invoice_pdf


def build_sales_invoice_response(sale_data: dict, product_info: dict, transaction_id: str) -> StreamingResponse:
    """Build invoice PDF download response for a sale."""
    pdf_content = generate_invoice_pdf(sale_data, product_info)

    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{transaction_id}.pdf"
        },
    )
