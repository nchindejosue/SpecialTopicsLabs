
import tkinter as tk
from .base_page import BasePage
class GamePage(BasePage):
    """Placeholder page for the game."""
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = tk.Label(self, text="Game Page", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Back to Menu",
                           command=lambda: controller.show_frame("MenuPage"))
        button.pack()
