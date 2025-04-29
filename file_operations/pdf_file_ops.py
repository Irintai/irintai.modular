"""
Enhanced PDF Extraction for IrintAI Assistant

This module provides improved PDF text extraction capabilities using:
1. PyMuPDF for robust PDF parsing
2. Text preprocessing to clean extracted content
3. Optional OCR for image-based content
"""

import os
import re
import fitz  # PyMuPDF
import base64
from typing import Tuple, List, Dict, Any, Optional
from file_operations.file_ops import FileOps

# Try to import OCR dependencies, but make them optional
try:
    import pytesseract
    from PIL import Image
    import numpy as np
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class PDFFileOps:
    """Extends FileOps with enhanced PDF handling capabilities"""
    
    def __init__(self, file_ops: FileOps, enable_ocr: bool = False):
        """
        Initialize PDF file operations
        
        Args:
            file_ops: Base FileOps instance
            enable_ocr: Whether to enable OCR for image-based text
        """
        self.file_ops = file_ops
        self.pdf_extractor = get_pdf_extractor(logger=file_ops.log, enable_ocr=enable_ocr)
        
    def read_pdf(self, file_path: str) -> Tuple[bool, str]:
        """
        Read a PDF file with enhanced text extraction
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple with success flag and extracted text
        """
        # Check if file exists
        if not os.path.exists(file_path):
            self.file_ops.log(f"[PDF] File not found: {file_path}")
            return False, f"Error: File not found: {file_path}"
            
        # Check if file is a PDF
        if not file_path.lower().endswith(".pdf"):
            self.file_ops.log(f"[PDF] Not a PDF file: {file_path}")
            return False, "Error: Not a PDF file"
            
        # Extract text from PDF using enhanced extractor
        return self.pdf_extractor.extract_text_from_pdf(file_path)
        
    def get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata from a PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            import fitz  # PyMuPDF
            
            if not os.path.exists(file_path):
                self.file_ops.log(f"[PDF] File not found: {file_path}")
                return {"error": "File not found"}
                
            # Open the PDF
            doc = fitz.open(file_path)
            
            # Get basic metadata
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", ""),
                "page_count": len(doc),
                "file_size": os.path.getsize(file_path),
                "has_text": any(page.get_text().strip() for page in doc),
                "is_encrypted": doc.is_encrypted,
                "permissions": doc.permissions if hasattr(doc, "permissions") else None
            }
            
            # Additional statistics
            text_length = sum(len(page.get_text()) for page in doc)
            metadata["total_text_length"] = text_length
            
            # Count images
            image_count = 0
            for page in doc:
                image_count += len(page.get_images())
            metadata["image_count"] = image_count
            
            doc.close()
            return metadata
            
        except Exception as e:
            self.file_ops.log(f"[PDF] Error getting metadata: {e}")
            return {"error": str(e)}

    @staticmethod
    def extend_file_ops(file_ops: FileOps, enable_ocr: bool = False) -> "PDFFileOps":
        """
        Extend a FileOps instance with enhanced PDF capabilities
        
        Args:
            file_ops: The FileOps instance to extend
            enable_ocr: Whether to enable OCR for image-based text
            
        Returns:
            PDFFileOps instance
        """
        return PDFFileOps(file_ops, enable_ocr=enable_ocr)

class EnhancedPDFExtractor:
    """Enhanced PDF extraction with preprocessing and OCR capabilities"""
    
    def __init__(self, logger=None, ocr_enabled=False, ocr_lang="eng"):
        """
        Initialize the PDF extractor with optional OCR support
        
        Args:
            logger: Optional logging function
            ocr_enabled: Whether to use OCR when text extraction fails
            ocr_lang: Language for OCR (default: English)
        """
        self.logger = logger or print
        self.ocr_enabled = ocr_enabled and HAS_OCR
        self.ocr_lang = ocr_lang
        
        # If OCR is enabled but dependencies aren't installed, log a warning
        if ocr_enabled and not HAS_OCR:
            self.logger("[PDF] OCR requested but dependencies not installed. Install pytesseract and Pillow.")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Extract text from a PDF with enhanced quality
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple with success flag and extracted text
        """
        if not os.path.exists(pdf_path):
            self.logger(f"[PDF] File not found: {pdf_path}")
            return False, f"Error: File not found: {pdf_path}"
            
        try:
            self.logger(f"[PDF] Extracting text from {os.path.basename(pdf_path)}")
            document = fitz.open(pdf_path)
            
            content = []
            images_processed = 0
            
            for page_num, page in enumerate(document):
                # First try regular text extraction
                text = page.get_text("text")
                
                # If page has very little text and OCR is enabled, try OCR
                if len(text.strip()) < 100 and self.ocr_enabled:
                    # Only process the page with OCR if it likely contains images
                    if page.get_images():
                        ocr_text = self._ocr_page(page, page_num)
                        if ocr_text.strip():
                            text = ocr_text
                            images_processed += 1
                
                # Clean and preprocess the text
                text = self._preprocess_text(text)
                
                # Add page number as metadata
                page_header = f"\n\n--- Page {page_num + 1} ---\n\n"
                content.append(page_header + text)
            
            document.close()
            
            if images_processed > 0:
                self.logger(f"[PDF] Used OCR on {images_processed} pages with minimal text")
                
            full_text = "\n".join(content)
            
            # Apply global cleaning
            full_text = self._apply_global_cleaning(full_text)
            
            return True, full_text
            
        except Exception as e:
            self.logger(f"[PDF] Error extracting text: {e}")
            return False, f"Error: {str(e)}"
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove null bytes and other control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]', '', text)
        
        # Replace Unicode replacement characters
        text = text.replace("\uFFFD", "")
        
        # Fix common PDF encoding issues with math symbols
        text = text.replace("α", "alpha")
        text = text.replace("β", "beta")
        text = text.replace("γ", "gamma")
        text = text.replace("Δ", "Delta")
        text = text.replace("π", "pi")
        text = text.replace("∞", "infinity")
        
        # Clean up excessive whitespace without removing paragraph breaks
        text = re.sub(r' {2,}', ' ', text)
        
        # Fix hyphens at end of lines (attempt to identify hyphenated words)
        text = re.sub(r'([a-zA-Z])- *\n *([a-zA-Z])', r'\1\2', text)
        
        return text
    
    def _apply_global_cleaning(self, text: str) -> str:
        """Apply global text cleaning operations"""
        # Remove PDF artifacts like headers/footers that repeat on every page
        # This uses a heuristic to detect repeated lines at page boundaries
        lines = text.split('\n')
        repeated_lines = self._find_repeated_lines(lines)
        
        for pattern in repeated_lines:
            if len(pattern) > 5:  # Only remove if substantial pattern found
                text = text.replace(pattern, '')
        
        # Final cleanup of multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _find_repeated_lines(self, lines: List[str]) -> List[str]:
        """Find lines that repeat across pages (likely headers/footers)"""
        patterns = []
        threshold = 3  # Minimum occurrences to consider a line as repeating
        
        # Count line frequencies
        line_counts = {}
        for line in lines:
            line_clean = line.strip()
            if len(line_clean) > 5:  # Ignore very short lines
                line_counts[line_clean] = line_counts.get(line_clean, 0) + 1
        
        # Find repeated lines
        for line, count in line_counts.items():
            if count >= threshold:
                patterns.append(line)
                
        return patterns
    
    def _ocr_page(self, page, page_num: int) -> str:
        """Extract text from a page using OCR"""
        if not HAS_OCR:
            return ""
            
        try:
            # Convert page to a PIL Image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Increase resolution for OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Use pytesseract for OCR
            text = pytesseract.image_to_string(img, lang=self.ocr_lang)
            return text
        except Exception as e:
            self.logger(f"[PDF] OCR failed on page {page_num}: {e}")
            return ""

def get_pdf_extractor(logger=None, enable_ocr=False):
    """Factory function to create a PDF extractor"""
    return EnhancedPDFExtractor(logger=logger, ocr_enabled=enable_ocr)
