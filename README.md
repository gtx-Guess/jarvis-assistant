# Jarvis AI Assistant

A personal AI assistant inspired by Iron Man's Jarvis, featuring voice interaction, screen monitoring, and intelligent routing between local and cloud AI models.

## Features

- **Voice and Text Input**: Supports both speech-to-text and keyboard input modes
- **Screen Analysis**: Can capture and analyze code or content on your screen
- **Multi-Model AI**: Routes requests between local Ollama models and cloud APIs (OpenAI/Claude)
- **Conversation Memory**: Maintains context across interactions
- **Audio Output**: Text-to-speech responses using natural voice synthesis
- **Hot Word Activation**: Responds to natural language triggers

## Architecture

Jarvis uses a tiered approach for AI processing:

1. **Local Model (Ollama)**: Handles simple queries for speed and privacy
2. **Cloud APIs**: Complex analysis, coding tasks, and advanced reasoning
3. **Automatic Escalation**: Smart routing based on query complexity and keywords

## Requirements

### System Requirements
- **Python 3.12** (required)
- **Operating System**: Windows, macOS, or Linux

### Required System Libraries

**macOS (using Homebrew):**
```bash
brew install tesseract
brew install portaudio
```

**Windows (using winget):**
```bash
winget install UB-Mannheim.TesseractOCR
# Note: Add Tesseract to your PATH manually after installation
# Restart VS Code/terminal after updating PATH
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr portaudio19-dev
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Setup

### 1. Clone and Install Dependencies
```bash
git clone <your-repo-url>
cd jarvis-ai
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
# Required: At least one API key
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Optional: Model preference (default: true)
USE_OPENAI=true

# Optional: Audio settings (default: auto)
ENABLE_AUDIO=auto
```

### 3. Ollama Setup (Optional but Recommended)
For local AI processing, run Ollama in Docker:

```bash
cd ollama/
docker-compose up -d
```

Then install a lightweight model:
```bash
docker exec ollama-server ollama pull qwen2.5:7b
```

## Usage

### Running Jarvis
```bash
python Jarvis.py
```

The application will automatically detect if audio hardware is available and choose the appropriate input mode.

### Voice Commands
- **Activation**: Say "Jarvis" or other hot words to activate
- **Screen Analysis**: "Analyze this code", "Look at my screen", "Debug this code"
- **Screen Monitoring**: "Start monitoring" / "Stop monitoring"
- **Memory Management**: "Clear history", "Start fresh"
- **Shutdown**: "Shutdown" or "Shut down"

### Text Mode
If audio is unavailable, Jarvis runs in text mode. Type commands directly and use the same natural language patterns.

## Development

### VS Code Setup
The project includes a VS Code launch configuration for debugging:
- Open the project in VS Code
- Use F5 to start debugging
- Breakpoints and step-through debugging are fully supported

### Project Structure
```
jarvis-ai/
├── Jarvis.py                 # Main application entry point
├── requirements.txt          # Python dependencies
├── utils/
│   ├── utils.py             # Core AI and utility functions
│   ├── escalation_keywords.json  # Keywords for model routing
│   └── class_models/
│       └── ScreenMonitor.py # Screen capture and analysis
├── ollama/                  # Docker setup for local AI model
├── windows/                 # Windows-specific setup files
└── mac/                     # macOS-specific setup files
```

### Configuration Options

**Model Selection:**
- Set `USE_OPENAI=true` for OpenAI GPT models
- Set `USE_OPENAI=false` for Anthropic Claude models

**Audio Configuration:**
- `ENABLE_AUDIO=true`: Force audio mode
- `ENABLE_AUDIO=false`: Force text-only mode  
- `ENABLE_AUDIO=auto`: Auto-detect hardware capabilities

## Troubleshooting

### Audio Issues
- **No microphone detected**: Check system audio permissions
- **TTS not working**: Verify pygame and edge-tts installation
- **Poor speech recognition**: Try adjusting microphone sensitivity

### Screen Capture Issues
- **OCR not working**: Ensure Tesseract is installed and in PATH
- **Permission errors**: Grant screen recording permissions (macOS/Windows)

### API Issues
- **Slow responses**: Check internet connection and API key validity
- **Ollama connection failed**: Verify Docker container is running on port 11434

### Platform-Specific Notes

**Windows:**
- Tesseract must be manually added to PATH
- Restart development environment after PATH changes

**macOS:**
- May require granting microphone and screen recording permissions
- Use Homebrew for easiest dependency installation
