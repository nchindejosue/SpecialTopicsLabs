
import tkinter as tk
from .base_page import BasePage
class MenuPage(BasePage):
    """The main menu page."""
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = tk.Label(self, text="Main Menu", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button1 = tk.Button(self, text="Go to Figma Design",
                            command=lambda: controller.show_frame("FigmaPage"))
        button2 = tk.Button(self, text="Go to Game",
                            command=lambda: controller.show_frame("GamePage"))
        button1.pack(pady=10)
        button2.pack(pady=10)
