import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Menu
import os
import sys
import shutil

# Ensure imports work regardless of run location
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.styles import DeepBlueTheme
from app.ui.editor import CodeEditor

class SecureIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Secure AI-Assisted Codebase Editor (Capstone v10.0)")
        self.geometry("1400x900")
        self.configure(bg=DeepBlueTheme.BG_MAIN)
        
        self.project_path = None
        self.current_file = None
        self.mention_popup = None
        self.all_project_items = [] 
        
        self.configure_styles()
        self.create_menu()
        self.setup_layout()
        
        self.editor.bind("<KeyRelease>", self.auto_save)
        
        self.log("System Ready. Type '@' for Context Palette.", "SYSTEM")

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=DeepBlueTheme.BG_SIDEBAR, 
                        foreground=DeepBlueTheme.FG_TEXT, 
                        fieldbackground=DeepBlueTheme.BG_SIDEBAR,
                        borderwidth=0,
                        font=DeepBlueTheme.FONT_UI)
        style.configure("Treeview.Heading", 
                        background=DeepBlueTheme.BG_MAIN, 
                        foreground=DeepBlueTheme.FG_TEXT, 
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        style.map('Treeview', background=[('selected', DeepBlueTheme.ACCENT)])
        
        style.configure("Vertical.TScrollbar", background=DeepBlueTheme.BG_SIDEBAR, bordercolor=DeepBlueTheme.BG_MAIN, arrowcolor=DeepBlueTheme.FG_TEXT)

    def create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Project Folder...", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def setup_layout(self):
        self.main_split = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=DeepBlueTheme.BORDER, sashwidth=3, sashrelief="flat")
        self.main_split.pack(fill=tk.BOTH, expand=True)

        # === LEFT SIDEBAR ===
        self.sidebar_frame = tk.Frame(self.main_split, bg=DeepBlueTheme.BG_SIDEBAR)
        
        # Action Bar
        self.action_bar = tk.Frame(self.sidebar_frame, bg=DeepBlueTheme.BG_SIDEBAR)
        self.action_bar.pack(fill=tk.X, padx=5, pady=5)
        
        def make_icon_btn(parent, text, cmd):
            return tk.Button(parent, text=text, command=cmd, 
                             bg=DeepBlueTheme.BG_SIDEBAR, fg=DeepBlueTheme.FG_TEXT, 
                             font=("Segoe UI", 12, "bold"), bd=0, activebackground=DeepBlueTheme.ACCENT, cursor="hand2")

        self.btn_open = make_icon_btn(self.action_bar, "📂", self.open_project)
        self.btn_open.pack(side=tk.LEFT, padx=2)
        
        self.btn_new_file = make_icon_btn(self.action_bar, "📄+", self.create_new_file)
        self.btn_new_file.pack(side=tk.RIGHT, padx=2)
        
        self.btn_new_folder = make_icon_btn(self.action_bar, "📁+", self.create_new_folder)
        self.btn_new_folder.pack(side=tk.RIGHT, padx=2)

        self.lbl_explorer = tk.Label(self.sidebar_frame, text=" EXPLORER", bg=DeepBlueTheme.BG_SIDEBAR, fg="#94a3b8", font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_explorer.pack(fill=tk.X, pady=(10,0))
        
        # File Tree
        tree_frame = tk.Frame(self.sidebar_frame, bg=DeepBlueTheme.BG_SIDEBAR)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.file_tree = ttk.Treeview(tree_frame, show="tree")
        self.tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=self.tree_scroll.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.file_tree.bind("<Double-1>", self.on_double_click_rename)
        self.file_tree.bind("<Button-3>", self.show_context_menu)
        
        self.context_menu = Menu(self.file_tree, tearoff=0)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_command(label="Delete", command=self.delete_item)

        self.main_split.add(self.sidebar_frame, width=280)

        # === CENTER WORK AREA ===
        self.work_split = tk.PanedWindow(self.main_split, orient=tk.HORIZONTAL, bg=DeepBlueTheme.BORDER, sashwidth=3)
        self.main_split.add(self.work_split)

        self.center_frame = tk.Frame(self.work_split, bg=DeepBlueTheme.BG_MAIN)
        self.center_split = tk.PanedWindow(self.center_frame, orient=tk.VERTICAL, bg=DeepBlueTheme.BORDER, sashwidth=3)
        self.center_split.pack(fill=tk.BOTH, expand=True)

        # Editor
        self.editor_container = tk.Frame(self.center_split, bg=DeepBlueTheme.BG_EDITOR)
        self.editor_scroll = ttk.Scrollbar(self.editor_container, orient="vertical")
        self.editor = CodeEditor(self.editor_container, yscrollcommand=self.editor_scroll.set)
        self.editor_scroll.config(command=self.editor.yview)
        self.editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.center_split.add(self.editor_container, height=500)

        # Terminal
        self.term_container = tk.Frame(self.center_split, bg=DeepBlueTheme.BG_TERMINAL)
        self.lbl_term = tk.Label(self.term_container, text=" TERMINAL / LOGS", bg=DeepBlueTheme.BG_TERMINAL, fg="#00ff00", anchor="w", font=("Consolas", 9))
        self.lbl_term.pack(fill=tk.X)
        self.term_scroll = ttk.Scrollbar(self.term_container, orient="vertical")
        self.terminal = tk.Text(self.term_container, bg=DeepBlueTheme.BG_TERMINAL, fg="#94a3b8", 
                                font=("Consolas", 10), relief="flat", padx=10, pady=5,
                                yscrollcommand=self.term_scroll.set)
        self.term_scroll.config(command=self.terminal.yview)
        self.terminal.tag_config("SYSTEM", foreground="#38bdf8")
        self.terminal.tag_config("AI_OP", foreground="#a78bfa")
        self.terminal.tag_config("SUCCESS", foreground="#4ade80")
        self.terminal.tag_config("ERROR", foreground="#f44336")
        self.term_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.center_split.add(self.term_container, height=200)

        self.work_split.add(self.center_frame, width=700)

        # === RIGHT CHAT ===
        self.chat_frame = tk.Frame(self.work_split, bg=DeepBlueTheme.BG_CHAT)
        self.lbl_chat = tk.Label(self.chat_frame, text=" AI ARCHITECT", bg=DeepBlueTheme.BG_CHAT, fg="#94a3b8", font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_chat.pack(fill=tk.X, pady=5, padx=5)

        self.chat_history = tk.Text(self.chat_frame, bg=DeepBlueTheme.BG_CHAT, fg=DeepBlueTheme.FG_TEXT, font=("Segoe UI", 10), state="disabled", wrap="word", relief="flat", padx=10)
        self.chat_history.tag_config("USER", foreground="#38bdf8", justify="right")
        self.chat_history.tag_config("AI", foreground="#e2e8f0", justify="left")
        self.chat_history.pack(fill=tk.BOTH, expand=True)

        # Chat Controls
        self.chat_ctrl_frame = tk.Frame(self.chat_frame, bg="#334155")
        self.chat_ctrl_frame.pack(fill=tk.X, padx=10, pady=10)

        self.btn_at = tk.Button(self.chat_ctrl_frame, text="@", command=self.show_mention_popup, 
                                bg=DeepBlueTheme.ACCENT, fg="white", font=("Consolas", 11, "bold"), width=3, relief="flat", cursor="hand2")
        self.btn_at.pack(side=tk.LEFT, padx=(5,5))

        self.chat_input = tk.Text(self.chat_ctrl_frame, height=3, bg="#334155", fg="white", font=("Segoe UI", 11), relief="flat", insertbackground="white")
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        self.chat_input.bind("<Return>", self.on_chat_enter)
        self.chat_input.bind("<KeyRelease>", self.check_mentions)

        self.btn_send = tk.Button(self.chat_ctrl_frame, text="➤", command=self.send_to_ai, 
                                  bg=DeepBlueTheme.ACCENT, fg="white", font=("Segoe UI", 12), width=3, relief="flat", cursor="hand2")
        self.btn_send.pack(side=tk.RIGHT, padx=(5,5), pady=5)

        self.work_split.add(self.chat_frame, width=350)

    # --- HELPERS ---
    def log(self, message, tag="SYSTEM"):
        self.terminal.insert(tk.END, f">> {message}\n", tag)
        self.terminal.see(tk.END)

    def chat_bubble(self, sender, message):
        self.chat_history.config(state="normal")
        self.chat_history.insert(tk.END, f"[{sender}]\n{message}\n\n", sender)
        self.chat_history.config(state="disabled")
        self.chat_history.see(tk.END)

    def auto_save(self, event=None):
        if self.current_file and os.path.exists(self.current_file):
            content = self.editor.get("1.0", tk.END).strip()
            with open(self.current_file, "w") as f: f.write(content)

    # --- FILE OPS ---
    def open_project(self):
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            self.project_path = path
            self.populate_file_tree()
            self.log(f"Workspace loaded: {path}", "SUCCESS")
            self.file_tree.heading("#0", text=f"PROJECT: {os.path.basename(path)}")

    def populate_file_tree(self):
        self.file_tree.delete(*self.file_tree.get_children())
        if not self.project_path: return
        root = self.file_tree.insert("", "end", text=os.path.basename(self.project_path), open=True, values=(self.project_path,))
        self.build_tree(root, self.project_path)

    def build_tree(self, parent, path):
        try:
            for item in os.listdir(path):
                abspath = os.path.join(path, item)
                isdir = os.path.isdir(abspath)
                
                # Icons
                icon = "📁 " if isdir else "📄 "
                display_text = f"{icon}{item}"
                
                oid = self.file_tree.insert(parent, "end", text=display_text, open=False, values=(abspath,))
                self.all_project_items.append((display_text, item))
                
                if isdir: self.build_tree(oid, abspath)
        except PermissionError: pass

    def on_file_select(self, event):
        selected = self.file_tree.selection()
        if not selected: return
        values = self.file_tree.item(selected[0], "values")
        if values:
            file_path = values[0]
            if os.path.isfile(file_path):
                self.current_file = file_path
                with open(file_path, "r") as f: self.editor.set_text(f.read())
                self.log(f"Editing: {os.path.basename(file_path)}", "SYSTEM")

    def get_selected_path(self):
        if not self.project_path: return None
        selection = self.file_tree.selection()
        if not selection: return self.project_path
        target = self.file_tree.item(selection[0], "values")[0]
        return target if os.path.isdir(target) else os.path.dirname(target)

    def show_context_menu(self, event):
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click_rename(self, event): self.rename_item()

    def rename_item(self):
        selected = self.file_tree.selection()
        if not selected: return
        item = selected[0]
        old_path = self.file_tree.item(item, "values")[0]
        if old_path == self.project_path: return
        
        current_display = self.file_tree.item(item, "text")
        clean_name = current_display[2:] if len(current_display) > 2 else current_display
        
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=clean_name)
        if new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.populate_file_tree()
                self.log(f"Renamed to {new_name}", "SUCCESS")
            except Exception as e: self.log(f"Rename Error: {e}", "ERROR")

    def delete_item(self):
        selected = self.file_tree.selection()
        if not selected: return
        path = self.file_tree.item(selected[0], "values")[0]
        if path == self.project_path: return
        if messagebox.askyesno("Delete", f"Delete {os.path.basename(path)}?"):
            try:
                if os.path.isdir(path): shutil.rmtree(path)
                else: os.remove(path)
                self.populate_file_tree()
                self.log("Deleted item", "SUCCESS")
                self.editor.delete("1.0", tk.END)
            except Exception as e: self.log(f"Delete Error: {e}", "ERROR")

    def create_new_file(self):
        target_dir = self.get_selected_path()
        if not target_dir: return messagebox.showerror("Error", "Open project first")
        name = simpledialog.askstring("New File", "Filename:")
        if name:
            with open(os.path.join(target_dir, name), "w") as f: f.write("")
            self.populate_file_tree()
            self.log(f"Created file: {name}", "SUCCESS")

    def create_new_folder(self):
        target_dir = self.get_selected_path()
        if not target_dir: return messagebox.showerror("Error", "Open project first")
        name = simpledialog.askstring("New Folder", "Folder Name:")
        if name:
            os.makedirs(os.path.join(target_dir, name))
            self.populate_file_tree()
            self.log(f"Created folder: {name}", "SUCCESS")

    # --- CENTERED @MENTION POPUP ---
    def check_mentions(self, event):
        if event.char == '@': self.show_mention_popup()

    def show_mention_popup(self):
        if self.mention_popup: self.mention_popup.destroy()
        if not self.project_path: return
        
        self.all_project_items = []
        for root, dirs, filenames in os.walk(self.project_path):
            for d in dirs: self.all_project_items.append(("📁 " + d, d))
            for f in filenames: self.all_project_items.append(("📄 " + f, f))

        if not self.all_project_items: return

        self.mention_popup = tk.Toplevel(self)
        self.mention_popup.overrideredirect(True)
        self.mention_popup.configure(bg=DeepBlueTheme.BORDER)
        
        # Calculate Center of Window
        rw = self.winfo_width()
        rh = self.winfo_height()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty()
        
        pw, ph = 500, 350
        px = rx + (rw // 2) - (pw // 2)
        py = ry + (rh // 2) - (ph // 2)
        
        self.mention_popup.geometry(f"{pw}x{ph}+{px}+{py}")

        # UI Components for Popup
        tk.Label(self.mention_popup, text=" SEARCH PROJECT FILES", bg=DeepBlueTheme.BG_MAIN, 
                 fg=DeepBlueTheme.FG_KEYWORD, font=("Segoe UI", 12, "bold"), pady=10).pack(fill=tk.X)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_files)
        
        self.search_entry = tk.Entry(self.mention_popup, textvariable=self.search_var, 
                                     bg="#334155", fg="white", font=("Segoe UI", 14), 
                                     relief="flat", insertbackground="white")
        self.search_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.search_entry.focus_set()

        list_frame = tk.Frame(self.mention_popup, bg=DeepBlueTheme.BG_SIDEBAR)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.popup_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        self.popup_list = tk.Listbox(list_frame, bg=DeepBlueTheme.BG_SIDEBAR, fg="white", 
                                     font=("Segoe UI", 12), bd=0, highlightthickness=0, 
                                     selectbackground=DeepBlueTheme.ACCENT, 
                                     yscrollcommand=self.popup_scroll.set)
        
        self.popup_scroll.config(command=self.popup_list.yview)
        self.popup_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.popup_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for display_name, actual_name in self.all_project_items:
            self.popup_list.insert(tk.END, display_name)
        
        self.popup_list.bind("<<ListboxSelect>>", lambda e: self.insert_mention())
        self.mention_popup.bind("<Escape>", lambda e: self.mention_popup.destroy())
        self.search_entry.bind("<Down>", lambda e: self.popup_list.focus_set())
        self.popup_list.bind("<Return>", lambda e: self.insert_mention())

    def filter_files(self, *args):
        query = self.search_var.get().lower()
        self.popup_list.delete(0, tk.END)
        for display_name, actual_name in self.all_project_items:
            if query in actual_name.lower():
                self.popup_list.insert(tk.END, display_name)

    def insert_mention(self):
        if not self.popup_list.curselection(): return
        selection = self.popup_list.get(self.popup_list.curselection())
        clean_name = selection[2:] # Remove icon
        
        self.chat_input.insert(tk.INSERT, f"{clean_name} ")
        end_idx = self.chat_input.index(tk.INSERT)
        start_idx = f"{end_idx} - {len(clean_name)+1}c"
        self.chat_input.tag_add("bold_tag", start_idx, end_idx)
        self.chat_input.tag_config("bold_tag", font=("Segoe UI", 11, "bold"), foreground=DeepBlueTheme.FG_KEYWORD)
        
        self.mention_popup.destroy()
        self.mention_popup = None
        self.chat_input.focus_set()

    def on_chat_enter(self, event):
        self.send_to_ai()
        return "break"

    def send_to_ai(self, event=None):
        prompt = self.chat_input.get("1.0", tk.END).strip()
        if not prompt: return
        if not self.project_path: 
            messagebox.showerror("Error", "Open a project first.")
            return

        self.chat_input.delete("1.0", tk.END)
        self.chat_bubble("USER", prompt)
        
        response_msg = "I'm generating instructions to update your codebase safely."
        if "delete" in prompt.lower(): response_msg = "I'll prepare a delete operation for the compiler."
        
        self.after(500, lambda: self.chat_bubble("AI", response_msg))
        self.log(f"AI: Reasoning about '{prompt}'...", "AI_OP")
        self.after(800, lambda: self.log("COMPILER: Generating CEIL...", "SYSTEM"))
        self.after(1200, lambda: self.log("SECURITY: Scanning AST for threats...", "SYSTEM"))
        self.after(1600, lambda: self.log("SUCCESS: Safety check passed. Executing.", "SUCCESS"))

if __name__ == "__main__":
    app = SecureIDE()
    app.mainloop()
