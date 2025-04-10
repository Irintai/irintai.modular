# Irintai: Your Personal AI Companion

## Welcome to Irintai

### What is Irintai?
Irintai is a locally-hosted, privacy-first AI assistant designed to be:
- 100% Offline
- Completely Private
- Fully Customizable
- Accessible to Everyone

## 1. Understanding Irintai

### Core Philosophy
Irintai is built on the belief that:
- Technology should empower individuals
- Privacy is a fundamental right
- AI should be accessible to everyone
- Users should have full control over their digital assistant

### Key Features
- Local AI processing
- No external data transmission
- Customizable personality
- Adaptive learning
- Comprehensive privacy controls

## 2. Getting Started

### Minimum System Requirements
- Computer running:
  - Windows 10+
  - macOS 10.15+
  - Linux (Ubuntu 20.04+)
- Python 3.8 or higher
- 8GB RAM (16GB recommended)
- 10GB free disk space
- Optional but recommended: NVIDIA GPU

### Installation Steps

#### 1. Install Prerequisites
```bash
# Install Python (if not already installed)
# Windows/macOS: Download from python.org
# Linux:
sudo apt update
sudo apt install python3 python3-pip
```

#### 2. Install Ollama
1. Visit [ollama.ai](https://ollama.ai/download)
2. Download the installer for your operating system
3. Follow installation instructions

#### 3. Clone Irintai Repository
```bash
# Using Git
git clone https://github.com/yourusername/irintai.git
cd irintai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. First-Time Setup

### Initial Configuration
1. Open Irintai
2. Go to Settings Tab
3. Configure:
   - Model Path
   - Embedding Model
   - Memory Mode
   - System Prompt

### Choosing Your First Model
- Recommended Starter Models:
  1. mistral:7b-instruct (Balanced)
  2. llama3:8b (Good performance)
  3. phi-2 (Lightweight)

## 4. Basic Usage Guide

### Chat Interface
- Type your message in the input field
- Press Enter or click Send
- Explore different models and settings

### Memory System
- Load documents via Memory Tab
- Choose Memory Mode:
  - Off: No memory context
  - Manual: Search documents manually
  - Auto: Automatic context addition
  - Background: Silent context integration

### Customization Options
- Adjust system prompt
- Configure model settings
- Modify interaction modes
- Personalize AI behavior

## 5. Privacy and Control

### Complete Offline Operation
- No internet connection required
- All processing happens locally
- No data leaves your computer

### Data Management
- Full control over stored documents
- Ability to clear memory
- Configurable storage locations

## 6. Troubleshooting

### Common Issues
1. Model won't start
   - Ensure Ollama is running
   - Check disk space
   - Verify model download

2. Performance Problems
   - Use smaller models
   - Enable 8-bit mode
   - Close other resource-intensive apps

### Getting Help
- Check logs in `data/logs/`
- Consult documentation
- Community forums

## 7. Ethical AI Use

### Responsible AI Guidelines
- Respect privacy
- Use for positive purposes
- Understand AI limitations
- Maintain critical thinking

## 8. Continuous Learning

### Resources
- Official Documentation
- Community Forums
- GitHub Repository
- Tutorial Videos

## Conclusion

Irintai is more than just an AI—it's a personal, private assistant designed to respect your autonomy and empower your digital experience.

---

**Remember**: You are in control. Irintai is a tool to assist, not to replace human judgment.

**Happy Exploring!**
