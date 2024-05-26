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

        # Bind the hotkey
        keyboard.add_hotkey('space', self.capture_text)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def move_window(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")

    def show_text(self, processed_text, cleaned_items):
        text_window = tk.Toplevel(self)
        text_window.title("OCR Result")
        text_window.geometry("400x300")

        text_area = tk.Text(text_window, wrap=tk.WORD)
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, "Processed Text:\n")
        text_area.insert(tk.END, processed_text)
        text_area.insert(tk.END, "\n\nCleaned Items:\n")
        formatted_items = json.dumps(cleaned_items, indent=4)  # Pretty-print the cleaned items
        text_area.insert(tk.END, formatted_items)

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
