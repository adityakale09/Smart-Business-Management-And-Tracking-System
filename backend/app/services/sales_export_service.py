"""
Sales export formatting service.

This module handles sales export payload formatting and file response
construction for CSV and Excel outputs.
"""

from datetime import datetime
from io import BytesIO

from fastapi.responses import Response, StreamingResponse

from app.utils.export_utils import export_to_csv, export_to_excel, prepare_sales_export_data


def build_sales_csv_response(sales: list) -> Response:
    """Build CSV download response for sales data."""
    data, headers = prepare_sales_export_data(sales)
    csv_content = export_to_csv(data, headers)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=sales_export_{datetime.now().strftime('%Y%m%d')}.csv"
        },
    )


def build_sales_excel_response(sales: list) -> StreamingResponse:
    """Build Excel download response for sales data."""
    data, headers = prepare_sales_export_data(sales)
    excel_content = export_to_excel(data, headers, "Sales Report")

    return StreamingResponse(
        BytesIO(excel_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=sales_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        },
    )
