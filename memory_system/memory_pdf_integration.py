#Memory System PDF Enhancement Integration for IrintAI Assistant
#This module provides integration between the memory system and enhanced PDF capabilities.

import os
from typing import Tuple, Dict, Any, Optional, List
from core.memory_system import MemorySystem
from file_operations.pdf_file_ops import PDFFileOps
from file_operations.file_ops import FileOps

class EnhancedMemoryFileHandler:
    """
    Enhanced file handler for the memory system with improved PDF handling
    """
    
    def __init__(self, memory_system: MemorySystem, file_ops: FileOps, enable_ocr: bool = False, logger=None):
        """
        Initialize the enhanced memory file handler
        
        Args:
            memory_system: MemorySystem instance
            file_ops: FileOps instance
            enable_ocr: Whether to enable OCR for PDF files
            logger: Optional logger function
        """
        self.memory_system = memory_system
        self.file_ops = file_ops
        self.pdf_ops = PDFFileOps.extend_file_ops(file_ops, enable_ocr=enable_ocr)
        self.logger = logger or memory_system.log
        
    def add_file_to_memory(self, file_path: str) -> bool:
        """
        Add a file to the memory system with enhanced handling
        
        Args:
            file_path: Path to the file to add
            
        Returns:
            True if file was successfully added to memory, False otherwise
        """
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle PDF files with enhanced extraction
        if file_ext == '.pdf':
            return self._add_pdf_to_memory(file_path)
        else:
            # Use standard file handling for other file types
            success, content = self.file_ops.read_file(file_path)
            if success:
                return self.memory_system.add_file_to_index(file_path, content)
            return False
            
    def _add_pdf_to_memory(self, pdf_path: str) -> bool:
        """
        Add a PDF file to memory with enhanced extraction
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if PDF was successfully added to memory, False otherwise
        """
        # Use enhanced PDF extraction
        success, content = self.pdf_ops.read_pdf(pdf_path)
        
        if not success:
            self.logger(f"[Memory PDF] Failed to extract text from {pdf_path}")
            return False
            
        # Get PDF metadata for additional context
        metadata = self.pdf_ops.get_pdf_metadata(pdf_path)
        
        # Add the extracted content to the memory system
        return self.memory_system.add_file_to_index(pdf_path, content)
        
    def add_folder_to_memory(self, folder_path: str, extensions: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        Add all files in a folder to memory
        
        Args:
            folder_path: Path to the folder
            extensions: Optional list of file extensions to include
            
        Returns:
            Tuple with (number of files processed, number of files successfully added)
        """
        # Get default extensions if not provided
        if extensions is None:
            extensions = self.file_ops.get_supported_extensions()
            
        # Get all matching files
        all_files = []
        for ext in extensions:
            all_files.extend(self.file_ops.get_files_by_type(folder_path, ext))
            
        # Process each file
        processed = 0
        successful = 0
        
        for file_path in all_files:
            processed += 1
            if self.add_file_to_memory(file_path):
                successful += 1
                
        return processed, successful

def enhance_memory_system(memory_system: MemorySystem, file_ops: FileOps, enable_ocr: bool = False) -> EnhancedMemoryFileHandler:
    """
    Create an enhanced memory file handler with improved PDF capabilities

    Args:
        memory_system: MemorySystem instance
        file_ops: FileOps instance
        enable_ocr: Whether to enable OCR for PDF files
    """

    return EnhancedMemoryFileHandler(memory_system, file_ops, enable_ocr=enable_ocr)
