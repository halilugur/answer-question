# answer-question

**Screenshot AI Answer Tool**  
A desktop application that captures any part of your screen and provides AI-powered answers using either **OpenAI’s GPT-4 Vision** or **local Ollama** models.

---

## Features

- **Always On Top Window**  
  The app window stays above all others using `attributes("-topmost", True)` so it’s always accessible.
  
- **Two AI Providers**  
  - **OpenAI GPT-4 Vision** — Cloud-based, advanced visual understanding.  
  - **Ollama** — Local AI models for privacy and offline usage.
  
- **Enhanced UI**  
  - Emoji-based status indicators with color coding.  
  - Scrollable text area for long AI responses.  
  - Organized settings panel for provider and model selection.
  
- **Keyboard Shortcut**  
  Press **F10** to capture and process instantly.

---

## Requirements

Install Python 3.9+ and the dependencies:

```bash
pip install -r requirements.txt
```

**requirements.txt**
```
openai>=1.0.0
pyautogui>=0.9.54
pynput>=1.7.6
Pillow>=9.0.0
requests>=2.28.0
```

---

## Setup

### OpenAI GPT-4 Vision
1. Get your API key from [platform.openai.com](https://platform.openai.com/).  
2. Set it as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
3. In the app settings, choose **OpenAI** as the provider and select your model (e.g., `gpt-4o`, `gpt-4o-mini`).

---

### Ollama (Local AI)
1. Install Ollama from [ollama.ai](https://ollama.ai/).  
2. Pull a vision-capable model:
   ```bash
   ollama pull llava
   ollama pull moondream
   ```
3. Make sure Ollama is running (`ollama serve`).  
4. In the app settings, select **Ollama** as the provider, set the API URL (`http://localhost:11434` by default), and choose your model.

---

## Usage

1. **Run the app**:
   ```bash
   python main.py
   ```
2. **Configure provider** in settings (⚙️).  
3. **Select Area** → drag to capture part of the screen.  
4. Press **F10** to capture and process.  
5. AI-generated answer appears in the text box and is copied to clipboard.

---

## Benefits

### OpenAI
- Cloud processing with high accuracy.
- Supports multiple GPT-4 variants.
- Fast and reliable.

### Ollama
- 100% local processing — privacy-first.
- Works offline after model download.
- No per-request API cost.

---

## Technical Improvements

- **Thread-Safe UI Updates**: Uses `root.after()` to avoid crashes.  
- **Resource Management**: Cleans up listeners and temporary files.  
- **Better Error Handling**: Graceful fallback if provider fails.  
- **Organized Code**: Modular functions and improved readability.  
- **UI Enhancements**:  
  - Status indicators  
  - Scrollable output  
  - Resizable window

---

## Security & Privacy

- Screenshots saved locally in the `ss/` directory.  
- No unauthorized uploads — only sent to your selected provider.  
- Environment variables protect API keys.  
- App cleans up temporary resources on exit.

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Roadmap

- [ ] Add Whisper integration for audio-based Q&A.  
- [ ] Add history panel for previous answers.  
- [ ] Improve multi-monitor capture support.  
- [x] Dark mode UI.

---

## Author

Created by [Halil Uğur](https://github.com/halilugur).
