import base64
import io
import json
import os
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import uuid
from datetime import datetime
import requests
from openai import OpenAI

import pyautogui
from pynput.keyboard import Key, Listener

# OCR libraries
try:
    import pytesseract
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR libraries not found. Please install: pip install pytesseract easyocr")

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# Global client - will be initialized based on settings
client = None


class SettingsManager:
    def __init__(self):
        self.settings_file = "settings.json"
        self.default_settings = {
            "ai_provider": "openai",  # "openai" or "ollama"
            "openai_model": "gpt-4o-mini",
            "ollama_url": "http://localhost:11434",
            "ollama_model": "gemma3:12b",
            "max_tokens": 1000,
            "temperature": 0.1,
            "system_prompt": "You are an advanced AI assistant specializing in analyzing text extracted from images. Provide clear, accurate, and detailed answers based on the given text content. Focus on understanding the context and providing helpful responses in English with perfect grammar and contextual accuracy.",
            "ocr_method": "pytesseract",  # "pytesseract" or "easyocr"
            "send_text_only": True,  # If True, send only OCR text; if False, send both text and image
            "ocr_language": "eng",  # Language for OCR (eng, spa, fra, deu, etc.)
            "window_transparency": 0.9  # Window transparency (0.1 = very transparent, 1.0 = opaque)
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or create default."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                # Merge with defaults to handle new settings
                settings = self.default_settings.copy()
                settings.update(loaded_settings)
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key):
        """Get a setting value."""
        return self.settings.get(key, self.default_settings.get(key))
    
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
    
    def initialize_ai_client(self):
        """Initialize the AI client based on current settings."""
        global client
        try:
            if self.get("ai_provider") == "openai":
                # Get API key from environment variable
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    client = OpenAI(api_key=api_key)
                else:
                    # Try to use default OpenAI client (might have API key set elsewhere)
                    client = OpenAI()
                return True
            else:  # ollama
                # For Ollama, we'll use requests directly
                client = None
                return True
        except Exception as e:
            print(f"Error initializing AI client: {e}")
            return False


class SettingsWindow:
    def __init__(self, parent, settings_manager, on_save_callback=None):
        self.parent = parent
        self.settings_manager = settings_manager
        self.on_save_callback = on_save_callback
        
        # Create settings window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Settings")
        self.window.geometry("700x800")
        self.window.resizable(True, True)
        
        # Make settings window stay on top of everything including the main window
        self.window.attributes("-topmost", True)
        self.window.lift()
        self.window.focus_force()
        
        # Center the window
        self.window.transient(parent)
        self.window.grab_set()
        
        # Ensure the settings window appears above the parent
        self.center_window()
        
        self.setup_ui()
        self.load_current_settings()
    
    def center_window(self):
        """Center the settings window on the screen and ensure it's visible."""
        self.window.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - 700) // 2
        y = (screen_height - 800) // 2
        
        # Set position and bring to front
        self.window.geometry(f"700x800+{x}+{y}")
        self.window.deiconify()
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.focus_force()
    
    def setup_ui(self):
        """Setup the settings UI with CustomTkinter."""
        # Main container
        main_container = ctk.CTkFrame(self.window)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_container, 
            text="⚙️ Application Settings", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Buttons Frame at the top
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 15))
        
        # Test Connection Button
        self.test_button = ctk.CTkButton(
            button_frame,
            text="Test Connection",
            command=self.test_connection,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=140
        )
        self.test_button.pack(side="left", padx=(0, 10))
        
        # Save Button
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            command=self.save_settings,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=140,
            fg_color="green",
            hover_color="dark green"
        )
        save_button.pack(side="right", padx=(10, 0))
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.close_window,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=100,
            fg_color="red",
            hover_color="dark red"
        )
        cancel_button.pack(side="right")
        
        # Create scrollable frame for content
        self.scrollable_frame = ctk.CTkScrollableFrame(main_container)
        self.scrollable_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # AI Provider Section
        provider_frame = ctk.CTkFrame(self.scrollable_frame)
        provider_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        provider_title = ctk.CTkLabel(
            provider_frame, 
            text="AI Provider", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        provider_title.pack(pady=(15, 10))
        
        self.provider_var = tk.StringVar()
        
        openai_radio = ctk.CTkRadioButton(
            provider_frame, 
            text="OpenAI (GPT-4 Vision)", 
            variable=self.provider_var, 
            value="openai",
            command=self.on_provider_change,
            font=ctk.CTkFont(size=14)
        )
        openai_radio.pack(anchor="w", padx=20, pady=5)
        
        ollama_radio = ctk.CTkRadioButton(
            provider_frame, 
            text="Ollama (Local AI)", 
            variable=self.provider_var, 
            value="ollama",
            command=self.on_provider_change,
            font=ctk.CTkFont(size=14)
        )
        ollama_radio.pack(anchor="w", padx=20, pady=(5, 15))
        
        # OpenAI Settings Frame
        self.openai_frame = ctk.CTkFrame(self.scrollable_frame)
        self.openai_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        openai_title = ctk.CTkLabel(
            self.openai_frame, 
            text="OpenAI Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        openai_title.pack(pady=(15, 10))
        
        # API Key info
        api_info_frame = ctk.CTkFrame(self.openai_frame, fg_color="transparent")
        api_info_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            api_info_frame, 
            text="API Key: Uses OPENAI_API_KEY environment variable", 
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        ).pack(anchor="w")
        
        # Check if API key is available
        api_key_status = "✅ Found" if os.getenv("OPENAI_API_KEY") else "❌ Not found"
        status_color = "green" if os.getenv("OPENAI_API_KEY") else "red"
        ctk.CTkLabel(
            api_info_frame, 
            text=f"Status: {api_key_status}", 
            font=ctk.CTkFont(size=12),
            text_color=status_color
        ).pack(anchor="w")
        
        # Model selection
        ctk.CTkLabel(
            self.openai_frame, 
            text="Model:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.openai_model_var = tk.StringVar()
        openai_model_combo = ctk.CTkComboBox(
            self.openai_frame, 
            variable=self.openai_model_var,
            values=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview"],
            state="readonly"
        )
        openai_model_combo.pack(fill="x", padx=20, pady=(0, 15))
        
        # Ollama Settings Frame
        self.ollama_frame = ctk.CTkFrame(self.scrollable_frame)
        self.ollama_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        ollama_title = ctk.CTkLabel(
            self.ollama_frame, 
            text="Ollama Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        ollama_title.pack(pady=(15, 10))
        
        # URL
        ctk.CTkLabel(
            self.ollama_frame, 
            text="Ollama URL:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.ollama_url_entry = ctk.CTkEntry(
            self.ollama_frame, 
            placeholder_text="Enter Ollama URL (e.g., http://localhost:11434)",
            font=ctk.CTkFont(size=12)
        )
        self.ollama_url_entry.pack(fill="x", padx=20, pady=(0, 5))
        
        # URL examples
        url_help = ctk.CTkLabel(
            self.ollama_frame, 
            text="Examples: http://localhost:11434, http://192.168.1.100:11434", 
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        url_help.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Model selection
        ctk.CTkLabel(
            self.ollama_frame, 
            text="Model:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(5, 5))
        
        # Model frame with combo and refresh button
        model_frame = ctk.CTkFrame(self.ollama_frame, fg_color="transparent")
        model_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.ollama_model_var = tk.StringVar()
        self.ollama_model_combo = ctk.CTkComboBox(
            model_frame, 
            variable=self.ollama_model_var,
            values=["llava", "llava:7b", "llava:13b", "llava:34b", "bakllava", "moondream", "minicpm-v"],
            state="readonly"
        )
        self.ollama_model_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Refresh models button
        refresh_btn = ctk.CTkButton(
            model_frame,
            text="🔄",
            command=self.refresh_ollama_models,
            font=ctk.CTkFont(size=12),
            width=40,
            height=32
        )
        refresh_btn.pack(side="right")
        
        # Model help
        model_help = ctk.CTkLabel(
            self.ollama_frame, 
            text="Common vision models: llava, bakllava, moondream. Click 🔄 to fetch available models.", 
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        model_help.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Advanced Settings Frame
        advanced_frame = ctk.CTkFrame(self.scrollable_frame)
        advanced_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        advanced_title = ctk.CTkLabel(
            advanced_frame, 
            text="Advanced Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_title.pack(pady=(15, 10))
        
        # System Prompt
        ctk.CTkLabel(
            advanced_frame, 
            text="System Prompt:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.system_prompt_textbox = ctk.CTkTextbox(
            advanced_frame,
            height=120,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.system_prompt_textbox.pack(fill="x", padx=20, pady=(0, 15))
        
        # Max Tokens
        tokens_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        tokens_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            tokens_frame, 
            text="Max Tokens:", 
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        self.max_tokens_var = tk.IntVar()
        tokens_entry = ctk.CTkEntry(
            tokens_frame, 
            textvariable=self.max_tokens_var,
            width=100,
            placeholder_text="1000"
        )
        tokens_entry.pack(side="right")
        
        # Temperature
        temp_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        temp_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            temp_frame, 
            text="Temperature:", 
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        self.temperature_var = tk.DoubleVar()
        temp_entry = ctk.CTkEntry(
            temp_frame, 
            textvariable=self.temperature_var,
            width=100,
            placeholder_text="0.1"
        )
        temp_entry.pack(side="right")
        
        # OCR Settings Frame
        ocr_frame = ctk.CTkFrame(self.scrollable_frame)
        ocr_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        ocr_title = ctk.CTkLabel(
            ocr_frame, 
            text="OCR (Text Extraction) Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        ocr_title.pack(pady=(15, 10))
        
        # Send text only option
        self.send_text_only_var = tk.BooleanVar()
        send_text_checkbox = ctk.CTkCheckBox(
            ocr_frame,
            text="Send only extracted text to AI (recommended for better processing)",
            variable=self.send_text_only_var,
            font=ctk.CTkFont(size=12)
        )
        send_text_checkbox.pack(anchor="w", padx=20, pady=(10, 15))
        
        # OCR Method
        ocr_method_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        ocr_method_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            ocr_method_frame, 
            text="OCR Method:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        self.ocr_method_var = tk.StringVar()
        ocr_method_combo = ctk.CTkComboBox(
            ocr_method_frame, 
            variable=self.ocr_method_var,
            values=["pytesseract", "easyocr"],
            state="readonly",
            width=150
        )
        ocr_method_combo.pack(side="right")
        
        # OCR Language
        ocr_lang_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        ocr_lang_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            ocr_lang_frame, 
            text="OCR Language:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        self.ocr_language_var = tk.StringVar()
        ocr_lang_combo = ctk.CTkComboBox(
            ocr_lang_frame, 
            variable=self.ocr_language_var,
            values=["eng", "spa", "fra", "deu", "ita", "por", "rus", "chi_sim", "chi_tra", "jpn", "kor"],
            state="readonly",
            width=150
        )
        ocr_lang_combo.pack(side="right")
        
        # OCR help
        ocr_help = ctk.CTkLabel(
            ocr_frame, 
            text="OCR extracts text from images. Languages: eng=English, spa=Spanish, fra=French, deu=German, etc.", 
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        ocr_help.pack(anchor="w", padx=20, pady=(0, 15))
        
        # UI Settings Frame
        ui_frame = ctk.CTkFrame(self.scrollable_frame)
        ui_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        ui_title = ctk.CTkLabel(
            ui_frame, 
            text="UI Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        ui_title.pack(pady=(15, 10))
        
        # Window Transparency
        transparency_frame = ctk.CTkFrame(ui_frame, fg_color="transparent")
        transparency_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            transparency_frame, 
            text="Window Transparency:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        self.transparency_var = tk.DoubleVar()
        transparency_slider = ctk.CTkSlider(
            transparency_frame,
            from_=0.3,
            to=1.0,
            variable=self.transparency_var,
            number_of_steps=7,
            width=150,
            command=self.on_transparency_change
        )
        transparency_slider.pack(side="right", padx=(10, 0))
        
        # Transparency value label
        self.transparency_label = ctk.CTkLabel(
            transparency_frame,
            text="90%",
            font=ctk.CTkFont(size=12),
            width=40
        )
        self.transparency_label.pack(side="right", padx=(5, 5))
        
        # Transparency help
        transparency_help = ctk.CTkLabel(
            ui_frame, 
            text="Adjust window transparency. Lower values make the window more transparent.", 
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        transparency_help.pack(anchor="w", padx=20, pady=(0, 15))
    
    def on_transparency_change(self, value):
        """Handle transparency slider change."""
        try:
            # Update the label
            percentage = int(value * 100)
            self.transparency_label.configure(text=f"{percentage}%")
            
            # Apply transparency to parent window immediately
            self.parent.attributes("-alpha", value)
        except Exception as e:
            print(f"Error changing transparency: {e}")
    
    def close_window(self):
        """Close the settings window and restore main window focus."""
        try:
            # Restore main window topmost
            self.parent.attributes("-topmost", True)
            self.parent.lift()
            self.window.destroy()
        except Exception as e:
            print(f"Error closing settings window: {e}")
            self.window.destroy()
    
    def load_current_settings(self):
        """Load current settings into the UI."""
        self.provider_var.set(self.settings_manager.get("ai_provider"))
        self.openai_model_var.set(self.settings_manager.get("openai_model"))
        self.ollama_url_entry.delete(0, "end")
        self.ollama_url_entry.insert(0, self.settings_manager.get("ollama_url"))
        self.ollama_model_var.set(self.settings_manager.get("ollama_model"))
        self.max_tokens_var.set(self.settings_manager.get("max_tokens"))
        self.temperature_var.set(self.settings_manager.get("temperature"))
        
        # Load OCR settings
        self.send_text_only_var.set(self.settings_manager.get("send_text_only"))
        self.ocr_method_var.set(self.settings_manager.get("ocr_method"))
        self.ocr_language_var.set(self.settings_manager.get("ocr_language"))
        
        # Load UI settings
        transparency = self.settings_manager.get("window_transparency")
        self.transparency_var.set(transparency)
        percentage = int(transparency * 100)
        self.transparency_label.configure(text=f"{percentage}%")
        
        # Load system prompt
        self.system_prompt_textbox.delete("0.0", "end")
        self.system_prompt_textbox.insert("0.0", self.settings_manager.get("system_prompt"))
        
        self.on_provider_change()
    
    def on_provider_change(self):
        """Handle provider change to show/hide relevant sections."""
        provider = self.provider_var.get()
        if provider == "openai":
            self.openai_frame.pack(fill="x", pady=(0, 20), padx=20, before=self.ollama_frame)
            self.ollama_frame.pack_forget()
        else:
            self.ollama_frame.pack(fill="x", pady=(0, 20), padx=20, before=self.openai_frame)
            self.openai_frame.pack_forget()
    
    def refresh_ollama_models(self):
        """Fetch available models from Ollama instance."""
        try:
            url = self.ollama_url_entry.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter Ollama URL first")
                return
            
            # Fetch models from Ollama
            response = requests.get(f"{url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                # Filter for vision models (models that typically support images)
                vision_keywords = ['llava', 'bakllava', 'moondream', 'minicpm-v', 'vision']
                vision_models = [m for m in models if any(keyword in m.lower() for keyword in vision_keywords)]
                
                if vision_models:
                    # Update combobox values
                    self.ollama_model_combo.configure(values=vision_models)
                    messagebox.showinfo("Success", f"Found {len(vision_models)} vision models:\n" + "\n".join(vision_models[:5]))
                else:
                    # Show all models if no vision models found
                    self.ollama_model_combo.configure(values=models[:10])  # Limit to first 10
                    messagebox.showinfo("Models Found", f"Found {len(models)} models (showing first 10):\n" + "\n".join(models[:5]))
            else:
                messagebox.showerror("Error", f"Failed to fetch models: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to Ollama:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching models:\n{str(e)}")
    
    def test_connection(self):
        """Test the connection to the selected AI provider."""
        provider = self.provider_var.get()
        
        try:
            if provider == "openai":
                # Check if API key is available
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    messagebox.showerror("Error", "OPENAI_API_KEY environment variable not found.\n\nPlease set it in your system environment or terminal:\nexport OPENAI_API_KEY='your-api-key-here'")
                    return
                
                test_client = OpenAI(api_key=api_key)
                # Simple test request
                response = test_client.chat.completions.create(
                    model=self.openai_model_var.get(),
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                messagebox.showinfo("Success", "✅ OpenAI connection successful!")
                
            else:  # ollama
                url = self.ollama_url_entry.get().strip()
                model = self.ollama_model_var.get()
                
                if not url:
                    messagebox.showerror("Error", "Please enter Ollama URL")
                    return
                    
                if not model:
                    messagebox.showerror("Error", "Please select a model")
                    return
                
                # Test Ollama connection with a simple text request first
                test_url = f"{url}/api/generate"
                response = requests.post(
                    test_url,
                    json={
                        "model": model,
                        "prompt": "Hello",
                        "stream": False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", f"✅ Ollama connection successful!\nModel '{model}' is working.")
                else:
                    messagebox.showerror("Error", f"Ollama connection failed: {response.status_code}\n\nMake sure:\n1. Ollama is running\n2. Model '{model}' is installed\n3. URL is correct")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Connection test failed:\n{str(e)}")
    
    def save_settings(self):
        """Save the current settings."""
        try:
            # Validate settings before saving
            if self.provider_var.get() == "openai":
                if not os.getenv("OPENAI_API_KEY"):
                    messagebox.showerror("Error", "OPENAI_API_KEY environment variable not found.\n\nPlease set it before using OpenAI.")
                    return
                if not self.openai_model_var.get():
                    messagebox.showerror("Error", "Please select an OpenAI model")
                    return
            else:  # ollama
                if not self.ollama_url_entry.get().strip():
                    messagebox.showerror("Error", "Please enter Ollama URL")
                    return
                if not self.ollama_model_var.get():
                    messagebox.showerror("Error", "Please select an Ollama model")
                    return
            
            # Update settings
            self.settings_manager.set("ai_provider", self.provider_var.get())
            self.settings_manager.set("openai_model", self.openai_model_var.get())
            self.settings_manager.set("ollama_url", self.ollama_url_entry.get().strip())
            self.settings_manager.set("ollama_model", self.ollama_model_var.get())
            self.settings_manager.set("max_tokens", self.max_tokens_var.get())
            self.settings_manager.set("temperature", self.temperature_var.get())
            self.settings_manager.set("system_prompt", self.system_prompt_textbox.get("0.0", "end-1c"))
            
            # Update OCR settings
            self.settings_manager.set("send_text_only", self.send_text_only_var.get())
            self.settings_manager.set("ocr_method", self.ocr_method_var.get())
            self.settings_manager.set("ocr_language", self.ocr_language_var.get())
            
            # Update UI settings
            self.settings_manager.set("window_transparency", self.transparency_var.get())
            
            # Save to file
            if self.settings_manager.save_settings():
                # Initialize AI client with new settings
                self.settings_manager.initialize_ai_client()
                
                # Call callback if provided
                if self.on_save_callback:
                    self.on_save_callback()
                
                provider_name = "OpenAI" if self.provider_var.get() == "openai" else "Ollama"
                messagebox.showinfo("Success", f"✅ Settings saved successfully!\n\nUsing: {provider_name}")
                self.close_window()
            else:
                messagebox.showerror("Error", "Failed to save settings")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings:\n{str(e)}")



class OCRProcessor:
    """Handle OCR text extraction from images."""
    
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.easyocr_reader = None
    
    def extract_text(self, image):
        """Extract text from an image using the configured OCR method."""
        if not OCR_AVAILABLE:
            return "OCR libraries not available. Please install: pip install pytesseract easyocr"
        
        method = self.settings_manager.get("ocr_method")
        language = self.settings_manager.get("ocr_language")
        
        try:
            if method == "pytesseract":
                return self._extract_with_pytesseract(image, language)
            elif method == "easyocr":
                return self._extract_with_easyocr(image, language)
            else:
                return f"Unknown OCR method: {method}"
        except Exception as e:
            return f"OCR extraction failed: {str(e)}"
    
    def _extract_with_pytesseract(self, image, language):
        """Extract text using pytesseract."""
        try:
            import pytesseract
            # Configure language for pytesseract
            text = pytesseract.image_to_string(image, lang=language)
            return text.strip()
        except ImportError:
            return "pytesseract not installed. Please install: pip install pytesseract"
        except Exception as e:
            return f"Pytesseract error: {str(e)}"
    
    def _extract_with_easyocr(self, image, language):
        """Extract text using easyocr."""
        try:
            import easyocr
            import numpy as np
            
            # Initialize reader if not already done
            if self.easyocr_reader is None:
                # Map common language codes to EasyOCR format
                lang_map = {
                    'eng': 'en',
                    'spa': 'es', 
                    'fra': 'fr',
                    'deu': 'de',
                    'ita': 'it',
                    'por': 'pt',
                    'rus': 'ru',
                    'chi_sim': 'ch_sim',
                    'chi_tra': 'ch_tra',
                    'jpn': 'ja',
                    'kor': 'ko'
                }
                
                easy_lang = lang_map.get(language, 'en')
                self.easyocr_reader = easyocr.Reader([easy_lang])
            
            # Convert PIL image to numpy array
            img_array = np.array(image)
            
            # Extract text
            results = self.easyocr_reader.readtext(img_array)
            
            # Combine all detected text
            text_lines = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter low confidence results
                    text_lines.append(text)
            
            return '\n'.join(text_lines).strip()
            
        except ImportError:
            return "easyocr not installed. Please install: pip install easyocr"
        except Exception as e:
            return f"EasyOCR error: {str(e)}"


class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot App - AI Answer Tool")
        self.root.geometry("600x800")
        
        # Keep window always on top
        self.root.attributes("-topmost", True)
        
        # Make window transparent (macOS)
        try:
            transparency = self.settings_manager.get("window_transparency")
            self.root.attributes("-alpha", transparency)
        except:
            # Fallback for other platforms
            pass
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        self.settings_manager.initialize_ai_client()
        
        # Initialize OCR processor
        self.ocr_processor = OCRProcessor(self.settings_manager)
        
        # Make sure ss directory exists
        if not os.path.exists("ss"):
            os.makedirs("ss")
        
        # Add status tracking
        self.listener = None
        self.is_listening = False
        self.answer_only_mode = False  # Track answer-only view state

        self.screenshot_area = None  # Stores the screenshot coordinates (x, y, width, height)
        self.base64_image = None  # Stores the base64 encoded screenshot
        self.extracted_text = None  # Stores the OCR extracted text

        # Initialize UI
        self.setup_ui()
        
        # Start listening for F10 key in a separate thread
        self.start_keyboard_listener()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
    
    def setup_ui(self):
        """Initialize all UI components with CustomTkinter."""
        # Main container
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status frame
        self.status_frame = ctk.CTkFrame(main_container)
        self.status_frame.pack(fill="x", pady=(0, 15), padx=15)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="🟢 Ready - Press F10 to capture selected area", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="green"
        )
        self.status_label.pack(pady=10)

        # Instructions
        self.label = ctk.CTkLabel(
            main_container, 
            text="1. Click 'Select Area' to choose screenshot region\n2. Press F10 anywhere to capture\n3. Use F11/F12 to adjust transparency\n4. Answer will appear below and be copied to clipboard",
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        self.label.pack(pady=(0, 20), padx=15)

        # Button frame
        self.button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=(0, 15), padx=15)
        
        self.select_button = ctk.CTkButton(
            self.button_frame, 
            text="Select Area", 
            command=self.select_area, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=140,
            fg_color="green",
            hover_color="dark green"
        )
        self.select_button.pack(side="left", padx=5)

        self.clear_button = ctk.CTkButton(
            self.button_frame, 
            text="Clear Selection", 
            command=self.clear_selection, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=140,
            fg_color="orange",
            hover_color="dark orange"
        )
        self.clear_button.pack(side="left", padx=5)

        self.settings_button = ctk.CTkButton(
            self.button_frame, 
            text="⚙️ Settings", 
            command=self.open_settings, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=140,
            fg_color="purple",
            hover_color="dark violet"
        )
        self.settings_button.pack(side="left", padx=5)

        # Add toggle answer-only view button
        self.answer_only_button = ctk.CTkButton(
            self.button_frame, 
            text="Answer Only", 
            command=self.toggle_answer_only_view, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=140,
            fg_color="blue",
            hover_color="dark blue"
        )
        self.answer_only_button.pack(side="left", padx=5)

        self.quit_button = ctk.CTkButton(
            self.button_frame, 
            text="Quit", 
            command=self.quit_app, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=100,
            fg_color="red",
            hover_color="dark red"
        )
        self.quit_button.pack(side="right", padx=5)

        # Answer display area
        self.answer_frame = ctk.CTkFrame(main_container)
        self.answer_frame.pack(fill="both", expand=True, pady=(0, 15), padx=15)
        
        # Answer title (will be recreated in toggle mode)
        self.answer_title_frame = ctk.CTkFrame(self.answer_frame)
        self.answer_title_frame.pack(fill="x", pady=(15, 10), padx=15)
        
        answer_title = ctk.CTkLabel(
            self.answer_title_frame,
            text="AI Response",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        answer_title.pack()
        
        self.answer_label = ctk.CTkTextbox(
            self.answer_frame,
            height=200,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.answer_label.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.answer_label.insert("0.0", "Answer will be displayed here...")

    def update_status(self, message, color="white"):
        """Update the status label with a message and color."""
        self.status_label.configure(text=message, text_color=color)
        self.root.update()
    
    def open_settings(self):
        """Open the settings window."""
        try:
            # Temporarily disable topmost for main window
            self.root.attributes("-topmost", False)
            
            # Create settings window
            settings_window = SettingsWindow(
                self.root, 
                self.settings_manager, 
                on_save_callback=self.on_settings_saved
            )
            
            # Wait for settings window to close, then restore main window topmost
            def restore_topmost():
                self.root.attributes("-topmost", True)
                self.root.lift()
            
            # Check if settings window is still open and restore topmost when closed
            def check_settings_window():
                try:
                    if settings_window.window.winfo_exists():
                        # Settings window still exists, check again in 100ms
                        self.root.after(100, check_settings_window)
                    else:
                        # Settings window closed, restore main window topmost
                        restore_topmost()
                except tk.TclError:
                    # Settings window was destroyed, restore main window topmost
                    restore_topmost()
            
            # Start checking
            self.root.after(100, check_settings_window)
            
        except Exception as e:
            self.log_error(f"Error opening settings: {e}")
            self.update_status("❌ Error opening settings", "red")
            # Restore topmost even if there was an error
            self.root.attributes("-topmost", True)
    
    def on_settings_saved(self):
        """Called when settings are saved."""
        provider = self.settings_manager.get("ai_provider")
        self.update_status(f"⚙️ Settings saved - Using {provider.upper()}", "blue")
        
        # Update transparency from settings
        self.update_transparency()
        
        # Ensure main window stays on top after settings are saved
        self.root.after(200, lambda: self.root.attributes("-topmost", True))
    
    def toggle_answer_only_view(self):
        """Toggle between full view and answer-only view."""
        try:
            self.answer_only_mode = not self.answer_only_mode
            
            if self.answer_only_mode:
                # Hide all components except answer area
                self.status_frame.pack_forget()
                self.label.pack_forget()
                self.button_frame.pack_forget()
                self.answer_title_frame.pack_forget()
                
                # Create minimal header for the button
                self.minimal_header = ctk.CTkFrame(self.answer_frame)
                self.minimal_header.pack(fill="x", pady=(10, 0), padx=15)
                
                # Add title and toggle button to minimal header
                header_content = ctk.CTkFrame(self.minimal_header, fg_color="transparent")
                header_content.pack(fill="x", padx=10, pady=5)
                
                self.answer_title = ctk.CTkLabel(
                    header_content,
                    text="AI Response",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                self.answer_title.pack(side="left")
                
                # Create new toggle button for minimal view
                self.toggle_back_button = ctk.CTkButton(
                    header_content,
                    text="Show All",
                    command=self.toggle_answer_only_view,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    height=30,
                    width=100,
                    fg_color="gray",
                    hover_color="dark gray"
                )
                self.toggle_back_button.pack(side="right")
                
                # Adjust window size to focus on answer
                self.root.geometry("800x500")
                
            else:
                # Show all components back
                if hasattr(self, 'minimal_header'):
                    self.minimal_header.destroy()
                
                # Restore original layout
                self.status_frame.pack(fill="x", pady=(0, 15), padx=15, before=self.answer_frame)
                self.label.pack(pady=(0, 20), padx=15, before=self.answer_frame)
                self.button_frame.pack(fill="x", pady=(0, 15), padx=15, before=self.answer_frame)
                self.answer_title_frame.pack(fill="x", pady=(15, 10), padx=15, before=self.answer_label)
                
                # Restore original window size
                self.root.geometry("900x700")
                
        except Exception as e:
            self.log_error(f"Error toggling view: {e}")
            self.update_status("❌ Error toggling view", "red")
    
    def clear_selection(self):
        """Clear the current area selection."""
        self.screenshot_area = None
        self.update_status("🔄 Selection cleared - Select new area", "orange")
    
    def start_keyboard_listener(self):
        """Start the keyboard listener in a separate thread."""
        def listen():
            try:
                with Listener(on_press=self.on_key_press) as listener:
                    self.listener = listener
                    self.is_listening = True
                    self.update_status("🟢 Ready - Press F10 to capture selected area", "green")
                    listener.join()
            except Exception as e:
                self.log_error(f"Keyboard listener error: {e}")
                self.update_status("❌ Keyboard listener error", "red")
        
        self.listening_thread = threading.Thread(target=listen, daemon=True)
        self.listening_thread.start()
    
    def on_key_press(self, key):
        """Handle key press events."""
        try:
            if key == Key.f10:
                self.capture_screenshot()
            elif key == Key.f11:
                # Increase transparency (less opaque)
                self.adjust_transparency(-0.1)
            elif key == Key.f12:
                # Decrease transparency (more opaque)
                self.adjust_transparency(0.1)
        except AttributeError:
            # Handle special keys that might not have the expected attributes
            pass
    
    def log_error(self, message):
        """Log error messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ERROR: {message}")

    def quit_app(self):
        """Quit the application safely."""
        try:
            if self.listener and self.is_listening:
                self.listener.stop()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            self.log_error(f"Error during quit: {e}")
            self.root.destroy()

    def update_transparency(self):
        """Update window transparency from settings."""
        try:
            transparency = self.settings_manager.get("window_transparency")
            self.root.attributes("-alpha", transparency)
        except Exception as e:
            print(f"Error updating transparency: {e}")
    
    def adjust_transparency(self, delta):
        """Adjust transparency by delta amount (for keyboard shortcuts)."""
        try:
            current = self.settings_manager.get("window_transparency")
            new_value = max(0.3, min(1.0, current + delta))
            self.settings_manager.set("window_transparency", new_value)
            self.settings_manager.save_settings()
            self.root.attributes("-alpha", new_value)
            percentage = int(new_value * 100)
            self.update_status(f"🔍 Transparency: {percentage}%", "blue")
        except Exception as e:
            print(f"Error adjusting transparency: {e}")

    def select_area(self):
        """Use a simple click-and-drag method to select area without canvas."""
        try:
            self.update_status("🎯 Click and drag to select area on screen", "blue")
            
            # Get current window position to stay on same screen
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            
            # Hide main window temporarily
            self.root.withdraw()

            # Create simple overlay on the same screen as main window
            self.overlay = tk.Toplevel()
            
            # Get screen dimensions for the current screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Position overlay on the same screen
            self.overlay.geometry(f"{screen_width}x{screen_height}+{max(0, main_x-100)}+0")
            self.overlay.attributes("-alpha", 0.3)
            self.overlay.attributes("-topmost", True)
            self.overlay.config(cursor="cross", bg="gray25")
            self.overlay.overrideredirect(True)  # Remove window decorations
            
            # Add instruction label
            instruction = tk.Label(
                self.overlay, 
                text="Click and drag to select area • Press ESC to cancel", 
                font=("Arial", 16, "bold"), 
                bg="black", 
                fg="white",
                padx=15,
                pady=8
            )
            instruction.place(x=50, y=50)

            # Initialize selection variables
            self.start_x = None
            self.start_y = None
            self.selection_frame = None

            # Bind events directly to overlay (no canvas)
            self.overlay.bind("<ButtonPress-1>", self.start_selection)
            self.overlay.bind("<B1-Motion>", self.drag_selection)
            self.overlay.bind("<ButtonRelease-1>", self.complete_selection)
            self.overlay.bind("<Escape>", self.cancel_selection)
            self.overlay.bind("<KeyPress-Escape>", self.cancel_selection)
            self.overlay.focus_set()
            
        except Exception as e:
            self.log_error(f"Error in select_area: {e}")
            self.update_status("❌ Error selecting area", "red")
            self.root.deiconify()

    def cancel_selection(self, event=None):
        """Cancel area selection."""
        try:
            if hasattr(self, 'overlay') and self.overlay:
                self.overlay.destroy()
            self.root.deiconify()
            self.update_status("🔄 Selection cancelled", "orange")
        except Exception as e:
            self.log_error(f"Error cancelling selection: {e}")

    def start_selection(self, event):
        """Start the selection rectangle."""
        self.start_x = event.x_root  # Use root coordinates for screen positioning
        self.start_y = event.y_root
        
        # Create a simple frame to show selection area
        if self.selection_frame:
            self.selection_frame.destroy()
            
        self.selection_frame = tk.Frame(
            self.overlay, 
            bg="red", 
            highlightbackground="red", 
            highlightthickness=2
        )
        self.selection_frame.place(x=event.x, y=event.y, width=1, height=1)

    def drag_selection(self, event):
        """Update the selection rectangle while dragging."""
        if self.start_x and self.start_y and self.selection_frame:
            # Calculate relative positions within overlay
            start_x_rel = self.start_x - self.overlay.winfo_rootx()
            start_y_rel = self.start_y - self.overlay.winfo_rooty()
            
            x = min(start_x_rel, event.x)
            y = min(start_y_rel, event.y)
            width = abs(event.x - start_x_rel)
            height = abs(event.y - start_y_rel)
            
            self.selection_frame.place(x=x, y=y, width=width, height=height)

    def complete_selection(self, event):
        """Complete the area selection."""
        try:
            if not self.start_x or not self.start_y:
                self.cancel_selection()
                return
                
            end_x = event.x_root
            end_y = event.y_root
            
            # Calculate final coordinates
            x1 = min(self.start_x, end_x)
            y1 = min(self.start_y, end_y)
            x2 = max(self.start_x, end_x)
            y2 = max(self.start_y, end_y)
            
            width = x2 - x1
            height = y2 - y1
            
            # Minimum size check
            if width < 10 or height < 10:
                self.update_status("❌ Selected area too small (minimum 10x10 pixels)", "red")
                self.cancel_selection()
                return
                
            # Store the selection area (x, y, width, height) in screen coordinates
            self.screenshot_area = (x1, y1, width, height)

            # Clean up
            if self.selection_frame:
                self.selection_frame.destroy()
            self.overlay.destroy()
            self.root.deiconify()
            
            area_info = f"📍 Area selected: {width}x{height} pixels at ({x1},{y1})"
            self.update_status(area_info, "green")
            print(f"Area Selected: {self.screenshot_area}")
            
        except Exception as e:
            self.log_error(f"Error completing selection: {e}")
            self.cancel_selection()

    def capture_screenshot(self):
        """Capture a screenshot of the selected area and process it."""
        if self.screenshot_area is None:
            self.update_status("❌ No area selected. Please select an area first.", "red")
            return
            
        try:
            self.update_status("📸 Capturing screenshot...", "blue")
            
            # Capture screenshot
            screenshot = pyautogui.screenshot(region=self.screenshot_area)
            buffered = io.BytesIO()

            # Save to file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_name = f"screenshot_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            file_path = os.path.join("ss", random_name)
            screenshot.save(file_path, format="PNG")

            # Convert to base64 (still needed if sending both text and image)
            screenshot.save(buffered, format="PNG")
            self.base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Extract text using OCR
            self.update_status("🔍 Extracting text from image...", "blue")
            self.extracted_text = self.ocr_processor.extract_text(screenshot)
            
            print(f"Screenshot saved: {file_path}")
            print(f"Extracted text: {self.extracted_text[:200]}{'...' if len(self.extracted_text) > 200 else ''}")
            
            if self.settings_manager.get("send_text_only"):
                self.update_status("🤖 Processing text with AI...", "blue")
            else:
                self.update_status("🤖 Processing with AI...", "blue")
            
            # Send to AI in separate thread to avoid blocking UI
            threading.Thread(target=self.send_to_ai, daemon=True).start()
            
        except Exception as e:
            self.log_error(f"Failed to capture screenshot: {e}")
            self.update_status("❌ Failed to capture screenshot", "red")

    def send_to_ai(self):
        """Send the extracted text or image to the selected AI provider and display the response."""
        try:
            # Check if we have extracted text
            if not hasattr(self, 'extracted_text'):
                self.root.after(0, self.update_status, "❌ No text extracted", "red")
                return

            provider = self.settings_manager.get("ai_provider")
            send_text_only = self.settings_manager.get("send_text_only")
            
            if provider == "openai":
                self.send_to_openai_api(send_text_only)
            else:
                self.send_to_ollama(send_text_only)
                
        except Exception as e:
            error_msg = f"Failed to get AI response: {str(e)}"
            self.log_error(error_msg)
            self.root.after(0, self.update_status, "❌ AI request failed", "red")
    
    def send_to_openai_api(self, send_text_only=True):
        """Send to OpenAI API."""
        global client
        
        if not client:
            self.root.after(0, self.update_status, "❌ OpenAI client not initialized", "red")
            return
            
        response = client.chat.completions.create(
            model=self.settings_manager.get("openai_model"),
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": self.settings_manager.get("system_prompt"),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Please answer the question and keep short: {self.extracted_text}",
                        }
                    ],
                }
            ],
            max_tokens=self.settings_manager.get("max_tokens"),
            temperature=self.settings_manager.get("temperature")
        )

        answer = response.choices[0].message.content
        # Update UI in main thread
        self.root.after(0, self.display_answer, answer)
    
    def send_to_ollama(self, send_text_only=True):
        """Send to Ollama local instance."""
        url = self.settings_manager.get("ollama_url")
        model = self.settings_manager.get("ollama_model")
        
        # Ollama API endpoint
        api_url = f"{url}/api/generate"
        
        if send_text_only:
            # Send only text to Ollama (for non-vision models or text-only processing)
            payload = {
                "model": model,
                "system": self.settings_manager.get("system_prompt"),
                "prompt": f"Please answer the question and keep short:\n\n{self.extracted_text}",
                "stream": False,
                "options": {
                    "temperature": self.settings_manager.get("temperature"),
                    "num_predict": self.settings_manager.get("max_tokens")
                }
            }
        else:
            # Send both text and image to Ollama (for vision models)
            payload = {
                "model": model,
                "system": self.settings_manager.get("system_prompt"),
                "prompt": f"Please answer the question and keep short: {self.extracted_text}",
                "stream": False,
                "options": {
                    "temperature": self.settings_manager.get("temperature"),
                    "num_predict": self.settings_manager.get("max_tokens")
                }
            }
        
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "No response from Ollama")
            # Update UI in main thread
            self.root.after(0, self.display_answer, answer)
        else:
            error_msg = f"Ollama request failed: {response.status_code} - {response.text}"
            self.log_error(error_msg)
            self.root.after(0, self.update_status, "❌ Ollama request failed", "red")
    
    def display_answer(self, answer):
        """Display the answer in the UI and copy to clipboard."""
        try:
            # Clear and insert new answer
            self.answer_label.delete("0.0", "end")
            self.answer_label.insert("0.0", answer)
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(answer)
            
            # Update status
            word_count = len(answer.split())
            self.update_status(f"✅ Answer ready ({word_count} words) - Copied to clipboard!", "green")
            
            print(f"AI Response ({word_count} words):")
            print(answer[:200] + "..." if len(answer) > 200 else answer)
            
        except Exception as e:
            self.log_error(f"Error displaying answer: {e}")
            self.update_status("❌ Error displaying answer", "red")


if __name__ == "__main__":
    root = ctk.CTk()
    app = ScreenshotApp(root)
    root.mainloop()
