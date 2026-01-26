import tkinter as tk
from src.core.game import Game
from src.ui.figma_view import FigmaView
class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Menu")
        self.geometry("300x200")
        self.resizable(False, False)
        self.game_window = None
        self.figma_window = None
        label = tk.Label(self, text="Choose an option:", font=("Arial", 16))
        label.pack(pady=20)
        play_button = tk.Button(self, text="Play Game", command=self.open_game, width=20)
        play_button.pack(pady=10)
        figma_button = tk.Button(self, text="View Figma Design", command=self.open_figma_view, width=20)
        figma_button.pack(pady=10)
    def open_game(self):
        self.withdraw() # Hide the launcher
        self.game_window = Game(self) # Pass self to the Game window
    def open_figma_view(self):
        self.withdraw() # Hide the launcher
        self.figma_window = FigmaView(self) # Pass self to the FigmaView window
    def show_launcher(self):
        self.deiconify() # Show the launcher again
