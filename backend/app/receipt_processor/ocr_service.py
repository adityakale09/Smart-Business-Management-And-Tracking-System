"""
OCR Service for extracting text from images and PDFs
"""

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
from typing import Optional
import os
import warnings


class OCRService:
    """Service for extracting text from receipt images and PDFs"""
    
    def __init__(self):
        """Initialize OCR service and detect Tesseract installation"""
        self.tesseract_available = False
        
        # Try to set tesseract path if on Windows
        if os.name == 'nt':
            # Common Tesseract installation paths on Windows
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_available = True
                    print(f"[OCR] Tesseract found at: {path}")
                    break
        
        if not self.tesseract_available:
            # Try to detect tesseract in PATH
            try:
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
                print("[OCR] Tesseract found in system PATH")
            except Exception:
                warnings.warn(
                    "Tesseract OCR is not installed. Receipt OCR features will not work. "
                    "Download from: https://github.com/UB-Mannheim/tesseract/wiki"
                )
    
    def _check_tesseract(self):
        """Check if Tesseract is available"""
        if not self.tesseract_available:
            raise Exception(
                "Tesseract OCR is not installed. Please install it from: "
                "https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Windows: Download and install tesseract-ocr-w64-setup-5.x.x.exe\n"
                "After installation, restart the backend server."
            )
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from a PIL Image
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text as string
        """
        self._check_tesseract()
        
        try:
            # Convert image to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use Tesseract OCR
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            if "tesseract" in str(e).lower():
                raise Exception(
                    "Tesseract OCR is not properly configured. "
                    "Please install from: https://github.com/UB-Mannheim/tesseract/wiki"
                )
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str, first_page: Optional[int] = None, last_page: Optional[int] = None) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            first_page: First page to extract (1-indexed)
            last_page: Last page to extract (1-indexed)
            
        Returns:
            Extracted text as string
        """
        self._check_tesseract()
        
        try:
            # Convert PDF to images
            if first_page and last_page:
                images = convert_from_path(pdf_path, first_page=first_page, last_page=last_page)
            else:
                images = convert_from_path(pdf_path)
            
            # Extract text from each page
            all_text = []
            for image in images:
                text = self.extract_text_from_image(image)
                all_text.append(text)
            
            return "\n\n".join(all_text)
        except Exception as e:
            if "tesseract" in str(e).lower():
                raise Exception(
                    "Tesseract OCR is not properly configured. "
                    "Please install from: https://github.com/UB-Mannheim/tesseract/wiki"
                )
            raise Exception(f"PDF OCR extraction failed: {str(e)}")
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from uploaded file (image or PDF)
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Extracted text as string
        """
        try:
            # Check file extension
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == '.pdf':
                # Save PDF temporarily and process
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                try:
                    text = self.extract_text_from_pdf(tmp_path)
                finally:
                    os.unlink(tmp_path)
                
                return text
            else:
                # Assume it's an image
                image = Image.open(io.BytesIO(file_content))
                return self.extract_text_from_image(image)
        except Exception as e:
            raise Exception(f"File OCR extraction failed: {str(e)}")


# Singleton instance
ocr_service = OCRService()

