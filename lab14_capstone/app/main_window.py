import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Menu
import os
import sys
import shutil

# Ensure imports work regardless of run location
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.styles import DeepBlueTheme
from app.ui.editor import CodeEditor
from app.core.security.database import SecurityDB
from app.core.settings import SettingsHandler
from app.core.ai_engine.ai_engine import CeilAIEngine
from app.core.compiler.lexer import CeilLexer
from app.core.compiler.parser import CeilParser
from app.core.security.security import SecurityEngine
from app.core.executor.executor import CeilExecutor
from app.core.chat_manager import ChatManager
import threading
import time
import subprocess
import queue

class SecureIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Marvel Code")
        self.geometry("1400x900")
        self.configure(bg=DeepBlueTheme.BG_MAIN)
        
        # Use a dark blue for the window title bar if the OS supports it
        try:
            from ctypes import windll, byref, sizeof, c_int
            if sys.platform == "win32":
                # Convert hex to color code (0x00BBGGRR)
                # BG_MAIN is #0f172a -> R:0f, G:17, B:2a
                # Windows wants 0x002a170f
                COLOR = 0x002a170f 
                HWND = windll.user32.GetParent(self.winfo_id())
                # DWMWA_CAPTION_COLOR = 35 (Windows 11)
                windll.dwmapi.DwmSetWindowAttribute(HWND, 35, byref(c_int(COLOR)), sizeof(c_int))
                # DWMWA_TEXT_COLOR = 36 (Windows 11)
                white = 0x00ffffff
                windll.dwmapi.DwmSetWindowAttribute(HWND, 36, byref(c_int(white)), sizeof(c_int))
        except Exception:
            pass # Fallback for non-supported OS versions
        
        self.project_path = None
        self.current_file = None
        self.mention_popup = None
        self.all_project_items = [] 
        self.recursion_depth = 0
        self.current_user = None
        self.current_user_role = None
        self.pending_instructions = None # Mission 3: Staging Area
        self.terminal_tabs = {} # Store terminal objects
        self.active_terminal_id = None
        self.chat_manager = None
        self.active_chat_id = "default"
        self.is_ai_processing = False
        self.timer_line_index = None
        
        self.db = SecurityDB()
        self.lexer = CeilLexer()
        self.parser = CeilParser()
        self.sec = SecurityEngine(self.project_path or ".")
        self.exe = CeilExecutor(self.project_path or ".")
        self.ai = CeilAIEngine()
        
        self.configure_styles()
        self.create_menu()
        self.setup_layout()
        
        self.editor.bind("<KeyRelease>", self.auto_save)
        
        self.withdraw() # Hide until login
        self.perform_login()
        
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
        self.main_split = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=DeepBlueTheme.BG_SIDEBAR, sashwidth=3, sashrelief="flat")
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
        self.work_split = tk.PanedWindow(self.main_split, orient=tk.HORIZONTAL, bg=DeepBlueTheme.BG_MAIN, sashwidth=3)
        self.main_split.add(self.work_split)

        self.center_frame = tk.Frame(self.work_split, bg=DeepBlueTheme.BG_MAIN)
        self.center_split = tk.PanedWindow(self.center_frame, orient=tk.VERTICAL, bg=DeepBlueTheme.BG_MAIN, sashwidth=3)
        self.center_split.pack(fill=tk.BOTH, expand=True)

        # Editor
        self.editor_container = tk.Frame(self.center_split, bg=DeepBlueTheme.BG_EDITOR)
        self.editor_scroll = ttk.Scrollbar(self.editor_container, orient="vertical")
        self.editor = CodeEditor(self.editor_container, yscrollcommand=self.editor_scroll.set)
        self.editor_scroll.config(command=self.editor.yview)
        self.editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.center_split.add(self.editor_container, height=500)

        # Multi-Terminal Container
        self.term_container = tk.Frame(self.center_split, bg=DeepBlueTheme.BG_TERMINAL)
        
        # Terminal Header with Tabs and + Button
        self.term_header = tk.Frame(self.term_container, bg="#1e293b", height=30)
        self.term_header.pack(fill=tk.X)
        
        self.term_tabs_frame = tk.Frame(self.term_header, bg="#1e293b")
        self.term_tabs_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.btn_add_term = tk.Button(self.term_header, text=" + ", command=self.add_terminal_tab,
                                     bg="#334155", fg="white", bd=0, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_add_term.pack(side=tk.RIGHT, padx=5, pady=2)

        # Content Area for Terminals
        self.term_content = tk.Frame(self.term_container, bg=DeepBlueTheme.BG_TERMINAL)
        self.term_content.pack(fill=tk.BOTH, expand=True)

        self.center_split.add(self.term_container, height=300)

        # Initialize First System Log Terminal
        self.add_terminal_tab(name="SYSTEM LOGS", is_system=True)

        self.work_split.add(self.center_frame, width=700)

        # === RIGHT CHAT ===
        self.chat_frame = tk.Frame(self.work_split, bg=DeepBlueTheme.BG_CHAT)
        
        # Chat Header (Title + Controls)
        self.chat_header_frame = tk.Frame(self.chat_frame, bg=DeepBlueTheme.BG_CHAT)
        self.chat_header_frame.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_chat = tk.Label(self.chat_header_frame, text=" AI ARCHITECT", bg=DeepBlueTheme.BG_CHAT, fg="#94a3b8", font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_chat.pack(side=tk.LEFT)

        # Chat Switcher
        self.chat_selector = ttk.Combobox(self.chat_header_frame, state="readonly", width=15)
        self.chat_selector.pack(side=tk.LEFT, padx=5)
        self.chat_selector.bind("<<ComboboxSelected>>", self.on_chat_selected)

        # Chat Actions
        self.btn_new_chat = tk.Button(self.chat_header_frame, text="+", command=self.create_new_chat,
                                     bg="#334155", fg="white", bd=0, font=("Segoe UI", 9, "bold"), width=2, cursor="hand2")
        self.btn_new_chat.pack(side=tk.RIGHT, padx=2)
        
        self.btn_ren_chat = tk.Button(self.chat_header_frame, text="✎", command=self.rename_current_chat,
                                     bg="#334155", fg="white", bd=0, font=("Segoe UI", 9, "bold"), width=2, cursor="hand2")
        self.btn_ren_chat.pack(side=tk.RIGHT, padx=2)

        # Chat History with Scrollbar
        chat_scroll_frame = tk.Frame(self.chat_frame, bg=DeepBlueTheme.BG_CHAT)
        
        # Chat History Text
        self.chat_history = tk.Text(chat_scroll_frame, bg=DeepBlueTheme.BG_CHAT, fg=DeepBlueTheme.FG_TEXT, 
                                   font=("Segoe UI", 10), state="disabled", wrap="word", relief="flat", padx=10)
        self.chat_history.tag_config("USER", foreground="#38bdf8", justify="right")
        self.chat_history.tag_config("AI", foreground="#e2e8f0", justify="left")
        self.chat_history.tag_config("PLAN", foreground="#a78bfa", justify="left")
        
        # FIX: Ensure scrollbar is correctly linked to the text widget
        self.chat_scroll = ttk.Scrollbar(chat_scroll_frame, orient="vertical", command=self.chat_history.yview)
        self.chat_history.configure(yscrollcommand=self.chat_scroll.set)

        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat Controls
        self.chat_ctrl_frame = tk.Frame(self.chat_frame, bg="#334155")
        
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

        # Mission 3: Dedicated Staging Area for Confirm Button
        # Using a dedicated frame ensures the button doesn't get pushed out of view
        self.staging_frame = tk.Frame(self.chat_frame, bg=DeepBlueTheme.BG_CHAT)
        self.btn_confirm = tk.Button(self.staging_frame, text="CONFIRM & EXECUTE", 
                                    command=self.execute_pending, 
                                    bg="#10b981", fg="white", font=("Segoe UI", 12, "bold"),
                                    relief="flat", cursor="hand2")
        # Note: btn_confirm is NOT packed yet, staging_frame is packed in REFINED PACKING ORDER

        # --- REFINED PACKING ORDER FOR VISIBILITY ---
        self.chat_header_frame.pack(fill=tk.X, padx=5, pady=5) # 1. Top
        self.chat_ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10) # 2. Bottom
        self.staging_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10) # 3. Above Input
        chat_scroll_frame.pack(fill=tk.BOTH, expand=True) # 4. Fill middle

        self.work_split.add(self.chat_frame, width=350)

    # --- MULTI-TERMINAL SYSTEM ---
    def add_terminal_tab(self, name=None, is_system=False):
        term_id = len(self.terminal_tabs)
        if name is None: name = f"PowerShell {term_id}"

        # 1. Create Tab Button
        btn_tab = tk.Button(self.term_tabs_frame, text=name, 
                            command=lambda: self.switch_terminal(term_id),
                            bg="#1e293b", fg="#94a3b8", bd=0, font=("Segoe UI", 9), padx=10)
        btn_tab.pack(side=tk.LEFT, padx=1)

        # 2. Create Terminal Frame (Stacked)
        frame = tk.Frame(self.term_content, bg=DeepBlueTheme.BG_TERMINAL)
        
        # Scrollbar
        scroll = ttk.Scrollbar(frame, orient="vertical")
        
        # Text Widget
        text_widget = tk.Text(frame, bg=DeepBlueTheme.BG_TERMINAL, fg="#cbd5e1", 
                              font=("Consolas", 10), relief="flat", padx=10, pady=5,
                              yscrollcommand=scroll.set, insertbackground="white")
        scroll.config(command=text_widget.yview)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Store Terminal Data
        self.terminal_tabs[term_id] = {
            "btn": btn_tab,
            "frame": frame,
            "text": text_widget,
            "is_system": is_system,
            "process": None,
            "queue": queue.Queue()
        }

        # Configure Tags for System Terminal
        if is_system:
            text_widget.tag_config("SYSTEM", foreground="#38bdf8")
            text_widget.tag_config("AI_OP", foreground="#a78bfa")
            text_widget.tag_config("SUCCESS", foreground="#4ade80")
            text_widget.tag_config("ERROR", foreground="#f44336")
            text_widget.insert(tk.END, "MarvelCode System Log Initialized...\n", "SYSTEM")
            text_widget.config(state="disabled") # System log is read-only
        else:
            # Interactive Shell Logic
            self.start_powershell(term_id)
            text_widget.bind("<Return>", lambda e: self.on_term_enter(e, term_id))

        self.switch_terminal(term_id)

    def switch_terminal(self, term_id):
        # Hide all frames
        for tid, data in self.terminal_tabs.items():
            data['frame'].pack_forget()
            data['btn'].config(bg="#1e293b", fg="#94a3b8") # Inactive style

        # Show active frame
        self.terminal_tabs[term_id]['frame'].pack(fill=tk.BOTH, expand=True)
        self.terminal_tabs[term_id]['btn'].config(bg="#334155", fg="white") # Active style
        self.active_terminal_id = term_id

    def start_powershell(self, term_id):
        """Starts a persistent PowerShell process for the terminal tab."""
        def read_output(pipe, q):
            for line in iter(pipe.readline, ''):
                q.put(line)
            pipe.close()

        # Startupinfo to hide window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            ["powershell", "-NoExit", "-Command", "-"], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1,
            cwd=self.project_path or os.getcwd(),
            startupinfo=startupinfo
        )
        
        self.terminal_tabs[term_id]['process'] = process
        
        # Start reading threads
        threading.Thread(target=read_output, args=(process.stdout, self.terminal_tabs[term_id]['queue']), daemon=True).start()
        threading.Thread(target=read_output, args=(process.stderr, self.terminal_tabs[term_id]['queue']), daemon=True).start()

        # Initial Prompt
        self.terminal_tabs[term_id]['text'].insert(tk.END, f"PS {self.project_path or os.getcwd()}> ")
        self.terminal_tabs[term_id]['text'].see(tk.END)

        self.update_terminal_output(term_id)

    def update_terminal_output(self, term_id):
        """Polls the queue and updates the UI."""
        if term_id not in self.terminal_tabs: return
        
        try:
            while True:
                line = self.terminal_tabs[term_id]['queue'].get_nowait()
                self.terminal_tabs[term_id]['text'].insert(tk.END, line)
                self.terminal_tabs[term_id]['text'].see(tk.END)
        except queue.Empty:
            pass
        
        self.after(50, lambda: self.update_terminal_output(term_id))

    def on_term_enter(self, event, term_id):
        """Handles command input in the interactive terminal."""
        txt = self.terminal_tabs[term_id]['text']
        # Get last line
        content = txt.get("1.0", tk.END).strip()
        lines = content.split("\n")
        
        # Simple extraction: assumes the last line is the command
        # Better: find the last occurrence of "> "
        last_line = lines[-1]
        if "> " in last_line:
            command = last_line.split("> ")[-1]
        else:
            command = last_line
            
        if not command: return "break"
        
        # Send to process
        if self.terminal_tabs[term_id]['process']:
            try:
                # Chain a Write-Host to simulate prompt reappearance
                full_cmd = f"{command}; Write-Host 'PS ' $PWD '> '"
                self.terminal_tabs[term_id]['process'].stdin.write(full_cmd + "\n")
                self.terminal_tabs[term_id]['process'].stdin.flush()
                txt.insert(tk.END, "\n") # Visual newline
            except Exception as e:
                txt.insert(tk.END, f"\nError: {e}\n")
        
        return "break" # Prevent default newline insertion

    # --- HELPERS ---
    def perform_login(self):
        login_win = tk.Toplevel(self)
        login_win.title("MarvelCode - Mission Control Login")
        login_win.state('zoomed') # Mission 1: Professional Maximized State
        login_win.configure(bg=DeepBlueTheme.BG_MAIN)
        
        # Centering container
        center_frame = tk.Frame(login_win, bg=DeepBlueTheme.BG_MAIN)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(center_frame, text="MARVELCODE LOGIN", 
                 bg=DeepBlueTheme.BG_MAIN, fg=DeepBlueTheme.FG_KEYWORD, 
                 font=("Segoe UI", 24, "bold")).pack(pady=30)

        tk.Label(center_frame, text="Username", bg=DeepBlueTheme.BG_MAIN, fg="#94a3b8", font=("Segoe UI", 14)).pack(pady=(10, 5))
        user_ent = tk.Entry(center_frame, font=("Segoe UI", 14), width=30, bg="#334155", fg="white", insertbackground="white", relief="flat")
        user_ent.pack(ipady=10)
        
        tk.Label(center_frame, text="Password", bg=DeepBlueTheme.BG_MAIN, fg="#94a3b8", font=("Segoe UI", 14)).pack(pady=(20, 5))
        pass_ent = tk.Entry(center_frame, show="*", font=("Segoe UI", 14), width=30, bg="#334155", fg="white", insertbackground="white", relief="flat")
        pass_ent.pack(ipady=10)
        
        def attempt_login(event=None):
            u, p = user_ent.get(), pass_ent.get()
            success, role = self.db.authenticate(u, p)
            if success:
                self.current_user = u
                self.current_user_role = role
                SettingsHandler.set("current_user", u) # Mission 1: Save State
                
                self.deiconify()
                login_win.destroy()
                self.log(f"Mission Control: {u} authenticated as {role}", "SUCCESS")
                
                # Mission 1: Auto-Mount
                last_path = SettingsHandler.get("last_project_path")
                if last_path and os.path.exists(last_path):
                    self.auto_load_project(last_path)
            else:
                messagebox.showerror("Security Alert", "Invalid Credentials. Access Denied.")

        btn_login = tk.Button(center_frame, text="AUTHORIZE ACCESS", command=attempt_login, 
                              bg=DeepBlueTheme.ACCENT, fg="white", font=("Segoe UI", 14, "bold"), 
                              width=25, relief="flat", cursor="hand2")
        btn_login.pack(pady=40, ipady=10)
        
        login_win.bind("<Return>", attempt_login)
        login_win.protocol("WM_DELETE_WINDOW", self.quit)

    def auto_load_project(self, path):
        self.project_path = path
        # Initialize Chat Manager
        self.chat_manager = ChatManager(path)
        self.refresh_chat_selector()
        
        # Refresh components with new path
        self.ai = CeilAIEngine()
        self.sec = SecurityEngine(path)
        self.exe = CeilExecutor(path)
        self.populate_file_tree()
        self.log(f"Auto-Mounting Workspace: {path}", "SUCCESS")
        self.file_tree.heading("#0", text=f"PROJECT: {os.path.basename(path)}")

    def log(self, message, tag="SYSTEM"):
        if 0 not in self.terminal_tabs: return
        
        timestamp = time.strftime("%H:%M:%S")
        text_widget = self.terminal_tabs[0]['text']
        text_widget.config(state="normal")
        text_widget.insert(tk.END, f"[{timestamp}] >> {message}\n", tag)
        text_widget.config(state="disabled")
        text_widget.see(tk.END)

    def loop_timer(self, start_time, mode, start_ts):
        if not self.is_ai_processing: return
        elapsed = time.time() - start_time
        self.update_timer_line(mode, elapsed, start_ts)
        self.after(100, lambda: self.loop_timer(start_time, mode, start_ts))

    def update_timer_line(self, mode, elapsed, start_ts, create=False, done=False):
        if 0 not in self.terminal_tabs: return
        txt = self.terminal_tabs[0]['text']
        txt.config(state="normal")
        
        msg = f"[{start_ts}] >> --- Processing {mode.upper()} Request ({elapsed:.1f}s) ---"
        if done: msg = f"[{start_ts}] >> --- Processing {mode.upper()} Request (COMPLETED in {elapsed:.1f}s) ---"

        if create:
            txt.insert(tk.END, msg + "\n", "SYSTEM")
            self.timer_line_index = txt.index("end-2c linestart")
        elif self.timer_line_index:
            # Replace the specific line
            line_start = self.timer_line_index
            line_end = txt.index(f"{line_start} lineend")
            txt.delete(line_start, line_end)
            txt.insert(line_start, msg)
            
        txt.config(state="disabled")
        txt.see(tk.END)

    def chat_bubble(self, sender, message):
        self.chat_history.config(state="normal")
        if sender == "PLAN":
            self.chat_history.tag_config("PLAN", foreground="#a78bfa", justify="left")
        self.chat_history.insert(tk.END, f"[{sender}]\n{message}\n\n", sender)
        self.chat_history.config(state="disabled")
        self.chat_history.see(tk.END)
        
        # Save to Chat Manager
        if self.chat_manager:
            self.chat_manager.add_message(self.active_chat_id, sender, message)

    def refresh_chat_selector(self):
        if not self.chat_manager: return
        chats = self.chat_manager.chats["chats"]
        chat_names = [f"{v['name']} ({k})" for k, v in chats.items()]
        self.chat_selector['values'] = chat_names
        
        # Select active chat
        active_id = self.chat_manager.chats["active_chat_id"]
        active_name = chats.get(active_id, {}).get("name", "Unknown")
        self.chat_selector.set(f"{active_name} ({active_id})")
        self.active_chat_id = active_id
        
        self.load_chat_history(active_id)

    def load_chat_history(self, chat_id):
        self.chat_history.config(state="normal")
        self.chat_history.delete("1.0", tk.END)
        
        history = self.chat_manager.get_history(chat_id)
        for msg in history:
            sender = msg['sender']
            message = msg['message']
            self.chat_history.insert(tk.END, f"[{sender}]\n{message}\n\n", sender)
            
        self.chat_history.config(state="disabled")
        self.chat_history.see(tk.END)

    def on_chat_selected(self, event):
        selection = self.chat_selector.get()
        # Extract ID from "Name (ID)"
        chat_id = selection.split("(")[-1].strip(")")
        self.active_chat_id = chat_id
        self.chat_manager.chats["active_chat_id"] = chat_id
        self.chat_manager.save_chats()
        self.load_chat_history(chat_id)

    def create_new_chat(self):
        name = simpledialog.askstring("New Chat", "Enter chat name:")
        if name:
            new_id = f"chat_{int(time.time())}"
            self.chat_manager.add_chat(new_id, name)
            self.chat_manager.chats["active_chat_id"] = new_id
            self.refresh_chat_selector()

    def rename_current_chat(self):
        new_name = simpledialog.askstring("Rename Chat", "Enter new name:")
        if new_name:
            self.chat_manager.rename_chat(self.active_chat_id, new_name)
            self.refresh_chat_selector()

    def auto_save(self, event=None):
        if self.current_file and os.path.exists(self.current_file):
            content = self.editor.get("1.0", tk.END).strip()
            with open(self.current_file, "w") as f: f.write(content)

    # --- FILE OPS ---
    def open_project(self):
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            SettingsHandler.set("last_project_path", path) # Mission 1: Persist Path
            self.auto_load_project(path)

    def process(self, mode, prompt):
        start_time = time.time()
        start_ts = time.strftime("%H:%M:%S")
        self.is_ai_processing = True
        
        # Initial Timer Log (Thread-safe creation)
        self.after(0, lambda: self.update_timer_line(mode, 0.0, start_ts, create=True))
        # Start Timer Loop
        self.after(100, lambda: self.loop_timer(start_time, mode, start_ts))

        try:
            self.btn_confirm.after(0, self.btn_confirm.pack_forget) # Thread-safe UI update
            
            # 1. AI Layer (Blocking call moved to thread)
            history = self.chat_manager.get_history(self.active_chat_id)
            
            # Mission 3: Robust Header Normalization
            # Sometimes AI adds markdown or brackets to headers. We normalize them for easier splitting.
            def normalize_headers(text):
                text = text.replace("[PLAN]", "PLAN").replace("### PLAN", "PLAN")
                text = text.replace("[COMMANDS]", "COMMANDS").replace("### COMMANDS", "COMMANDS")
                text = text.replace("[CHAT]", "CHAT").replace("### CHAT", "CHAT")
                return text

            # Helper for thread-safe logging from within AI engine
            def ai_log(msg, level="INFO"):
                self.after(0, lambda: self.log(msg, level))
            
            if mode == "figma":
                self.after(0, lambda: self.log(f"Transpiling Figma Data...", "AI_OP"))
                raw_response = self.ai.figma_to_ceil(prompt)
            else:
                raw_response = self.ai.generate_instructions(prompt, self.project_path, history=history, log_callback=ai_log)
            
            raw_response = normalize_headers(raw_response)
            self.is_ai_processing = False # Stop Timer Loop
            elapsed = time.time() - start_time
            
            # Finalize Timer Line
            self.after(0, lambda: self.update_timer_line(mode, elapsed, start_ts, create=False, done=True))
            self.after(0, lambda: self.log(f"AI Process Completed in {elapsed:.2f} seconds", "SUCCESS"))
            
            if "ERROR" in raw_response:
                self.after(0, lambda: self.log(raw_response, "ERROR"))
                self.after(0, lambda: self.chat_bubble("AI", f"⚠️ {raw_response}"))
                return

            # Mission 3: Logical Intent Differentiation & Parsing
            chat_content = ""
            plan_content = ""
            ceil_content = ""

            # Robust Parsing
            # Mission 3: Use the last COMMANDS section in case the AI mentioned it earlier in text
            parts = raw_response.split("COMMANDS")
            non_command_part = parts[0]
            if len(parts) > 1:
                # Take the last part as the command block
                ceil_content = self.ai.clean_response(parts[-1].strip())

            plan_parts = non_command_part.split("PLAN")
            chat_part = plan_parts[0]
            if len(plan_parts) > 1:
                plan_content = plan_parts[1].strip()

            if "CHAT" in chat_part:
                chat_content = chat_part.split("CHAT")[1].strip()
            else:
                chat_content = chat_part.strip()


            # Update Chat UI (Thread-safe)
            if chat_content:
                # Remove artifacts like ": " if they remain
                if chat_content.startswith(":"): chat_content = chat_content[1:].strip()
                self.after(0, lambda: self.chat_bubble("AI", chat_content))
            
            if plan_content:
                # Remove artifacts like ": " if they remain
                if plan_content.startswith(":"): plan_content = plan_content[1:].strip()
                self.after(0, lambda: self.chat_bubble("PLAN", f"📋 PROPOSED PLAN:\n{plan_content}"))
                
                # Mission 3: Rigid Triggering
                # If the AI proposed a plan, we ALWAYS show the button, even if commands aren't parsed yet.
                self.after(0, lambda: self.btn_confirm.pack(fill=tk.X, pady=(0, 10)))
                self.after(0, lambda: self.log("AI Plan Proposed. Execution Button Enabled.", "SYSTEM"))
            
            if ceil_content:
                self.pending_instructions = ceil_content
                self.after(0, lambda: self.log("AI Instructions Parsed Successfully.", "SUCCESS"))
                # Only show the confirmation prompt if there are actual commands
                self.after(0, lambda: self.chat_bubble("AI", "I have prepared the changes. Please review the plan above and click 'CONFIRM & EXECUTE' when ready."))
            
            # Fallback only if absolutely nothing was parsed and it wasn't empty
            elif not chat_content and not plan_content and raw_response.strip():
                 self.after(0, lambda: self.chat_bubble("AI", raw_response))

        except Exception as e: 
            self.after(0, lambda: self.log(f"Pipeline Fail: {e}"))
            self.after(0, lambda: self.chat_bubble("AI", f"Critical Error: {e}"))

    def execute_pending(self):
        """Mission 3: The Execution Hook (Async)."""
        self.btn_confirm.pack_forget()
        
        if not self.pending_instructions:
            self.log("No CEIL commands found in the AI response. Please ask the AI to provide the COMMANDS section.", "ERROR")
            self.chat_bubble("AI", "⚠️ I proposed a plan but didn't provide the execution commands. Please ask me to 'Provide the CEIL commands for this plan' if you want to proceed.")
            return
        
        ceil = self.pending_instructions
        self.pending_instructions = None
        
        # Run execution in background thread
        threading.Thread(target=self._run_execution_thread, args=(ceil,), daemon=True).start()

    def _run_execution_thread(self, ceil):
        try:
            self.after(0, lambda: self.log("Executing Authorized Instructions...", "SYSTEM"))
            
            # 2. Compiler
            tokens = self.lexer.tokenize(ceil)
            ast = self.parser.set_tokens(tokens).parse()
            
            # 3. Security
            audited = self.sec.audit_ast(ast, self.current_user_role)
            
            # 4. Executor
            # Handle FETCH_FIGMA specially before generic execution
            for cmd in audited:
                if cmd['type'] == 'FETCH_FIGMA':
                    url = cmd['url']
                    self.after(0, lambda: self.log(f"Fetching Design from Figma: {url}", "AI_OP"))
                    figma_data = self.ai.fetch_figma_data(url)
                    if "error" in figma_data:
                        self.after(0, lambda: self.log(f"Figma Error: {figma_data['error']}", "ERROR"))
                    else:
                        self.after(0, lambda: self.log("Figma Data Retrieved. Processing with AI...", "SUCCESS"))
                        # Recurse with figma data to generate code
                        threading.Thread(target=self.process, args=("figma", str(figma_data)), daemon=True).start()
                    return # Exit after triggering figma process
            
            res_list = self.exe.execute(audited)
            
            # 5. Receipt (Thread-safe updates)
            for r in res_list: 
                self.after(0, lambda msg=r: self.log(msg))
            
            success_count = len([r for r in res_list if "CREATED" in r or "PATCHED" in r or "DELETED" in r])
            self.after(0, lambda: self.chat_bubble("AI", f"✅ Mission successful. {success_count} operations completed. See logs for details."))
            
            # Self-healing if needed
            errors = [r for r in res_list if "ERROR" in r or "RUNTIME ERROR" in r]
            if errors and self.recursion_depth < 3:
                self.recursion_depth += 1
                self.after(0, lambda: self.log(f"⚠️ Auto-Fixing: {len(errors)} errors found.", "AUTO-FIX"))
                threading.Thread(target=self.process, args=("text", f"The execution failed with these errors: {errors}. Fix them."), daemon=True).start()
            else:
                self.recursion_depth = 0
                self.after(100, lambda: self.after(0, self.populate_file_tree))

        except Exception as e:
            self.log(f"Execution Failed: {e}", "ERROR")
            self.chat_bubble("AI", f"❌ Execution Failed: {e}")

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

    def send_to_ai(self):
        prompt = self.chat_input.get("1.0", tk.END).strip()
        if not prompt or not self.project_path: return
        
        self.chat_input.delete("1.0", tk.END)
        self.chat_bubble("USER", prompt)
        
        # Start async processing
        threading.Thread(target=self.process, args=("text", prompt), daemon=True).start()

if __name__ == "__main__":
    app = SecureIDE()
    app.mainloop()
