# Screenshot AI Answer Tool

An improved screenshot application that captures screen areas and gets AI-powered answers using OpenAI's GPT-4 Vision or local Ollama models.

## 🚀 Key Features

### Always On Top
- Application window stays on top of all other windows using `attributes("-topmost", True)`
- Never gets lost behind other applications

### Dual AI Provider Support
- **OpenAI GPT-4 Vision**: Cloud-based AI with excellent vision capabilities
- **Ollama**: Local AI models for privacy and offline usage
- **Easy switching** between providers in settings
- **Automatic model discovery** for Ollama instances

### Enhanced UI
- **Status indicators** with emoji and color coding
- **Improved layout** with organized button groups
- **Settings panel** for easy configuration
- **Better feedback** for all user actions
- **Scrollable text area** for long answers
- **Clear instructions** and visual feedback

## ⚙️ Configuration

### OpenAI Setup
1. **Set environment variable**: `export OPENAI_API_KEY='your-api-key-here'`
2. **Select model** in settings (gpt-4o, gpt-4o-mini, etc.)
3. **No additional configuration needed**

### Ollama Setup
1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Pull a vision model**: `ollama pull llava` or `ollama pull moondream`
3. **Configure URL** in settings (default: http://localhost:11434)
4. **Select model** from available models or use refresh button
5. **Test connection** to verify everything works

### Recommended Vision Models for Ollama
- **llava**: General purpose vision model (7B, 13B, 34B variants)
- **moondream**: Lightweight and fast vision model
- **bakllava**: Alternative vision model
- **minicpm-v**: Compact vision model

## 🛠️ Usage

1. **Run the application**: `python main.py`
2. **Configure AI provider**: Click "⚙️ Settings" to choose OpenAI or Ollama
3. **Select capture area**: Click "Select Area" and drag to select region
4. **Capture**: Press F10 anywhere on your system
5. **Get answer**: AI will analyze the image and provide an answer
6. **Use result**: Answer is displayed and automatically copied to clipboard

## 📋 Requirements

```
openai>=1.0.0
pyautogui>=0.9.54
pynput>=1.7.6
Pillow>=9.0.0
requests>=2.28.0
```

Install with: `pip install -r requirements.txt`

## 🔧 Settings Features

### Smart Configuration
- **Environment-based API keys**: OpenAI API key from OPENAI_API_KEY environment variable
- **Dynamic model discovery**: Automatically fetch available Ollama models
- **Connection testing**: Test your configuration before saving
- **Validation**: Ensures all required settings are configured

### Advanced Options
- **Max Tokens**: Control response length (100-4000)
- **Temperature**: Adjust AI creativity (0.0-2.0)
- **Provider-specific settings**: Different options for OpenAI vs Ollama

## 🎯 Benefits

### OpenAI Advantages
- **Excellent accuracy**: State-of-the-art vision understanding
- **Fast responses**: Cloud-based processing
- **Multiple models**: Choose from various GPT-4 variants
- **Reliable**: Hosted service with high uptime

### Ollama Advantages
- **Privacy**: All processing happens locally
- **Offline capable**: Works without internet connection
- **No API costs**: Free to use after setup
- **Customizable**: Use different local models

## 🔧 Technical Improvements

- **Thread safety**: All UI updates use `root.after()` for thread safety
- **Resource management**: Proper cleanup of listeners and resources
- **Error resilience**: Comprehensive exception handling
- **Code organization**: Better separation of concerns and method organization
- **Memory efficiency**: Proper image handling and base64 encoding

## 🎨 UI Enhancements

- **Color-coded status messages**: Green for success, red for errors, blue for processing
- **Professional button styling**: Consistent colors and spacing
- **Responsive layout**: Better use of space and proper widget organization
- **Visual feedback**: Clear indication of current state and actions

## 🔒 Security & Privacy

- **Local screenshot storage**: All screenshots saved locally in `ss/` directory
- **Secure API usage**: Proper OpenAI API integration with error handling
- **Clean shutdown**: Proper resource cleanup on application exit
