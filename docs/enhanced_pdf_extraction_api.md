# Enhanced PDF Extraction System API Documentation

## Module Overview

The Enhanced PDF Extraction System consists of three main components:

1. `utils/enhanced_pdf.py` - Core PDF extraction functionality
2. `utils/pdf_file_ops.py` - Integration with FileOps system
3. `utils/memory_pdf_integration.py` - Integration with Memory system

This documentation provides details on the API for each component, allowing developers to extend or customize the PDF processing capabilities.

## 1. Enhanced PDF Module API

### EnhancedPDFExtractor Class

The `EnhancedPDFExtractor` class provides the core PDF text extraction functionality.

```python
from utils.enhanced_pdf import EnhancedPDFExtractor

# Create an extractor instance
extractor = EnhancedPDFExtractor(
    logger=my_logger_function,  # Optional logger function
    ocr_enabled=True,           # Enable OCR
    ocr_lang="eng"              # OCR language
)
```

#### Constructor Parameters

- `logger`: Optional function for logging messages (defaults to print)
- `ocr_enabled`: Boolean to enable/disable OCR capabilities
- `ocr_lang`: Language code for OCR (defaults to "eng" for English)

#### Main Methods

##### extract_text_from_pdf(pdf_path)

Extracts text from a PDF file with enhanced processing.

```python
success, text = extractor.extract_text_from_pdf("path/to/document.pdf")
```

- **Parameters**:
  - `pdf_path` (str): Path to the PDF file
- **Returns**:
  - Tuple `(success: bool, text: str)`: Success flag and extracted text

#### Internal Methods

These methods handle specific aspects of PDF processing but are not typically called directly:

- `_preprocess_text(text)`: Cleans and normalizes extracted text
- `_apply_global_cleaning(text)`: Applies document-level cleaning operations
- `_find_repeated_lines(lines)`: Identifies repeated headers/footers
- `_ocr_page(page, page_num)`: Performs OCR on a specific page

#### Factory Function

A factory function is provided for easy instantiation:

```python
from utils.enhanced_pdf import get_pdf_extractor

extractor = get_pdf_extractor(logger=my_logger, enable_ocr=True)
```

## 2. PDF File Operations API

### PDFFileOps Class

The `PDFFileOps` class extends the core FileOps functionality with PDF-specific operations.

```python
from utils.pdf_file_ops import PDFFileOps
from utils.file_ops import FileOps

# Create an instance with existing FileOps
file_ops = FileOps(logger=my_logger)
pdf_ops = PDFFileOps(file_ops, enable_ocr=True)
```

#### Constructor Parameters

- `file_ops`: An instance of the FileOps class
- `enable_ocr`: Boolean to enable/disable OCR capabilities

#### Main Methods

##### read_pdf(file_path)

Reads a PDF file with enhanced text extraction.

```python
success, text = pdf_ops.read_pdf("path/to/document.pdf")
```

- **Parameters**:
  - `file_path` (str): Path to the PDF file
- **Returns**:
  - Tuple `(success: bool, text: str)`: Success flag and extracted text

##### get_pdf_metadata(file_path)

Extracts metadata from a PDF file.

```python
metadata = pdf_ops.get_pdf_metadata("path/to/document.pdf")
```

- **Parameters**:
  - `file_path` (str): Path to the PDF file
- **Returns**:
  - Dictionary with PDF metadata (title, author, page count, etc.)

#### Factory Function

A factory function is provided for easy integration:

```python
from utils.pdf_file_ops import extend_file_ops
from utils.file_ops import FileOps

file_ops = FileOps(logger=my_logger)
pdf_ops = extend_file_ops(file_ops, enable_ocr=True)
```

## 3. Memory Integration API

### EnhancedMemoryFileHandler Class

The `EnhancedMemoryFileHandler` class provides integration between the Memory system and enhanced PDF capabilities.

```python
from utils.memory_pdf_integration import EnhancedMemoryFileHandler
from core.memory_system import MemorySystem
from utils.file_ops import FileOps

# Create an instance with existing components
memory_system = MemorySystem(...)
file_ops = FileOps(...)
memory_handler = EnhancedMemoryFileHandler(
    memory_system=memory_system,
    file_ops=file_ops,
    enable_ocr=True, 
    logger=my_logger
)
```

#### Constructor Parameters

- `memory_system`: MemorySystem instance
- `file_ops`: FileOps instance
- `enable_ocr`: Boolean to enable/disable OCR capabilities
- `logger`: Optional logger function

#### Main Methods

##### add_file_to_memory(file_path)

Adds a file to the memory system, using enhanced processing for PDFs.

```python
success = memory_handler.add_file_to_memory("path/to/document.pdf")
```

- **Parameters**:
  - `file_path` (str): Path to the file
- **Returns**:
  - Boolean indicating success or failure

##### add_folder_to_memory(folder_path, extensions=None)

Adds all files in a folder to memory, using enhanced processing for PDFs.

```python
processed, successful = memory_handler.add_folder_to_memory("path/to/folder")
```

- **Parameters**:
  - `folder_path` (str): Path to the folder
  - `extensions` (Optional[List[str]]): List of file extensions to include
- **Returns**:
  - Tuple `(processed: int, successful: int)`: Count of processed and successful files

#### Internal Methods

- `_add_pdf_to_memory(pdf_path)`: Handles PDF-specific processing

#### Factory Function

A factory function is provided for easy instantiation:

```python
from utils.memory_pdf_integration import enhance_memory_system
from core.memory_system import MemorySystem
from utils.file_ops import FileOps

memory_system = MemorySystem(...)
file_ops = FileOps(...)
enhanced_memory = enhance_memory_system(memory_system, file_ops, enable_ocr=True)
```

## Integration Example

Here's a complete example showing how to integrate all components:

```python
from core.memory_system import MemorySystem
from utils.file_ops import FileOps
from utils.memory_pdf_integration import enhance_memory_system

# Initialize core components
memory_system = MemorySystem(index_path="path/to/index.json", logger=print)
file_ops = FileOps(logger=print)

# Create enhanced memory system
enhanced_memory = enhance_memory_system(memory_system, file_ops, enable_ocr=True)

# Process a PDF file
enhanced_memory.add_file_to_memory("path/to/document.pdf")

# Process a folder
processed, successful = enhanced_memory.add_folder_to_memory("path/to/folder")
print(f"Processed {processed} files, {successful} were successful")
```
