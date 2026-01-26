import tkinter as tk
from .styles import DeepBlueTheme
import re

class CodeEditor(tk.Text):
    def __init__(self, master=None, **kw):
        super().__init__(master, bg=DeepBlueTheme.BG_EDITOR, fg=DeepBlueTheme.FG_TEXT, 
                         insertbackground="white", selectbackground=DeepBlueTheme.ACCENT, 
                         font=DeepBlueTheme.FONT_CODE, undo=True, relief="flat", padx=10, pady=10, **kw)
        self.bind("<KeyRelease>", self.highlight_syntax)

    def set_text(self, text):
        self.delete("1.0", tk.END)
        self.insert("1.0", text)
        self.highlight_syntax()

    def highlight_syntax(self, event=None):
        self.tag_remove("keyword", "1.0", tk.END)
        self.tag_remove("string", "1.0", tk.END)

        keywords = ["def", "class", "import", "from", "return", "if", "else", "elif", "while", "for", "print", "try", "except"]
        for word in keywords:
            start = "1.0"
            while True:
                pos = self.search(r"\b" + word + r"\b", start, stopindex=tk.END, regexp=True)
                if not pos: break
                end = f"{pos}+{len(word)}c"
                self.tag_add("keyword", pos, end)
                start = end

        start = "1.0"
        while True:
            pos = self.search(r'(".*?")|(\'.*?\')', start, stopindex=tk.END, regexp=True)
            if not pos: break
            end = self.search(r'(")|(\')', f"{pos}+1c", stopindex=tk.END, regexp=True)
            if not end: break
            end = f"{end}+1c"
            self.tag_add("string", pos, end)
            start = end

        self.tag_config("keyword", foreground=DeepBlueTheme.FG_KEYWORD)
        self.tag_config("string", foreground=DeepBlueTheme.FG_STRING)
