"""
IrintAI Assistant - PDF and CUDA Diagnostic Tool
This module provides diagnostic functions to check PDF integration and PyTorch CUDA support
"""
import os
import sys
import importlib
import subprocess
from pathlib import Path

def print_header(text):
    """Print a section header"""
    print(f"\n{'=' * 80}")
    print(f" {text}")
    print(f"{'=' * 80}")

def check_pdf_integration():
    """Check PDF integration components and dependencies"""
    print_header("PDF INTEGRATION CHECK")
    
    results = {}
    
    try:
        # Check if PyMuPDF is installed
        try:
            import fitz
            results["pymupdf"] = {
                "status": "Success",
                "message": f"PyMuPDF (fitz) is installed: version {fitz.version}"
            }
            print(f"✓ PyMuPDF (fitz) is installed: version {fitz.version}")
        except ImportError:
            results["pymupdf"] = {
                "status": "Failure",
                "message": "PyMuPDF (fitz) is not installed"
            }
            print("✗ PyMuPDF (fitz) is not installed")
        
        # Check PDF operations module
        sys.path.insert(0, os.getcwd())
        try:
            from utils.pdf_operations import extract_text_from_pdf
            
            # Try to extract text from a sample PDF if available
            sample_path = Path("data/samples/sample.pdf")
            if sample_path.exists():
                try:
                    text = extract_text_from_pdf(str(sample_path))
                    text_length = len(text)
                    results["pdf_operations"] = {
                        "status": "Success",
                        "message": f"PDF operations module works: extracted {text_length} characters"
                    }
                    print(f"✓ PDF operations module works: extracted {text_length} characters")
                except Exception as e:
                    results["pdf_operations"] = {
                        "status": "Warning",
                        "message": f"PDF operations module imported but extraction failed: {e}"
                    }
                    print(f"⚠ PDF operations module imported but extraction failed: {e}")
            else:
                results["pdf_operations"] = {
                    "status": "Warning",
                    "message": "PDF operations module imported but no sample PDF to test"
                }
                print("⚠ PDF operations module imported but no sample PDF to test")
        except ImportError as e:
            results["pdf_operations"] = {
                "status": "Failure",
                "message": f"PDF operations module not found: {e}"
            }
            print(f"✗ PDF operations module not found: {e}")
        
        # Check memory PDF integration
        try:
            from core.memory_system import PDFMemoryIntegration
            results["pdf_memory"] = {
                "status": "Success",
                "message": "PDF memory integration module found"
            }
            print("✓ PDF memory integration module found")
        except ImportError as e:
            results["pdf_memory"] = {
                "status": "Warning",
                "message": f"PDF memory integration not found: {e}"
            }
            print(f"⚠ PDF memory integration not found: {e}")
        
        # Check for OCR capabilities
        try:
            from PIL import Image
            import pytesseract
            
            # Check if tesseract command is available
            try:
                version = pytesseract.get_tesseract_version()
                results["ocr"] = {
                    "status": "Success",
                    "message": f"OCR support available (Tesseract v{version})"
                }
                print(f"✓ OCR support available (Tesseract v{version})")
            except pytesseract.TesseractNotFoundError:
                results["ocr"] = {
                    "status": "Warning",
                    "message": "pytesseract installed but Tesseract binary not found"
                }
                print("⚠ pytesseract installed but Tesseract binary not found")
        except ImportError:
            results["ocr"] = {
                "status": "Warning",
                "message": "OCR libraries not installed (pytesseract/PIL)"
            }
            print("⚠ OCR libraries not installed (pytesseract/PIL)")
        
        return results
    except Exception as e:
        error_message = f"PDF integration check failed: {e}"
        print(f"✗ {error_message}")
        return {"status": "Failure", "message": error_message}


def check_torch_cuda():
    """Check PyTorch CUDA support"""
    print_header("PYTORCH CUDA CHECK")
    
    results = {}
    
    try:
        # Check if PyTorch is installed
        try:
            import torch
            torch_version = torch.__version__
            results["torch"] = {
                "status": "Success", 
                "message": f"PyTorch is installed: version {torch_version}"
            }
            print(f"✓ PyTorch is installed: version {torch_version}")
            
            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                device_count = torch.cuda.device_count()
                cuda_version = torch.version.cuda
                device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
                
                results["cuda"] = {
                    "status": "Success",
                    "message": f"CUDA is available (v{cuda_version}), {device_count} device(s): {device_name}"
                }
                print(f"✓ CUDA is available (v{cuda_version})")
                print(f"  - Devices: {device_count}")
                print(f"  - GPU: {device_name}")
                
                # Test tensor operations on CUDA
                try:
                    x = torch.rand(5, 3).cuda()
                    y = torch.rand(5, 3).cuda()
                    z = x + y
                    results["cuda_test"] = {
                        "status": "Success",
                        "message": "CUDA tensor operations work correctly"
                    }
                    print("✓ CUDA tensor operations work correctly")
                except Exception as e:
                    results["cuda_test"] = {
                        "status": "Warning",
                        "message": f"CUDA tensor operations failed: {e}"
                    }
                    print(f"⚠ CUDA tensor operations failed: {e}")
            else:
                results["cuda"] = {
                    "status": "Warning",
                    "message": "CUDA is not available"
                }
                print("⚠ CUDA is not available")
                
                # Check for CPU-only operation
                try:
                    x = torch.rand(5, 3)
                    y = torch.rand(5, 3)
                    z = x + y
                    results["cpu_test"] = {
                        "status": "Success",
                        "message": "CPU tensor operations work correctly"
                    }
                    print("✓ CPU tensor operations work correctly")
                except Exception as e:
                    results["cpu_test"] = {
                        "status": "Failure",
                        "message": f"CPU tensor operations failed: {e}"
                    }
                    print(f"✗ CPU tensor operations failed: {e}")
        
        except ImportError:
            results["torch"] = {
                "status": "Failure",
                "message": "PyTorch is not installed"
            }
            print("✗ PyTorch is not installed")
            
        # Check for NVIDIA driver info if on suitable platform
        if sys.platform.startswith('win') or sys.platform.startswith('linux'):
            try:
                if sys.platform.startswith('win'):
                    proc = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
                else:
                    proc = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
                
                if proc.returncode == 0:
                    driver_info = proc.stdout.split('\n')[2:6]
                    results["nvidia_driver"] = {
                        "status": "Success",
                        "message": "NVIDIA driver installed",
                        "details": '\n'.join(driver_info).strip()
                    }
                    print("✓ NVIDIA driver installed")
                    print(f"  - {driver_info[0].strip()}")
                else:
                    results["nvidia_driver"] = {
                        "status": "Warning",
                        "message": "NVIDIA driver info command failed"
                    }
                    print("⚠ NVIDIA driver info command failed")
            except FileNotFoundError:
                results["nvidia_driver"] = {
                    "status": "Warning",
                    "message": "nvidia-smi not found, NVIDIA driver may not be installed"
                }
                print("⚠ nvidia-smi not found, NVIDIA driver may not be installed")
        
        return results
    except Exception as e:
        error_message = f"PyTorch CUDA check failed: {e}"
        print(f"✗ {error_message}")
        return {"status": "Failure", "message": error_message}

if __name__ == "__main__":
    check_pdf_integration()
    print("\n")
    check_torch_cuda()
