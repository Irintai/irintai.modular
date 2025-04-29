# Python script to detect CUDA and install appropriate PyTorch version
import os
import platform
import subprocess
import sys
from pathlib import Path
import re

def run_command(command):
    """Run a command and return its output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def detect_cuda():
    """Detect if CUDA is available on the system."""
    if platform.system() == "Windows":
        # Check if NVIDIA GPU drivers are installed
        try:
            output = run_command("nvidia-smi")
            # Extract CUDA version from nvidia-smi output
            match = re.search(r"CUDA Version: (\d+\.\d+)", output)
            if match:
                cuda_version = match.group(1)
                print(f"✓ CUDA detected: {cuda_version}")
                return cuda_version
            else:
                print("NVIDIA GPU detected, but CUDA version not found in nvidia-smi output.")
        except Exception as e:
            print("nvidia-smi not found or failed to run. Assuming no CUDA available.")
            # Optionally, check for CUDA toolkit in PATH
            cuda_path = os.environ.get('CUDA_PATH')
            if cuda_path:
                version_file = Path(cuda_path) / 'version.txt'
                if version_file.exists():
                    with open(version_file, 'r') as f:
                        version_line = f.readline()
                        match = re.search(r'(\d+\.\d+)', version_line)
                        if match:
                            cuda_version = match.group(1)
                            print(f"✓ CUDA toolkit detected: {cuda_version}")
                            return cuda_version
    return None

def get_cuda_pytorch_version(cuda_version):
    """Get the appropriate PyTorch CUDA version based on detected CUDA."""
    if cuda_version is None:
        return None
    
    # Map CUDA version to PyTorch CUDA support version
    cuda_float = float(cuda_version)
    
    if cuda_float >= 12.0:
        return "cu121"
    elif cuda_float >= 11.8:
        return "cu118"
    elif cuda_float >= 11.7:
        return "cu117"
    elif cuda_float >= 11.6:
        return "cu116"
    elif cuda_float >= 11.3:
        return "cu113"
    else:
        print(f"⚠ CUDA {cuda_version} detected, but using CPU version as no suitable PyTorch CUDA build exists")
        return None

def install_pytorch(cuda_pytorch_version):
    """Install the appropriate PyTorch version."""
    # Latest stable version as of April 2025
    pytorch_version = "2.1.0" 
    
    if cuda_pytorch_version:
        print(f"Installing PyTorch {pytorch_version} with CUDA support ({cuda_pytorch_version})...")
        cmd = f"pip install torch=={pytorch_version} --index-url https://download.pytorch.org/whl/{cuda_pytorch_version}"
    else:
        print("Installing PyTorch CPU version...")
        cmd = f"pip install torch=={pytorch_version} --index-url https://download.pytorch.org/whl/cpu"
    
    print(f"Running: {cmd}")
    os.system(cmd)

def verify_installation():
    """Verify that PyTorch is installed correctly."""
    print("\nVerifying PyTorch installation:")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU device: {torch.cuda.get_device_name(0)}")
            print(f"GPU count: {torch.cuda.device_count()}")
        else:
            print("CUDA: Not available")
    except ImportError:
        print("❌ PyTorch is not installed correctly")

def install_requirements():
    """Install the remaining packages from requirements.txt."""
    print("\nInstalling remaining requirements...")
    # Use pip to install requirements with upgrade and force-reinstall to avoid version conflicts
    os.system("pip install --upgrade --force-reinstall -r requirements.txt")

def main():
    print("=" * 70)
    print("IrintAI Assistant - CUDA Detection and PyTorch Setup")
    print("=" * 70)
    
    # Ensure we're in a virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠ Warning: Not running in a virtual environment!")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            sys.exit(1)
    
    # Detect CUDA
    cuda_version = detect_cuda()
    
    # Get appropriate PyTorch version
    cuda_pytorch_version = get_cuda_pytorch_version(cuda_version)
    
    # Install PyTorch
    install_pytorch(cuda_pytorch_version)
    
    # Verify installation
    verify_installation()
    
    # Install remaining requirements
    install_requirements()
    
    print("\n✓ Setup complete!")
    print("You can now run IrintAI Assistant using: python irintai.py")

if __name__ == "__main__":
    main()
