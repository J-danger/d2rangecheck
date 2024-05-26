import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, Image
import pytesseract
import cv2
import numpy as np
import keyboard
import json

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'  # your path may be different

class TransparentBox(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Transparent Resizable Box')
        self.geometry('300x200')
        self.overrideredirect(True)  # Remove window decorations
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)  # Set transparency

        self.canvas = tk.Canvas(self, bg='gray', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.resizable(True, True)  # Make window resizable
        self.bind('<B1-Motion>', self.move_window)
        self.bind('<ButtonPress-1>', self.start_move)

        # Add a resize handle
        self.sizer = ttk.Sizegrip(self)
        self.sizer.place(relx=1.0, rely=1.0, anchor='se')

        self.x = None
        self.y = None
        self.processed_text = None  # Define processed_text as an instance variable

        # Bind the hotkey for OCR capture
        keyboard.add_hotkey('space', self.capture_text)

        # Bind the hotkey for toggling Tesseract window
        keyboard.add_hotkey('f9', self.toggle_tesseract_window)

        # Initially hide the Tesseract window
        self.tesseract_window_hidden = True

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def move_window(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")

    def show_text(self, processed_text, cleaned_items):
        if not self.tesseract_window_hidden:  # Check if the tesseract window is not hidden
            if hasattr(self, 'text_window') and self.text_window.winfo_exists():
                # If text window already exists, destroy it
                self.text_window.destroy()

            # Create a transparent window within the main window
            self.text_window = tk.Toplevel(self)
            self.text_window.attributes('-alpha', 0.5)  # Set transparency of the new window
            self.text_window.overrideredirect(True)  # Remove window decorations
            self.text_window.configure(bg='#000000')  # Set background color to transparent black

            # Check if previous coordinates exist and position the window accordingly
            if hasattr(self, 'text_window_x') and hasattr(self, 'text_window_y'):
                self.text_window.geometry("+{}+{}".format(self.text_window_x, self.text_window_y))
            else:
                self.text_window.geometry("+{}+{}".format(self.winfo_x() - 400,
                                                          self.winfo_y()))  # Position the window to the left of the main window

            # Bind mouse events for moving the window
            self.text_window.bind('<B1-Motion>', lambda event: self.move_text_window(event))
            self.text_window.bind('<ButtonPress-1>', lambda event: self.start_move_text_window(event))

            # Bind window closure event to store window position
            self.text_window.protocol("WM_DELETE_WINDOW", self.on_text_window_close)

            # Create a frame to hold the text
            text_frame = tk.Frame(self.text_window, bg='#000000')  # Set frame background color to transparent black
            text_frame.pack(fill=tk.BOTH, expand=True)

            # Create a text widget to display the processed text
            text_area = tk.Text(text_frame, wrap=tk.WORD, bg='#000000', fg='white', font=('Arial', 12),
                                width=250)  # Set text widget background color to transparent black
            text_area.insert(tk.END, "Processed Text:\n")
            text_area.insert(tk.END, processed_text)
            text_area.insert(tk.END, "\n\nCleaned Items:\n")
            formatted_items = json.dumps(cleaned_items, indent=4)  # Pretty-print the cleaned items
            text_area.insert(tk.END, formatted_items)
            text_area.pack(expand=True, fill=tk.BOTH)

            # Resize the window to fit the content
            self.text_window.update_idletasks()
            height = text_area.winfo_reqheight() + self.text_window.winfo_height() - text_frame.winfo_height()
            self.text_window.geometry("250x{}".format(height))

    def move_text_window(self, event):
        # Calculate the new position of the window
        new_x = event.x_root - self.text_window_x
        new_y = event.y_root - self.text_window_y

        # Move the window
        self.text_window.geometry("+{}+{}".format(new_x, new_y))

    def move_text_window(self, event):
        # Move the window according to the mouse drag
        deltax = event.x_root - self.text_window_x
        deltay = event.y_root - self.text_window_y
        new_x = self.text_window.winfo_x() + deltax
        new_y = self.text_window.winfo_y() + deltay
        self.text_window.geometry("+{}+{}".format(new_x, new_y))

    def on_text_window_close(self):
        # Store the position of the text window when it's closed
        self.text_window_x = self.text_window.winfo_x()
        self.text_window_y = self.text_window.winfo_y()
        self.text_window.destroy()

    def capture_text(self):
        x1 = self.winfo_rootx()
        y1 = self.winfo_rooty()
        x2 = x1 + self.winfo_width()
        y2 = y1 + self.winfo_height()

        # Capture the screen area within the box
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        # Convert image to grayscale
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)

        # Perform OCR on the image
        text = pytesseract.image_to_string(img_cv)

        # Process the text to get the first line and replace '@' with 'O' and '®' with 'o'
        first_line = text.split('\n')[0]
        processed_text = first_line.replace('@', 'O').replace('®', 'o')

        # Find matching items
        matching_items = find_matching_items(processed_text)
        cleaned_items = clean_matching_items(matching_items)

        # Show the processed text and cleaned items in a new window
        self.show_text(processed_text, cleaned_items)

    def toggle_tesseract_window(self):
        if self.tesseract_window_hidden:
            self.deiconify()  # Show the Tesseract window
        else:
            self.withdraw()  # Hide the Tesseract window
        self.tesseract_window_hidden = not self.tesseract_window_hidden

def find_matching_items(processed_text, filename='unique_items.txt'):
    matching_items = []
    with open(filename, 'r') as file:
        items_data = json.load(file)
        for item_dict in items_data:
            for item_name, attributes in item_dict.items():
                if item_name.lower() in processed_text.lower():
                    matching_items.append({item_name: attributes})
    return matching_items

def clean_matching_items(matching_items):
    cleaned_items = []
    for item_dict in matching_items:
        for item_name, attributes in item_dict.items():
            if item_name != '':
                cleaned_items.append({item_name: attributes})
    return cleaned_items

if __name__ == '__main__':
    app = TransparentBox()
    app.mainloop()
