"""
OCR Service for extracting text from images and PDFs
"""

import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageOps
import io
from typing import Optional
import os
import warnings
import re


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

    def _prepare_image_variants(self, image: Image.Image):
        """Build a few preprocessed variants and let OCR choose the best output."""
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Scale up smaller receipts so table text becomes easier to read.
        width, height = image.size
        if width < 1600:
            scale = 2
            image = image.resize((width * scale, height * scale), Image.Resampling.LANCZOS)

        grayscale = ImageOps.grayscale(image)
        autocontrast = ImageOps.autocontrast(grayscale)
        sharpened = autocontrast.filter(ImageFilter.SHARPEN)
        thresholded = sharpened.point(lambda p: 255 if p > 160 else 0)
        thresholded_soft = sharpened.point(lambda p: 255 if p > 145 else 0)

        return [image, autocontrast, thresholded_soft, thresholded]

    def _score_receipt_text(self, text: str) -> int:
        """Score OCR output quality for tabular receipts."""
        if not text:
            return 0

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        score = 0

        for line in lines:
            if re.search(r'^\d+\s+.+\s+\d+\.\d{1,2}\s+\d+\.\d{1,2}$', line):
                score += 10
            elif re.search(r'^\d+\s+.+\s+\d+\.\d{1,2}$', line):
                score += 6

            if re.search(r'\b(qty|description|unit price|amount|subtotal|total)\b', line, re.IGNORECASE):
                score += 3

            if re.search(r'\d+\.\d{1,2}', line):
                score += 1

        # Prefer outputs that include enough lines to parse rows.
        score += min(len(lines), 20)
        return score
    
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
            variants = self._prepare_image_variants(image)
            configs = [
                '--oem 3 --psm 6 -c preserve_interword_spaces=1',
                '--oem 3 --psm 4 -c preserve_interword_spaces=1',
                '--oem 3 --psm 11 -c preserve_interword_spaces=1',
            ]

            best_text = ""
            best_score = -1

            for variant in variants:
                for config in configs:
                    text = pytesseract.image_to_string(variant, lang='eng', config=config)
                    score = self._score_receipt_text(text)
                    if score > best_score:
                        best_score = score
                        best_text = text

            return best_text.strip()
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

