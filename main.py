import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from datetime import datetime
import sys
import os
import re
import ast 
import time

# --- Constants ---
APP_TITLE = "Ice Hub - Joiner"
ACCENT_COLOR = "#00d4ff"  # Light Blue
SUCCESS_COLOR = "#00ff88"  # Green
ERROR_COLOR = "#ff4444"  # Red
BG_PRIMARY = "#16161e"
BG_SECONDARY = "#1e1e2e"
BG_TERTIARY = "#2a2a3e"
TEXT_LIGHT = "#ffffff"
TEXT_MUTED = "#888888"

# Change working directory to script location
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Create logs folder if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create default config if it doesn't exist
CONFIG_PATH = 'config.py'
if not os.path.exists(CONFIG_PATH):
    default_config = '''DISCORD_TOKEN = ""

MONEY_THRESHOLD = (1.0, 1999.0)
PLAYER_TRESHOLD = 8
IGNORE_UNKNOWN = True
IGNORE_LIST = ["La Cucaracha"]
FILTER_BY_NAME = False, ["Graipuss Medussi", "La Grande Combinasion"]
BYPASS_10M = True
READ_CHANNELS = ['notasnek_1m-10m', "10m_plus"]

WEBSOCKET_PORT = 51948
DISCORD_WS_URL = "wss://gateway.discord.gg/?encoding=json&v=9"

CHILLI_HUB_CHANNELS_ID = {
    "10m_plus": ["1401775181025775738"],
}
'''
    with open(CONFIG_PATH, 'w') as f:
        f.write(default_config)

# Global variables for control
stop_flag = False
roblox_thread = None
listener_thread = None
ui_instance = None


def get_timestamp():
    return datetime.now().strftime("[%H:%M:%S]")


class ModernButton(tk.Canvas):
    """Custom modern button with hover effects"""
    def __init__(self, parent, text, command, bg_color, hover_color, width=260, height=60, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent['bg'], **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text = text
        self.is_enabled = True
        self.width = width
        self.height = height
        
        self.configure(bg=bg_color)
        self.create_text(
            width//2, height//2,
            text=text,
            fill=TEXT_LIGHT,
            font=("Segoe UI", 14, "bold"),
            tags="text"
        )
        
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        if self.is_enabled:
            self.configure(bg=self.hover_color)
    
    def on_leave(self, e):
        if self.is_enabled:
            self.configure(bg=self.bg_color)
    
    def on_click(self, e):
        if self.is_enabled and self.command:
            self.command()
    
    def set_state(self, enabled):
        self.is_enabled = enabled
        if not enabled:
            self.configure(bg="#2a2a2a")
            self.itemconfig("text", fill="#666666")
        else:
            self.configure(bg=self.bg_color)
            self.itemconfig("text", fill=TEXT_LIGHT)


class IceHubJoinerUI:
    def __init__(self, root):
        global ui_instance
        ui_instance = self
        
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_PRIMARY)
        self.root.resizable(False, False)
        
        self.is_running = False
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # --- UI Initialization ---
        self._setup_top_bar(root)
        
        # Main content
        content = tk.Frame(root, bg=BG_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Script buttons frame (removed per request, kept for structure simplicity)
        script_buttons_frame = tk.Frame(content, bg=BG_PRIMARY)
        script_buttons_frame.pack_forget() # Hide this frame
        
        # Panels container with tabs
        panels_container = tk.Frame(content, bg=BG_PRIMARY)
        panels_container.pack(fill=tk.BOTH, expand=True)
        
        self._setup_notebook(panels_container)
        
        # Setup redirect
        self.setup_output_redirect()
        
        # Initial logs
        self.log_message("System initialized successfully", "success")
        self.log_message(f"{APP_TITLE} - Ready", "info")
        self.log_message("Awaiting start command...", "info")
        
        # Import
        global roblox_main
        try:
            from src.roblox import roblox_main
        except ImportError:
            self.log_message("Could not import 'roblox_main' from src.roblox. Check your file structure.", "error")
            def placeholder_roblox_main():
                print(f"{get_timestamp()} [ERROR] 'roblox_main' placeholder is running. Cannot start joiner script.")
            roblox_main = placeholder_roblox_main
            
    def _setup_top_bar(self, root):
        # Top bar
        top_bar = tk.Frame(root, bg=BG_SECONDARY, height=100)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Logo
        logo_frame = tk.Frame(top_bar, bg=BG_SECONDARY)
        logo_frame.pack(side=tk.LEFT, padx=20, pady=20)
        
        logo_canvas = tk.Canvas(logo_frame, width=60, height=60, bg=BG_SECONDARY, highlightthickness=0)
        logo_canvas.pack()
        logo_canvas.create_oval(5, 5, 55, 55, fill=ACCENT_COLOR, outline="")
        logo_canvas.create_text(30, 30, text="IH", fill="#000000", font=("Arial", 18, "bold"))
        
        # Title
        title_frame = tk.Frame(top_bar, bg=BG_SECONDARY)
        title_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            title_frame,
            text="ICE HUB",
            font=("Arial", 28, "bold"),
            fg=TEXT_LIGHT,
            bg=BG_SECONDARY
        ).pack(anchor=tk.W)
        
        tk.Label(
            title_frame,
            text="Advanced Auto-Join System",
            font=("Arial", 11),
            fg=ACCENT_COLOR,
            bg=BG_SECONDARY
        ).pack(anchor=tk.W)
        
        # Status indicator
        status_frame = tk.Frame(top_bar, bg=BG_TERTIARY)
        status_frame.pack(side=tk.RIGHT, padx=20, pady=20, ipadx=10, ipady=5)
        
        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=("Arial", 16),
            fg=ERROR_COLOR,
            bg=BG_TERTIARY
        )
        self.status_dot.pack(side=tk.LEFT, padx=(10, 5))
        
        self.status_label = tk.Label(
            status_frame,
            text="OFFLINE",
            font=("Arial", 12, "bold"),
            fg=ERROR_COLOR,
            bg=BG_TERTIARY
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 10))
        
    def _setup_notebook(self, parent):
        # Create notebook for tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=BG_PRIMARY, borderwidth=0)
        style.configure('TNotebook.Tab', background=BG_TERTIARY, foreground=TEXT_MUTED, padding=[20, 10], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', BG_SECONDARY)], foreground=[('selected', ACCENT_COLOR)])
        
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tabs
        main_tab = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(main_tab, text="Main")
        
        settings_tab = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(settings_tab, text="Settings")
        
        token_tab = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(token_tab, text="Token")
        
        # Content Setup
        self._setup_main_tab(main_tab)
        self._setup_settings_tab(settings_tab)
        self._setup_token_tab(token_tab)

    def _setup_main_tab(self, main_tab):
        main_content = tk.Frame(main_tab, bg=BG_PRIMARY)
        main_content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (Control)
        left_panel = tk.Frame(main_content, bg=BG_SECONDARY, width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_panel.pack_propagate(False)
        
        # Control panel header
        tk.Label(left_panel, text="CONTROL PANEL", font=("Segoe UI", 14, "bold"), fg=ACCENT_COLOR, bg=BG_SECONDARY).pack(pady=(20, 30), padx=20, anchor=tk.W)
        
        # START button
        self.start_btn = ModernButton(left_panel, "START", self.start_bot, SUCCESS_COLOR, "#00ff9d", width=260, height=60)
        self.start_btn.pack(padx=20, pady=10)
        
        # STOP button
        self.stop_btn = ModernButton(left_panel, "STOP", self.stop_bot, ERROR_COLOR, "#ff6666", width=260, height=60)
        self.stop_btn.pack(padx=20, pady=10)
        self.stop_btn.set_state(False)
        
        # Stats section
        stats_frame = tk.Frame(left_panel, bg=BG_TERTIARY)
        stats_frame.pack(fill=tk.X, padx=20, pady=30, ipady=5)
        
        tk.Label(stats_frame, text="STATISTICS", font=("Segoe UI", 11, "bold"), fg=ACCENT_COLOR, bg=BG_TERTIARY).pack(pady=(15, 10), padx=15, anchor=tk.W)
        
        # WebSocket status
        ws_frame = tk.Frame(stats_frame, bg=BG_TERTIARY)
        ws_frame.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(ws_frame, text="WebSocket:", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_TERTIARY).pack(side=tk.LEFT)
        self.ws_status = tk.Label(ws_frame, text="DISCONNECTED", font=("Segoe UI", 10, "bold"), fg=ERROR_COLOR, bg=BG_TERTIARY)
        self.ws_status.pack(side=tk.RIGHT)
        
        # Discord status
        dc_frame = tk.Frame(stats_frame, bg=BG_TERTIARY)
        dc_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        tk.Label(dc_frame, text="Discord:", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_TERTIARY).pack(side=tk.LEFT)
        self.dc_status = tk.Label(dc_frame, text="DISCONNECTED", font=("Segoe UI", 10, "bold"), fg=ERROR_COLOR, bg=BG_TERTIARY)
        self.dc_status.pack(side=tk.RIGHT)
        
        # Right panel (Logs)
        right_panel = tk.Frame(main_content, bg=BG_SECONDARY)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Logs header
        logs_header = tk.Frame(right_panel, bg=BG_TERTIARY)
        logs_header.pack(fill=tk.X)
        tk.Label(logs_header, text="LIVE ACTIVITY FEED", font=("Segoe UI", 13, "bold"), fg=ACCENT_COLOR, bg=BG_TERTIARY).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Clear button
        clear_btn = tk.Button(logs_header, text="Clear", font=("Segoe UI", 10, "bold"), fg=TEXT_LIGHT, bg=ERROR_COLOR, activebackground="#ff6666", border=0, relief=tk.FLAT, cursor="hand2", command=self.clear_logs, padx=15, pady=8)
        clear_btn.pack(side=tk.RIGHT, padx=20)
        
        # Logs text
        logs_container = tk.Frame(right_panel, bg="#0f0f1a")
        logs_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.logs_text = scrolledtext.ScrolledText(logs_container, font=("Consolas", 10), fg=SUCCESS_COLOR, bg="#0f0f1a", insertbackground=ACCENT_COLOR, border=0, state=tk.DISABLED, wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.logs_text.tag_config("info", foreground=ACCENT_COLOR)
        self.logs_text.tag_config("warning", foreground="#ffaa00")
        self.logs_text.tag_config("error", foreground=ERROR_COLOR)
        self.logs_text.tag_config("success", foreground=SUCCESS_COLOR)

    def _setup_token_tab(self, token_tab):
        token_content = tk.Frame(token_tab, bg=BG_PRIMARY)
        token_content.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        token_frame = tk.Frame(token_content, bg=BG_SECONDARY)
        token_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(token_frame, text="Discord Token", font=("Segoe UI", 14, "bold"), fg=ACCENT_COLOR, bg=BG_SECONDARY).pack(pady=(20, 10), padx=20, anchor=tk.W)
        tk.Label(token_frame, text="Enter your Discord bot token below:", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_SECONDARY).pack(pady=(0, 10), padx=20, anchor=tk.W)
        
        token_input_frame = tk.Frame(token_frame, bg=BG_SECONDARY)
        token_input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.token_entry = tk.Entry(token_input_frame, font=("Consolas", 11), bg="#0f0f1a", fg=SUCCESS_COLOR, insertbackground=ACCENT_COLOR, border=0, relief=tk.FLAT, width=50)
        self.token_entry.pack(fill=tk.X, ipady=10, padx=5)
        
        try:
            import config
            # Ensure config is reloaded before reading
            import importlib
            importlib.reload(config)
            if hasattr(config, 'DISCORD_TOKEN'):
                self.token_entry.insert(0, config.DISCORD_TOKEN.strip('"')) # Clean up potential quotes
        except:
            pass
        
        save_btn = tk.Button(token_frame, text="Save Token", font=("Segoe UI", 12, "bold"), fg=TEXT_LIGHT, bg=SUCCESS_COLOR, activebackground="#00ff9d", border=0, relief=tk.FLAT, cursor="hand2", command=self.save_token, width=15, height=2)
        save_btn.pack(pady=20)
        
        self.token_status = tk.Label(token_frame, text="", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_SECONDARY)
        self.token_status.pack(pady=(0, 20))

    def _setup_settings_tab(self, settings_tab):
        # Frame for scrollable settings
        settings_canvas = tk.Canvas(settings_tab, bg=BG_PRIMARY, highlightthickness=0)
        settings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        settings_scrollbar = ttk.Scrollbar(settings_tab, orient="vertical", command=settings_canvas.yview)
        settings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        # Bind the frame to the canvas scroll region
        def on_frame_configure(event):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))

        settings_frame = tk.Frame(settings_canvas, bg=BG_PRIMARY)
        settings_canvas.create_window((0, 0), window=settings_frame, anchor="nw", width=1050)
        
        # Bind the internal frame size changes to update scroll region
        settings_frame.bind("<Configure>", on_frame_configure)
        
        tk.Label(settings_frame, text="JOINER SETTINGS", font=("Segoe UI", 18, "bold"), fg=ACCENT_COLOR, bg=BG_PRIMARY).pack(pady=(30, 10), padx=40, anchor=tk.W)
        tk.Label(settings_frame, text="Changes require a bot restart.", font=("Segoe UI", 10), fg="#ffaa00", bg=BG_PRIMARY).pack(pady=(0, 20), padx=40, anchor=tk.W)

        # Container for all options
        options_container = tk.Frame(settings_frame, bg=BG_SECONDARY)
        options_container.pack(fill=tk.X, padx=40, pady=10, ipady=10)

        # Dictionary to hold control variables for easy access
        self.settings_vars = {}
        
        # Load initial values
        self.settings = self._load_current_settings()
        
        # Helper function for input fields (simplified for clarity, as grid/pack handling was complex)
        def create_setting_row(parent, label_text, key, type='entry'):
            row_frame = tk.Frame(parent, bg=BG_SECONDARY)
            row_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Label(row_frame, text=label_text, font=("Segoe UI", 11), fg=TEXT_LIGHT, bg=BG_SECONDARY, width=30, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
            
            if type == 'entry':
                var = tk.StringVar(value=str(self.settings.get(key, '')))
                entry = tk.Entry(row_frame, textvariable=var, font=("Consolas", 11), bg="#0f0f1a", fg=SUCCESS_COLOR, insertbackground=ACCENT_COLOR, border=0, relief=tk.FLAT, width=30)
                entry.pack(side=tk.LEFT, ipady=5, fill=tk.X, expand=True)
                self.settings_vars[key] = var
                return entry
            
            elif type == 'checkbox':
                var = tk.BooleanVar(value=self.settings.get(key, False))
                # Checkbutton without label text and packed on its own
                checkbox = tk.Checkbutton(row_frame, text="", variable=var, bg=BG_SECONDARY, activebackground=BG_SECONDARY, fg=TEXT_LIGHT, selectcolor="#0f0f1a", width=1, height=1)
                checkbox.pack(side=tk.LEFT, padx=0)
                self.settings_vars[key] = var
                return checkbox
        
        def create_list_setting(parent, label_text, key):
            list_frame = tk.Frame(parent, bg=BG_SECONDARY)
            list_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Label(list_frame, text=label_text, font=("Segoe UI", 11), fg=TEXT_LIGHT, bg=BG_SECONDARY, width=30, anchor=tk.W).pack(side=tk.LEFT, anchor=tk.N, padx=(0, 10))
            
            initial_list = self.settings.get(key, [])
            if key == 'FILTER_BY_NAME_LIST':
                 # The 'FILTER_BY_NAME' key in self.settings contains the (bool, list) tuple
                 initial_list = self.settings.get('FILTER_BY_NAME', (False, []))[1] 
                
            initial_text = ", ".join(map(str, initial_list)) # Ensure all items are strings for join
            text_widget = scrolledtext.ScrolledText(list_frame, width=35, height=3, font=("Consolas", 10), bg="#0f0f1a", fg=SUCCESS_COLOR, insertbackground=ACCENT_COLOR, border=0, wrap=tk.WORD)
            text_widget.insert(tk.END, initial_text)
            text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            self.settings_vars[key] = text_widget
            return text_widget

        # 1. MONEY_THRESHOLD
        money_frame = tk.Frame(options_container, bg=BG_SECONDARY)
        money_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(money_frame, text="MONEY_THRESHOLD (Min, Max):", font=("Segoe UI", 11), fg=TEXT_LIGHT, bg=BG_SECONDARY, width=30, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
        
        # Initial values from self.settings
        min_val_init = self.settings.get('MONEY_THRESHOLD', (1.0, 1999.0))[0]
        max_val_init = self.settings.get('MONEY_THRESHOLD', (1.0, 1999.0))[1]

        # Min
        min_money = tk.StringVar(value=str(min_val_init))
        tk.Entry(money_frame, textvariable=min_money, font=("Consolas", 11), bg="#0f0f1a", fg=SUCCESS_COLOR, insertbackground=ACCENT_COLOR, border=0, relief=tk.FLAT, width=15).pack(side=tk.LEFT, ipady=5)
        tk.Label(money_frame, text=" to ", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=BG_SECONDARY).pack(side=tk.LEFT, padx=10)
        # Max
        max_money = tk.StringVar(value=str(max_val_init))
        tk.Entry(money_frame, textvariable=max_money, font=("Consolas", 11), bg="#0f0f1a", fg=SUCCESS_COLOR, insertbackground=ACCENT_COLOR, border=0, relief=tk.FLAT, width=15).pack(side=tk.LEFT, ipady=5)
        
        self.settings_vars['MONEY_THRESHOLD_MIN'] = min_money
        self.settings_vars['MONEY_THRESHOLD_MAX'] = max_money

        # 2. PLAYER_TRESHOLD
        create_setting_row(options_container, "PLAYER_TRESHOLD:", 'PLAYER_TRESHOLD', type='entry')

        # 3. IGNORE_UNKNOWN
        create_setting_row(options_container, "IGNORE_UNKNOWN (bool):", 'IGNORE_UNKNOWN', type='checkbox')
        
        # 4. IGNORE_LIST
        create_list_setting(options_container, "IGNORE_LIST (Names):", 'IGNORE_LIST')

        # 5. FILTER_BY_NAME Boolean
        filter_name_bool_frame = tk.Frame(options_container, bg=BG_SECONDARY)
        filter_name_bool_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(filter_name_bool_frame, text="FILTER_BY_NAME Enabled:", font=("Segoe UI", 11), fg=TEXT_LIGHT, bg=BG_SECONDARY, width=30, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))

        # Initial value: first element of the tuple
        filter_names_bool = tk.BooleanVar(value=self.settings.get('FILTER_BY_NAME', (False, []))[0])
        tk.Checkbutton(filter_name_bool_frame, text="", variable=filter_names_bool, bg=BG_SECONDARY, activebackground=BG_SECONDARY, fg=TEXT_LIGHT, selectcolor="#0f0f1a", width=1, height=1).pack(side=tk.LEFT, anchor=tk.W)
        self.settings_vars['FILTER_BY_NAME_BOOL'] = filter_names_bool
        
        # 6. FILTER_BY_NAME List
        create_list_setting(options_container, "FILTER_BY_NAME List (Names):", 'FILTER_BY_NAME_LIST')


        # Save Button
        save_settings_btn = tk.Button(options_container, text="Save Settings", font=("Segoe UI", 12, "bold"), fg=TEXT_LIGHT, bg=ACCENT_COLOR, activebackground="#00a8cc", border=0, relief=tk.FLAT, cursor="hand2", command=self.save_settings, width=15, height=2)
        save_settings_btn.pack(pady=20, padx=20, anchor=tk.E)

        # Update the scroll region after all elements are placed
        settings_frame.update_idletasks()
        settings_canvas.config(scrollregion=settings_canvas.bbox("all"))

    def _load_current_settings(self):
        """Loads and parses the configurable settings from config.py"""
        settings = {}
        try:
            with open(CONFIG_PATH, 'r') as f:
                # Read line by line to prevent massive string capture by regex
                lines = f.readlines()
            
            content = "".join(lines) # For multi-line search if needed, but regex will be line-based

            # Corrected patterns:
            # .*? - non-greedy match; $ - end of line anchor; \s* - optional whitespace
            patterns = {
                # Look for tuple structure (.*?) inside parentheses
                'MONEY_THRESHOLD': r'MONEY_THRESHOLD\s*=\s*\((.*?)\)', 
                # Look for digit(s)
                'PLAYER_TRESHOLD': r'PLAYER_TRESHOLD\s*=\s*(\d+)\s*$', 
                # Look for True/False
                'IGNORE_UNKNOWN': r'IGNORE_UNKNOWN\s*=\s*(True|False)\s*$', 
                # Look for list structure (\[.*?\])
                'IGNORE_LIST': r'IGNORE_LIST\s*=\s*(\[.*?\])\s*$', 
                # Look for anything after = up to the end of line, including optional parentheses
                'FILTER_BY_NAME': r'FILTER_BY_NAME\s*=\s*\(?(.*?)\)?\s*$', 
            }
            
            for key, pattern in patterns.items():
                # Search across all content (DOTALL is not needed if we use line-by-line regex)
                # We iterate through lines for simpler regex matching
                for line in lines:
                    match = re.search(pattern, line)
                    if match:
                        value_str = match.group(1).strip()
                        if not value_str: continue # Skip if captured string is empty

                        # Special handling for MONEY_THRESHOLD value which is inside parentheses
                        if key == 'MONEY_THRESHOLD':
                            # Re-wrap in parentheses for ast.literal_eval if they were captured internally
                            value_str = f'({value_str})'
                        
                        # Special handling for FILTER_BY_NAME: if it doesn't look like a tuple, we wrap it
                        if key == 'FILTER_BY_NAME':
                            if not value_str.startswith('(') and not value_str.endswith(']'):
                                # Tries to handle cases like 'False, ["name"]' -> convert to ('False', ["name"])
                                pass # Keep as is, literal_eval should handle `bool, list` format without outer tuple for ast module
                        
                        try:
                            settings[key] = ast.literal_eval(value_str)
                            break # Found and parsed, move to next key
                        except (ValueError, SyntaxError) as e:
                            # Print only to console/logs, not as app log
                            print(f"[{get_timestamp()}] [WARNING] Could not parse config variable {key} with value '{value_str}': {e}. Using default/empty.")
                            settings[key] = None
                            break # Stop searching lines for this key
                

        except Exception as e:
            # Print file error only
            print(f"[{get_timestamp()}] [ERROR] Error loading config file for settings: {str(e)}")

        # Set safe defaults and clean up any parsing issues
        final_settings = {
            'MONEY_THRESHOLD': settings.get('MONEY_THRESHOLD') if isinstance(settings.get('MONEY_THRESHOLD'), tuple) and len(settings.get('MONEY_THRESHOLD')) == 2 else (1.0, 1999.0),
            'PLAYER_TRESHOLD': settings.get('PLAYER_TRESHOLD') if isinstance(settings.get('PLAYER_TRESHOLD'), int) else 8,
            'IGNORE_UNKNOWN': settings.get('IGNORE_UNKNOWN') if isinstance(settings.get('IGNORE_UNKNOWN'), bool) else True,
            'IGNORE_LIST': settings.get('IGNORE_LIST') if isinstance(settings.get('IGNORE_LIST'), list) else ["La Cucaracha"],
        }
        
        # Special handling for FILTER_BY_NAME: it should be a (bool, list) tuple
        filter_by_name = settings.get('FILTER_BY_NAME')
        
        if isinstance(filter_by_name, tuple) and len(filter_by_name) == 2 and isinstance(filter_by_name[0], bool) and isinstance(filter_by_name[1], list):
            final_settings['FILTER_BY_NAME'] = filter_by_name
        else:
            # If parsing failed or result wasn't expected type, use default
            default_filter = (False, ["Graipuss Medussi", "La Grande Combinasion"])
            final_settings['FILTER_BY_NAME'] = default_filter

        return final_settings

    def save_settings(self):
        """Validates and saves settings to config.py"""
        
        # --- 1. Validation and Parsing ---
        try:
            # MONEY_THRESHOLD
            min_val = float(self.settings_vars['MONEY_THRESHOLD_MIN'].get())
            max_val = float(self.settings_vars['MONEY_THRESHOLD_MAX'].get())
            if min_val >= max_val or min_val < 0 or max_val < 0:
                raise ValueError("MONEY_THRESHOLD: Min must be less than Max and both must be non-negative numbers.")
            new_money_threshold = (min_val, max_val)

            # PLAYER_TRESHOLD
            player_treshold = int(self.settings_vars['PLAYER_TRESHOLD'].get())
            if player_treshold < 0:
                raise ValueError("PLAYER_TRESHOLD must be a non-negative integer.")
            
            # IGNORE_UNKNOWN (already a bool)
            ignore_unknown = self.settings_vars['IGNORE_UNKNOWN'].get()
            
            # Helper to parse list from text area
            def parse_text_area(text_widget):
                text = text_widget.get("1.0", tk.END).strip()
                # Split by comma, remove leading/trailing whitespace, and filter empty strings
                return [item.strip().strip("'\"") for item in text.split(',') if item.strip()]

            # IGNORE_LIST
            new_ignore_list = parse_text_area(self.settings_vars['IGNORE_LIST'])

            # FILTER_BY_NAME
            filter_by_name_bool = self.settings_vars['FILTER_BY_NAME_BOOL'].get()
            new_filter_by_name_list = parse_text_area(self.settings_vars['FILTER_BY_NAME_LIST'])
            new_filter_by_name = (filter_by_name_bool, new_filter_by_name_list)

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            self.log_message(f"Settings validation failed: {e}", "error")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during parsing: {e}")
            self.log_message(f"Unexpected settings parsing error: {e}", "error")
            return


        # --- 2. Write to config.py ---
        try:
            with open(CONFIG_PATH, 'r') as f:
                lines = f.readlines()

            new_lines = []
            
            # Flags to track if we found the variables
            found_vars = {
                'MONEY_THRESHOLD': False, 
                'PLAYER_TRESHOLD': False, 
                'IGNORE_UNKNOWN': False, 
                'IGNORE_LIST': False, 
                'FILTER_BY_NAME': False
            }
            
            for line in lines:
                stripped_line = line.strip()
                
                # Use regex search to robustly find the variable name at the start of the line
                if re.match(r'MONEY_THRESHOLD\s*=', stripped_line):
                    new_lines.append(f'MONEY_THRESHOLD = {new_money_threshold}\n')
                    found_vars['MONEY_THRESHOLD'] = True
                elif re.match(r'PLAYER_TRESHOLD\s*=', stripped_line):
                    new_lines.append(f'PLAYER_TRESHOLD = {player_treshold}\n')
                    found_vars['PLAYER_TRESHOLD'] = True
                elif re.match(r'IGNORE_UNKNOWN\s*=', stripped_line):
                    new_lines.append(f'IGNORE_UNKNOWN = {ignore_unknown}\n')
                    found_vars['IGNORE_UNKNOWN'] = True
                elif re.match(r'IGNORE_LIST\s*=', stripped_line):
                    # Format as Python list string
                    list_str = str(new_ignore_list).replace('"', "'") # Use single quotes for cleaner config
                    new_lines.append(f'IGNORE_LIST = {list_str}\n')
                    found_vars['IGNORE_LIST'] = True
                elif re.match(r'FILTER_BY_NAME\s*=', stripped_line):
                    # Format as Python tuple string (bool, list)
                    list_str = str(new_filter_by_name_list).replace('"', "'")
                    # Ensure it is saved in a parseable format, e.g., False, ['item'] or (False, ['item'])
                    tuple_str = f'{filter_by_name_bool}, {list_str}'
                    new_lines.append(f'FILTER_BY_NAME = {tuple_str}\n')
                    found_vars['FILTER_BY_NAME'] = True
                else:
                    new_lines.append(line)
            
            # If any mandatory variable was not found, append it (should be safe if default config exists)
            # Find a suitable spot (e.g., before BYPASS_10M) to append missing variables if needed
            
            with open(CONFIG_PATH, 'w') as f:
                f.writelines(new_lines)

            messagebox.showinfo("Success", "Settings saved successfully! Please restart the bot to apply changes.")
            self.log_message("Settings saved to config.py. Restart is required.", "success")
            
            # Reload config module (for good measure, although full restart is needed)
            import importlib
            import config
            importlib.reload(config)
            
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to save settings to config.py: {e}")
            self.log_message(f"Failed to save settings: {str(e)}", "error")
    
    # --- Existing Methods (Setup, Logs, Control) ---

    def setup_output_redirect(self):
        class OutputRedirector:
            def __init__(self, ui_instance, original_stream):
                self.ui_instance = ui_instance
                self.original_stream = original_stream
                
            def write(self, string):
                if string and string.strip():
                    try:
                        # Schedule log message for the main thread
                        self.ui_instance.root.after(0, self.ui_instance.log_message_raw, string.rstrip())
                    except:
                        # Fallback if root is destroyed
                        self.original_stream.write(string)
                        self.original_stream.flush()

            def flush(self):
                self.original_stream.flush()
        
        sys.stdout = OutputRedirector(self, self.original_stdout)
        sys.stderr = OutputRedirector(self, self.original_stderr)
    
    def log_message(self, message, tag="info"):
        self.logs_text.config(state=tk.NORMAL)
        timestamp = get_timestamp()
        self.logs_text.insert(tk.END, f"{timestamp} ", "info")
        self.logs_text.insert(tk.END, f"{message}\n", tag)
        self.logs_text.see(tk.END)
        self.logs_text.config(state=tk.DISABLED)
    
    def log_message_raw(self, message):
        self.logs_text.config(state=tk.NORMAL)
        tag = "info"
        if "[ERROR]" in message or "error" in message.lower() or "exception" in message.lower():
            tag = "error"
        elif "[WARNING]" in message or "warning" in message.lower():
            tag = "warning"
        elif ">" in message or "[SUCCESS]" in message.lower() or "connected" in message.lower():
            tag = "success"
        
        # Ensure we don't try to tag an empty line
        if message:
            start_index = self.logs_text.index(tk.END + "-1c")
            self.logs_text.insert(tk.END, f"{message}\n", tag)
            # Tag the inserted message from its start to the end of the line
            self.logs_text.tag_add(tag, start_index, tk.END + "-1c")
            
        self.logs_text.see(tk.END)
        self.logs_text.config(state=tk.DISABLED)
    
    def clear_logs(self):
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.config(state=tk.DISABLED)
    
    def save_token(self):
        """Save Discord token to config file"""
        token = self.token_entry.get().strip()
        
        if not token:
            self.token_status.config(text="Error: Token cannot be empty", fg=ERROR_COLOR)
            self.log_message("Error: Token cannot be empty", "error")
            return
        
        # Strip quotes if the user mistakenly includes them
        token = token.strip('"').strip("'") 

        try:
            with open(CONFIG_PATH, 'r') as f:
                lines = f.readlines()
            
            with open(CONFIG_PATH, 'w') as f:
                found = False
                for line in lines:
                    if line.strip().startswith('DISCORD_TOKEN'):
                        f.write(f'DISCORD_TOKEN = "{token}"\n')
                        found = True
                    else:
                        f.write(line)
                if not found:
                    f.write(f'\nDISCORD_TOKEN = "{token}"\n')

            
            self.token_status.config(text="Token saved successfully! Restart required to apply changes.", fg=SUCCESS_COLOR)
            self.log_message("Discord token updated in config.py. Please restart the application.", "success")
            
            # Reload config module
            import importlib
            import config
            importlib.reload(config)
            
        except Exception as e:
            self.token_status.config(text=f"Error: {str(e)}", fg=ERROR_COLOR)
            self.log_message(f"Failed to save token: {str(e)}", "error")
    
    def start_bot(self):
        global stop_flag, roblox_thread, listener_thread, roblox_main
        
        if not self.is_running:
            try:
                import config
                # Re-import config to ensure latest token is used
                import importlib
                importlib.reload(config)
                
                if not hasattr(config, 'DISCORD_TOKEN') or not config.DISCORD_TOKEN or config.DISCORD_TOKEN.strip('"') == "":
                    self.log_message("ERROR: Discord Token is empty. Please set it in the 'Token' tab.", "error")
                    return
            except Exception as e:
                self.log_message(f"Error reading config: {str(e)}", "error")
                return

            self.is_running = True
            
            try:
                # Reset stop flags in modules if they exist
                import src.roblox as roblox_module
                roblox_module.stop_flag = False
            except:
                pass
            stop_flag = False
            
            self.start_btn.set_state(False)
            self.stop_btn.set_state(True)
            self.status_dot.config(fg=SUCCESS_COLOR)
            self.status_label.config(text="ONLINE", fg=SUCCESS_COLOR)
            self.ws_status.config(text="CONNECTING...", fg="#ffaa00")
            self.dc_status.config(text="CONNECTING...", fg="#ffaa00")
            
            self.log_message(f"{APP_TITLE} STARTING...", "success")
            
            try:
                roblox_thread = threading.Thread(target=roblox_main, daemon=False)
                roblox_thread.start()
                self.log_message("Roblox WebSocket server thread initiated", "success")
            except Exception as e:
                self.log_message(f"Error initiating Roblox server thread: {str(e)}", "error")
                self.ws_status.config(text="FAILED", fg=ERROR_COLOR)
            
            try:
                listener_thread = threading.Thread(target=self.run_listener, daemon=False)
                listener_thread.start()
                self.log_message("Discord listener thread initiated", "success")
            except Exception as e:
                self.log_message(f"Error initiating Discord listener thread: {str(e)}", "error")
                self.dc_status.config(text="FAILED", fg=ERROR_COLOR)
    
    def run_listener(self):
        global stop_flag
        try:
            # Need to re-import listener to get a clean state, or handle its shutdown gracefully
            from discord import listener 
            asyncio.run(listener())
            
        except ImportError as e:
            self.log_message(f"Could not import discord listener components: {str(e)}. Check your 'discord' package and 'listener' module.", "error")
            self.root.after(0, self.stop_bot)
        except Exception as e:
            if not stop_flag:
                self.log_message(f"Discord Listener error: {str(e)}", "error")
                self.root.after(0, self.stop_bot)
    
    def stop_bot(self):
        global stop_flag, roblox_thread, listener_thread
        
        if self.is_running:
            self.is_running = False
            
            stop_flag = True
            try:
                import src.roblox as roblox_module
                roblox_module.stop_flag = True
            except:
                pass
            
            self.start_btn.set_state(True)
            self.stop_btn.set_state(False)
            self.status_dot.config(fg=ERROR_COLOR)
            self.status_label.config(text="OFFLINE", fg=ERROR_COLOR)
            self.ws_status.config(text="DISCONNECTED", fg=ERROR_COLOR)
            self.dc_status.config(text="DISCONNECTED", fg=ERROR_COLOR)
            
            self.log_message(f"STOPPING {APP_TITLE}...", "warning")
            self.log_message("Attempting to signal threads for graceful shutdown...", "warning")
            self.log_message("Stopped successfully. Press START to restart.", "success")


if __name__ == "__main__":
    
    # -------------------------------------------------------------------------------------
    # Если вы исправили ошибку запуска, можете раскомментировать блок ниже, чтобы скрыть консоль.
    if sys.platform == "win32":
        import ctypes
        try:
            # 0 - SW_HIDE
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    # -------------------------------------------------------------------------------------
    
    try:
        root = tk.Tk()
        app = IceHubJoinerUI(root)
        root.mainloop()
    except Exception as e:
        # Пауза для отображения ошибки, если приложение не запустилось
        print("\n" + "="*50)
        print("FATAL ERROR DURING APPLICATION STARTUP:")
        import traceback
        traceback.print_exc()
        print("The application failed to initialize. Check the traceback above.")
        print("Press Enter to close the console...")
        print("="*50 + "\n")
        input()