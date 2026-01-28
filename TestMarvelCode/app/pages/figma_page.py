
import tkinter as tk
from .base_page import BasePage
class FigmaPage(BasePage):
    """Placeholder page for Figma designs."""
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = tk.Label(self, text="Figma Designs Page", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Back to Menu",
                           command=lambda: controller.show_frame("MenuPage"))
        button.pack()
