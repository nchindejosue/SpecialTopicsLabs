import tkinter as tk
class FigmaView(tk.Toplevel):
    def __init__(self, launcher):
        super().__init__(launcher)
        self.launcher = launcher
        self.title("Figma Design - TestFrame")
        # Frame dimensions from Figma node 68:4
        width = 625
        height = 574
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Background color from the outer rectangle (68:2)
        # Figma color: rgba(0.753, 0.774, 0.156, 1) -> #C0C528
        bg_color = "#C0C528"
        canvas = tk.Canvas(self, width=width, height=height, bg=bg_color, highlightthickness=0)
        canvas.pack()
        # Inner rectangle (68:3) properties
        # Figma color: rgba(0.586, 0.064, 0.064, 1) -> #961010
        rect_color = "#961010"
        # Calculate relative position and size from Figma's absolute coordinates
        # Frame (x,y): (-1523, -846)
        # Rect (x,y): (-1429, -778)
        # Relative x = -1429 - (-1523) = 94
        # Relative y = -778 - (-846) = 68
        rect_x = 94
        rect_y = 68
        rect_width = 421
        rect_height = 392
        # Draw the inner rectangle
        # Note: Tkinter canvas does not support cornerRadius, so it will be a sharp rectangle.
        canvas.create_rectangle(
            rect_x, 
            rect_y, 
            rect_x + rect_width, 
            rect_y + rect_height, 
            fill=rect_color, 
            outline=""
        )
        # Back Button
        back_button = tk.Button(self, text="Back to Menu", command=self.on_close, relief="flat", bg="white")
        canvas.create_window(width / 2, height - 40, window=back_button)
    def on_close(self):
        self.destroy()
        self.launcher.show_launcher()