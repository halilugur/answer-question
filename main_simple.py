import base64
import io
import threading
import tkinter as tk
import uuid
from openai import OpenAI

import pyautogui
from pynput.keyboard import Key, Listener

client = OpenAI()


class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot App")
        self.root.geometry("900x300")

        self.screenshot_area = None  # Stores the screenshot coordinates (x, y, width, height)
        self.base64_image = None  # Stores the base64 encoded screenshot

        # Create GUI elements
        self.label = tk.Label(
            self.root, text="Press 'Select Area' to choose the screenshot region.\nPress F10 to capture.",
            font=("Arial", 12)
        )
        self.label.pack(pady=20)

        self.select_button = tk.Button(self.root, text="Select Area", command=self.select_area, font=("Arial", 12))
        self.select_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", command=self.quit_app, font=("Arial", 12), fg="red")
        self.quit_button.pack(pady=10)

        # Create GUI elements
        self.answer_label = tk.Text(self.root, height=10, width=120)
        self.answer_label.insert(tk.END, "Answer will be displayed here.")
        self.answer_label.pack(pady=10)

        # Start listening for F10 key in a separate thread
        self.listening_thread = threading.Thread(target=self.listen_for_f10, daemon=True)
        self.listening_thread.start()

    def quit_app(self):
        """Quit the application."""
        self.root.quit()

    def listen_for_f10(self):
        """Continuously check for the F10 key press."""
        while True:
            try:
                with Listener(on_press=self.capture_screenshot) as listener:
                    listener.join()
                if pyautogui.press("f10"):  # Check for F10 key press
                    if self.screenshot_area is None:
                        print("Error", "No area selected. Please select an area first.")
                    else:
                        print("F10 pressed! Capturing screenshot...")
                        self.capture_screenshot("f10")
            except Exception as e:
                print(f"Error in F10 listener: {e}")

    def select_area(self):
        """Open a fullscreen window to select a screenshot region."""
        # self.root.withdraw()  # Hide the main window

        self.overlay = tk.Toplevel()
        self.overlay.geometry("1800x1000")
        self.overlay.attributes("-alpha", 0.3)
        self.overlay.config(cursor="cross", bg="gray")
        self.canvas = tk.Canvas(self.overlay, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.overlay.bind("<ButtonPress-1>", self.start_selection)
        self.overlay.bind("<B1-Motion>", self.drag_selection)
        self.overlay.bind("<ButtonRelease-1>", self.complete_selection)

    def start_selection(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red",
                                                 width=2)

    def drag_selection(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def complete_selection(self, event):
        end_x, end_y = event.x, event.y
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        self.screenshot_area = (x1, y1, x2 - x1, y2 - y1)

        self.overlay.destroy()
        self.root.deiconify()  # Show the main window
        print("Area Selected", f"Selected area: {self.screenshot_area}")

    def capture_screenshot(self, key):
        """Capture a screenshot of the saved area and store it as a base64 string."""
        if key == Key.f10:
            try:
                screenshot = pyautogui.screenshot(region=self.screenshot_area)
                buffered = io.BytesIO()

                random_name = f"screenshot_{uuid.uuid4().hex}.png"
                screenshot.save("ss/" + random_name, format="PNG")

                screenshot.save(buffered, format="PNG")
                self.base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

                print("Screenshot Captured", "Screenshot captured and stored as Base64.")
                print("Base64 Image:", self.base64_image[:100], "...")  # Print the first 100 characters
                self.send_to_openai()
            except Exception as e:
                print("Error", f"Failed to capture screenshot: {e}")

    def send_to_openai(self):
        """Send the base64 image to OpenAI and display the response."""
        try:
            if not self.base64_image:
                print("Error", "No Base64 image found. Please take a screenshot first.")
                return

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a helpful assistant and don't explain anything. just given answer.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self.base64_image}"
                                },
                            },
                        ],
                    }
                ],
            )

            answer = response.choices[0].message.content
            print("OpenAI Response", answer)
            self.answer_label.delete(1.0, tk.END)
            self.answer_label.insert(tk.END, answer)
            self.root.clipboard_clear()
            self.root.clipboard_append(answer)
        except Exception as e:
            print("Error", f"Failed to send to OpenAI: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()
