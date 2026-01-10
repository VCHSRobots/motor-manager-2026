"""
Motor Dynamometer Test Application
FRC Team 4415 - EPIC Robotz
Valley Christian High School, Cerritos, CA

Windows application for testing motors and uploading results to the Motor Management System.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import json
import os
import uuid
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from motor_test_controller import MotorTestController

# Configuration file for storing settings
CONFIG_FILE = "motor_test_config.json"
UPLOADED_TESTS_FILE = "uploaded_tests.json"

def parse_date_input(date_str):
    """
    Parse date string in multiple formats and return dict with appropriate fields.
    Returns: {'date_of_purchase': ..., 'purchase_season': ..., 'purchase_year': ...}
    """
    if not date_str:
        return {}
    
    date_str = date_str.strip()
    
    # Handle Unknown
    if date_str.lower() == 'unknown':
        return {}
    
    # Try to parse as full date (YYYY-MM-DD or YYYY/MM/DD)
    for fmt in ['%Y-%m-%d', '%Y/%m/%d']:
        try:
            from datetime import datetime
            parsed = datetime.strptime(date_str, fmt)
            return {'date_of_purchase': parsed.strftime('%Y-%m-%d')}
        except ValueError:
            pass
    
    # Try MM/DD/YYYY
    try:
        from datetime import datetime
        parsed = datetime.strptime(date_str, '%m/%d/%Y')
        return {'date_of_purchase': parsed.strftime('%Y-%m-%d')}
    except ValueError:
        pass
    
    # Try just year (YYYY)
    if date_str.isdigit() and len(date_str) == 4:
        return {'purchase_year': int(date_str)}
    
    # Try season + year (e.g., "Fall 2024" or "2024 Fall" or "Fall, 2024")
    seasons = ['winter', 'spring', 'summer', 'fall']
    parts = date_str.replace(',', ' ').split()
    
    if len(parts) == 2:
        season = None
        year = None
        
        for part in parts:
            if part.lower() in seasons:
                season = part.capitalize()
            elif part.isdigit() and len(part) == 4:
                year = int(part)
        
        if season and year:
            return {'purchase_season': season, 'purchase_year': year}
        elif year:  # Only year found
            return {'purchase_year': year}
    
    # If we can't parse it, return empty dict
    return {}

class AddMotorDialog(tk.Toplevel):
    """Dialog for adding a new motor to the system"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add New Motor")
        self.geometry("550x500")
        self.resizable(False, False)
        
        self.result = None
        self.parent_app = parent
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Type
        ttk.Label(main_frame, text="Type:", font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var,
                                 values=["Kraken X60", "Kraken X44", "NEO", "NEO 550", 
                                        "NEO Vortex", "Falcon 500", "CIM", "MiniCIM", "BAG", "775pro"],
                                 width=47, state="readonly")
        type_combo.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        type_combo.current(0)
        
        # Date of Purchase
        ttk.Label(main_frame, text="Date of Purchase:", font=('Segoe UI', 10)).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        self.date_var = tk.StringVar()
        date_entry = ttk.Entry(main_frame, textvariable=self.date_var, width=50)
        date_entry.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(main_frame, text="Formats: YYYY-MM-DD, MM/DD/YYYY, YYYY, Season YYYY, Unknown", 
                 font=('Segoe UI', 9), foreground='gray').grid(
            row=4, column=0, sticky="w", pady=(0, 15)
        )
        
        # Status
        ttk.Label(main_frame, text="Status:", font=('Segoe UI', 10)).grid(
            row=5, column=0, sticky="w", pady=(0, 5)
        )
        self.status_var = tk.StringVar()
        status_combo = ttk.Combobox(main_frame, textvariable=self.status_var,
                                   values=["Available", "In Use", "Damaged", "Retired"],
                                   width=47, state="readonly")
        status_combo.grid(row=6, column=0, sticky="ew", pady=(0, 15))
        status_combo.current(0)
        
        # Nickname
        ttk.Label(main_frame, text="Nickname (optional):", font=('Segoe UI', 10)).grid(
            row=7, column=0, sticky="w", pady=(0, 5)
        )
        self.nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(main_frame, textvariable=self.nickname_var, width=50)
        nickname_entry.grid(row=8, column=0, sticky="ew", pady=(0, 15))
        
        # Initial Comments
        ttk.Label(main_frame, text="Initial Comments (optional):", font=('Segoe UI', 10)).grid(
            row=9, column=0, sticky="w", pady=(0, 5)
        )
        self.comments_text = tk.Text(main_frame, width=50, height=5, font=('Segoe UI', 10))
        self.comments_text.grid(row=10, column=0, sticky="ew", pady=(0, 20))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=11, column=0, sticky="ew", pady=(0, 20))
        
        submit_btn = ttk.Button(btn_frame, text="Submit", command=self._submit)
        submit_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._cancel)
        cancel_btn.pack(side="left")
        
        main_frame.columnconfigure(0, weight=1)
    
    def _submit(self):
        """Submit new motor to server"""
        motor_type = self.type_var.get()
        date_input = self.date_var.get()
        status = self.status_var.get()
        nickname = self.nickname_var.get()
        comments = self.comments_text.get("1.0", "end-1c")
        
        if not motor_type or not status:
            messagebox.showwarning("Missing Information", 
                                 "Please fill in Type and Status.")
            return
        
        # Parse date input
        date_fields = parse_date_input(date_input)
        
        # Get server settings
        if not self.parent_app.settings.get('server_url'):
            messagebox.showerror("No Server Configured",
                               "Please configure server settings first.")
            return
        
        server_url = self.parent_app.settings.get('server_url').rstrip('/')
        username = self.parent_app.settings.get('username')
        password = self.parent_app.settings.get('password')
        
        if not username or not password:
            messagebox.showerror("Missing Credentials",
                               "Please configure username and password in Setup.")
            return
        
        try:
            # Login to get token
            login_url = f"{server_url}/auth/login"
            login_response = requests.post(
                login_url,
                params={"username": username, "password": password},
                timeout=10
            )
            
            if login_response.status_code != 200:
                messagebox.showerror("Login Failed",
                                   f"Could not authenticate with server.\n"
                                   f"Status code: {login_response.status_code}")
                return
            
            token_data = login_response.json()
            token = token_data.get('token')
            
            if not token:
                messagebox.showerror("Login Error",
                                   "Server did not return authentication token.")
                return
            
            # Create motor payload
            motor_payload = {
                "name": nickname if nickname else motor_type,
                "motor_type": motor_type,
                "status": status
            }
            
            # Add date fields from parsed input
            motor_payload.update(date_fields)
            
            # Create motor on server
            motors_url = f"{server_url}/motors"
            headers = {"Authorization": f"Bearer {token}"}
            
            create_response = requests.post(
                motors_url,
                json=motor_payload,
                headers=headers,
                timeout=10
            )
            
            if create_response.status_code == 200:
                created_motor = create_response.json()
                motor_id = created_motor.get('motor_id')
                
                # If there are comments, add them as a log entry
                if comments and motor_id:
                    log_url = f"{server_url}/motors/{created_motor.get('id')}/logs"
                    log_payload = {
                        "entry": comments
                    }
                    requests.post(log_url, json=log_payload, headers=headers, timeout=10)
                
                self.result = {
                    'motor_id': motor_id,
                    'motor_data': created_motor
                }
                
                # Close dialog immediately without confirmation
                self.destroy()
            else:
                messagebox.showerror("Creation Failed",
                                   f"Failed to create motor.\n"
                                   f"Status code: {create_response.status_code}\n"
                                   f"Response: {create_response.text[:200]}")
        
        except Timeout:
            messagebox.showerror("Timeout",
                               "Request timed out. Please check your connection.")
        except ConnectionError:
            messagebox.showerror("Connection Error",
                               f"Could not connect to server at {server_url}")
        except Exception as e:
            messagebox.showerror("Error",
                               f"An error occurred:\n\n{str(e)}")
    
    def _cancel(self):
        """Cancel without saving"""
        self.result = None
        self.destroy()


class SettingsDialog(tk.Toplevel):
    """Dialog for configuring server connection settings"""
    
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("550x650")
        self.resizable(False, False)
        
        self.result = None
        self.current_settings = current_settings
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._load_settings()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Server URL
        ttk.Label(main_frame, text="Server URL:", font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Username
        ttk.Label(main_frame, text="Username:", font=('Segoe UI', 10)).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=50)
        username_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Password
        ttk.Label(main_frame, text="Password:", font=('Segoe UI', 10)).grid(
            row=4, column=0, sticky="w", pady=(0, 5)
        )
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                   width=50, show="*")
        password_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Output Folder
        ttk.Label(main_frame, text="Output Folder:", font=('Segoe UI', 10)).grid(
            row=6, column=0, sticky="w", pady=(0, 5)
        )
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.output_folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.output_folder_var, width=42)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_btn = ttk.Button(folder_frame, text="Browse", command=self._browse_folder, width=8)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # === Weight Lift Test Hardware Settings ===
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(0, 10)
        )
        ttk.Label(main_frame, text="Weight Lift Test Hardware", font=('Segoe UI', 10, 'bold')).grid(
            row=9, column=0, sticky="w", pady=(0, 10)
        )
        
        # Row 10: Gear Ratio + Spool Diameter
        row10_frame = ttk.Frame(main_frame)
        row10_frame.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(row10_frame, text="Gear Ratio:", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.gear_ratio_var = tk.StringVar()
        ttk.Entry(row10_frame, textvariable=self.gear_ratio_var, width=8).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row10_frame, text="Spool Diameter (in):", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.spool_diameter_var = tk.StringVar()
        ttk.Entry(row10_frame, textvariable=self.spool_diameter_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        # Row 11: Weight + Max Lift Distance
        row11_frame = ttk.Frame(main_frame)
        row11_frame.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(row11_frame, text="Weight (lbs):", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.weight_lbs_var = tk.StringVar()
        ttk.Entry(row11_frame, textvariable=self.weight_lbs_var, width=8).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row11_frame, text="Max Lift Distance (in):", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.max_lift_distance_var = tk.StringVar()
        ttk.Entry(row11_frame, textvariable=self.max_lift_distance_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        # Row 12: Lift Direction (CW/CCW)
        self.lift_direction_cw_var = tk.BooleanVar(value=True)
        lift_dir_frame = ttk.Frame(main_frame)
        lift_dir_frame.grid(row=12, column=0, columnspan=2, sticky="w", pady=(0, 15))
        ttk.Label(lift_dir_frame, text="Lift Direction:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(lift_dir_frame, text="CW", variable=self.lift_direction_cw_var, value=True).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(lift_dir_frame, text="CCW", variable=self.lift_direction_cw_var, value=False).pack(side=tk.LEFT)
        
        # Hardware Description
        ttk.Label(main_frame, text="Hardware Description:", font=('Segoe UI', 10)).grid(
            row=13, column=0, sticky="w", pady=(0, 5)
        )
        self.hardware_desc_var = tk.StringVar()
        hardware_desc_entry = ttk.Entry(main_frame, textvariable=self.hardware_desc_var, width=50)
        hardware_desc_entry.grid(row=14, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=15, column=0, columnspan=2, sticky="ew")
        
        test_btn = ttk.Button(btn_frame, text="Test Connection", 
                             command=self._test_connection)
        test_btn.pack(side="left", padx=(0, 10))
        
        save_btn = ttk.Button(btn_frame, text="Save", command=self._save)
        save_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._cancel)
        cancel_btn.pack(side="left")
        
        main_frame.columnconfigure(0, weight=1)
    
    def _load_settings(self):
        """Load current settings into form"""
        self.url_var.set(self.current_settings.get('server_url', 'http://'))
        self.username_var.set(self.current_settings.get('username', ''))
        self.password_var.set(self.current_settings.get('password', ''))
        self.output_folder_var.set(self.current_settings.get('output_folder', os.path.join(os.path.expanduser('~'), 'Documents', 'MotorTests')))
        self.gear_ratio_var.set(str(self.current_settings.get('gear_ratio', 1.0)))
        self.spool_diameter_var.set(str(self.current_settings.get('spool_diameter', 2.0)))
        self.weight_lbs_var.set(str(self.current_settings.get('weight_lbs', 5.0)))
        self.lift_direction_cw_var.set(self.current_settings.get('lift_direction_cw', True))
        self.max_lift_distance_var.set(str(self.current_settings.get('max_lift_distance', 18.0)))
        self.hardware_desc_var.set(self.current_settings.get('hardware_description', ''))
    
    def _browse_folder(self):
        """Browse for output folder"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_folder_var.get()
        )
        if folder:
            self.output_folder_var.set(folder)
    
    def _test_connection(self):
        """Test connection to server"""
        url = self.url_var.get().rstrip('/')
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not url or not username or not password:
            messagebox.showwarning("Missing Information", 
                                 "Please fill in all fields before testing.")
            return
        
        try:
            # Attempt to login to verify credentials
            login_url = f"{url}/auth/login"
            
            response = requests.post(
                login_url,
                params={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    messagebox.showinfo(
                        "Connection Successful", 
                        f"Successfully connected to {url}\n\n"
                        f"Logged in as: {username}\n"
                        f"Server is responding correctly."
                    )
                else:
                    messagebox.showwarning(
                        "Unexpected Response",
                        f"Connected to {url} but received unexpected response format."
                    )
            elif response.status_code == 401:
                messagebox.showerror(
                    "Authentication Failed",
                    f"Connection to {url} successful, but login failed.\n\n"
                    f"Username or password is incorrect."
                )
            else:
                messagebox.showerror(
                    "Connection Failed",
                    f"Server returned error code: {response.status_code}\n\n"
                    f"Response: {response.text[:200]}"
                )
        
        except Timeout:
            messagebox.showerror(
                "Connection Timeout",
                f"Connection to {url} timed out.\n\n"
                f"Please check the server URL and ensure the server is running."
            )
        except ConnectionError:
            messagebox.showerror(
                "Connection Error",
                f"Could not connect to {url}.\n\n"
                f"Please check:\n"
                f"- Server URL is correct\n"
                f"- Server is running\n"
                f"- Network connection is available"
            )
        except RequestException as e:
            messagebox.showerror(
                "Connection Error",
                f"Error connecting to {url}:\n\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )
    
    def _save(self):
        """Save settings and close"""
        # Validate numeric fields
        try:
            gear_ratio = float(self.gear_ratio_var.get())
            if gear_ratio <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Gear ratio must be a positive number")
            return
        
        try:
            spool_diameter = float(self.spool_diameter_var.get())
            if spool_diameter <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Spool diameter must be a positive number")
            return
        
        try:
            weight_lbs = float(self.weight_lbs_var.get())
            if weight_lbs <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Weight must be a positive number")
            return
        
        try:
            max_lift_distance = float(self.max_lift_distance_var.get())
            if max_lift_distance <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Max lift distance must be a positive number")
            return
        
        self.result = {
            'server_url': self.url_var.get(),
            'username': self.username_var.get(),
            'password': self.password_var.get(),
            'output_folder': self.output_folder_var.get(),
            'gear_ratio': gear_ratio,
            'spool_diameter': spool_diameter,
            'weight_lbs': weight_lbs,
            'lift_direction_cw': self.lift_direction_cw_var.get(),
            'max_lift_distance': max_lift_distance,
            'hardware_description': self.hardware_desc_var.get()
        }
        self.destroy()
    
    def _cancel(self):
        """Cancel without saving"""
        self.result = None
        self.destroy()


class MotorTestApp(tk.Tk):
    """Main application window for motor testing"""
    
    def __init__(self):
        super().__init__()
        
        self.title("EPIC Robotz Motor Dynamometer - FRC Team 4415")
        self.geometry("1200x800")
        
        # Application state
        self.settings = self._load_settings()
        self.is_testing = False
        self.current_motor_info = None
        self.motors_cache = []
        self.canivore_connected = False
        self.website_connected = False
        self.motor_connected = False
        self.test_results = None  # Store last test results
        self.test_uuid = None  # UUID for current test
        self.test_max_rpm = 0
        self.test_max_amps = 0
        
        # Graph display settings
        self.graph_settings = {
            'RPM': {'visible': tk.BooleanVar(value=True), 'color': '#1f77b4', 'style': '-', 'width': 1.0},
            'Current': {'visible': tk.BooleanVar(value=True), 'color': '#ff7f0e', 'style': '-', 'width': 1.0},
            'Distance': {'visible': tk.BooleanVar(value=True), 'color': '#e377c2', 'style': '-', 'width': 1.5},
            'Motor Voltage': {'visible': tk.BooleanVar(value=True), 'color': '#2ca02c', 'style': '-', 'width': 0.5},
            'Bus Voltage': {'visible': tk.BooleanVar(value=True), 'color': '#8c564b', 'style': '-', 'width': 0.5},
            'Input Power': {'visible': tk.BooleanVar(value=False), 'color': '#d62728', 'style': '-', 'width': 0.5},
            'Output Power': {'visible': tk.BooleanVar(value=False), 'color': '#9467bd', 'style': '-', 'width': 0.5}
        }
        
        # Motor test controller (will be recreated with device ID)
        self.motor_controller = None
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('vista')  # Modern Windows theme
        
        self._create_widgets()
        
        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Load motors cache after window is displayed
        self.after_idle(self._load_motors_cache)
    
    def _load_settings(self):
        """Load settings from config file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'server_url': 'http://localhost:8000',
            'username': '',
            'password': '',
            'output_folder': os.path.join(os.path.expanduser('~'), 'Documents', 'MotorTests'),
            'gear_ratio': 1.0,
            'spool_diameter': 2.0,  # inches
            'weight_lbs': 5.0,  # pounds
            'lift_direction_cw': True,  # CW = True, CCW = False
            'max_lift_distance': 18.0,  # inches
            'hardware_description': ''
        }
    
    def _save_settings(self):
        """Save settings to config file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _create_widgets(self):
        """Create the main UI layout"""
        
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # SYSTEM STATUS SECTION
        self._create_status_section(main_frame)
        
        # TOP SECTION - Input controls
        self._create_top_section(main_frame)
        
        # MIDDLE SECTION - Graph
        self._create_graph_section(main_frame)
        
        # BOTTOM SECTION - Action buttons
        self._create_bottom_section(main_frame)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Graph gets most space    
    def _create_status_section(self, parent):
        """Create system status section with CANivore and website indicators"""
        
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        status_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        # CANivore status
        ttk.Label(status_frame, text="CANivore:", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.canivore_status_label = ttk.Label(status_frame, text="No Connection",
                                               font=('Segoe UI', 10),
                                               foreground='red')
        self.canivore_status_label.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        # Device ID field
        ttk.Label(status_frame, text="Device ID:", font=('Segoe UI', 10)).grid(
            row=0, column=2, sticky="w", padx=(0, 5)
        )
        self.device_id_var = tk.StringVar(value="1")
        # Trace changes to device ID to auto-reconnect
        self.device_id_var.trace_add('write', lambda *args: self._on_device_id_changed())
        device_id_entry = ttk.Entry(status_frame, textvariable=self.device_id_var, width=5)
        device_id_entry.grid(row=0, column=3, sticky="w", padx=(0, 10))
        
        # Connect button for CANivore/Motor
        self.canivore_connect_btn = ttk.Button(status_frame, text="Connect",
                                               command=self._connect_hardware,
                                               width=10)
        self.canivore_connect_btn.grid(row=0, column=4, sticky="w", padx=(0, 10))
        
        # Motor status
        ttk.Label(status_frame, text="Motor:", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=5, sticky="w", padx=(0, 10)
        )
        self.motor_status_label = ttk.Label(status_frame, text="No Motor Found",
                                           font=('Segoe UI', 10),
                                           foreground='red')
        self.motor_status_label.grid(row=0, column=6, sticky="w", padx=(0, 40))
        
        # Website status
        ttk.Label(status_frame, text="Website:", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=7, sticky="w", padx=(0, 10)
        )
        self.website_status_label = ttk.Label(status_frame, text="Off-Line",
                                             font=('Segoe UI', 10),
                                             foreground='red')
        self.website_status_label.grid(row=0, column=8, sticky="w")
        
        # Check initial status
        self._connect_hardware()
        self._check_website_status()
        
        # Start periodic website polling (every 30 seconds)
        self._start_website_polling()    
    def _create_top_section(self, parent):
        """Create top input section with Motor ID and Max Amps"""
        
        top_frame = ttk.LabelFrame(parent, text="Test Parameters", padding="15")
        top_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Motor ID
        ttk.Label(top_frame, text="Motor ID:", font=('Segoe UI', 11, 'bold')).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.motor_id_var = tk.StringVar()
        self.motor_id_combo = ttk.Combobox(top_frame, textvariable=self.motor_id_var, 
                                          width=15, font=('Segoe UI', 11))
        self.motor_id_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.motor_id_combo.bind('<<ComboboxSelected>>', self._on_motor_selected)
        
        # Refresh button
        refresh_btn = ttk.Button(top_frame, text="Refresh", command=self._refresh_motor)
        refresh_btn.grid(row=0, column=2, sticky="w", padx=(0, 30))
        
        # Max Amps dropdown
        ttk.Label(top_frame, text="Max Amps:", font=('Segoe UI', 11, 'bold')).grid(
            row=0, column=3, sticky="w", padx=(0, 10)
        )
        self.max_amps_var = tk.StringVar(value="20")
        max_amps_combo = ttk.Combobox(top_frame, textvariable=self.max_amps_var,
                                      values=["10", "20", "40"],
                                      state="readonly", width=10,
                                      font=('Segoe UI', 11))
        max_amps_combo.grid(row=0, column=4, sticky="w", padx=(0, 30))
        
        # Add Motor button
        add_motor_btn = ttk.Button(top_frame, text="➕ Add Motor", 
                                   command=self._show_add_motor)
        add_motor_btn.grid(row=0, column=5, sticky="e", padx=(30, 5))
        
        # Setup button (upper right)
        setup_btn = ttk.Button(top_frame, text="⚙ Setup", command=self._show_settings)
        setup_btn.grid(row=0, column=6, sticky="e", padx=(5, 0))
        
        top_frame.columnconfigure(5, weight=1)  # Push buttons to right
    
    def _create_graph_section(self, parent):
        """Create middle section with large graph area and controls"""
        
        graph_frame = ttk.LabelFrame(parent, text="Performance Graph", padding="10")
        graph_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Main container with graph on left and controls on right
        container = ttk.Frame(graph_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Graph
        graph_container = ttk.Frame(container)
        graph_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header with motor info and save button
        header_frame = ttk.Frame(graph_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.motor_info_label = ttk.Label(header_frame, text="Motor Not Known",
                                         font=('Segoe UI', 12, 'bold'),
                                         foreground='#666')
        self.motor_info_label.pack(side=tk.LEFT, expand=True)
        
        # Average power label (initially hidden)
        self.avg_power_label = ttk.Label(header_frame, text="",
                                        font=('Segoe UI', 11, 'bold'),
                                        foreground='#d62728')
        self.avg_power_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Save CSV button
        self.save_csv_btn = tk.Button(header_frame, text="Save CSV",
                                     command=self._save_csv,
                                     font=('Segoe UI', 9),
                                     bg="#17a2b8", fg="white",
                                     activebackground="#138496",
                                     activeforeground="white",
                                     relief=tk.RAISED,
                                     cursor="hand2",
                                     padx=10, pady=3,
                                     state="disabled")
        self.save_csv_btn.pack(side=tk.RIGHT)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(9, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Initial empty plot
        self.ax.set_xlabel('Time (seconds)', fontsize=11)
        self.ax.set_ylabel('Value', fontsize=11)
        self.ax.set_title('Motor Performance Test', fontsize=13, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(0, 60)
        self.ax.set_ylim(0, 100)
        
        # Embed matplotlib figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.draw()
        
        # Add matplotlib navigation toolbar for zoom/pan/reset
        toolbar_frame = ttk.Frame(graph_container)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Pack canvas after toolbar so toolbar appears at bottom
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Right side - Display Controls
        self._create_graph_controls(container)
        
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)
    
    def _create_graph_controls(self, parent):
        """Create graph display controls panel"""
        controls_frame = ttk.LabelFrame(parent, text="Display Controls", padding="10")
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        ttk.Label(controls_frame, text="Measurements:", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Create controls for each measurement
        for idx, (name, settings) in enumerate(self.graph_settings.items()):
            # Measurement frame
            meas_frame = ttk.Frame(controls_frame)
            meas_frame.pack(fill=tk.X, pady=5)
            
            # Checkbox for visibility
            cb = ttk.Checkbutton(meas_frame, text=name, variable=settings['visible'],
                               command=self._update_graph_display)
            cb.pack(anchor='w')
            
            # Sub-frame for style controls
            style_frame = ttk.Frame(meas_frame)
            style_frame.pack(fill=tk.X, padx=(20, 0))
            
            # Color picker button
            color_btn = tk.Button(style_frame, bg=settings['color'], width=3, height=1,
                                 command=lambda n=name: self._change_color(n))
            color_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Line style dropdown
            style_var = tk.StringVar(value='Solid' if settings['style'] == '-' else 'Dashed')
            style_combo = ttk.Combobox(style_frame, textvariable=style_var,
                                      values=['Solid', 'Dashed'], width=8, state='readonly')
            style_combo.pack(side=tk.LEFT, padx=(0, 5))
            style_combo.bind('<<ComboboxSelected>>',
                           lambda e, n=name, sv=style_var: self._change_style(n, sv.get()))
            
            # Line width spinner
            width_frame = ttk.Frame(style_frame)
            width_frame.pack(side=tk.LEFT)
            ttk.Label(width_frame, text="W:", font=('Segoe UI', 8)).pack(side=tk.LEFT)
            width_var = tk.StringVar(value=str(settings['width']))
            width_spin = ttk.Spinbox(width_frame, from_=0.5, to=5.0, increment=0.5,
                                    textvariable=width_var, width=5,
                                    command=lambda n=name, wv=width_var: self._change_width(n, wv.get()))
            width_spin.pack(side=tk.LEFT)
        
        # Refresh button
        ttk.Button(controls_frame, text="Refresh Graph",
                  command=self._update_graph_display).pack(pady=(10, 0), fill=tk.X)
    
    def _change_color(self, measurement):
        """Change line color for a measurement"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=self.graph_settings[measurement]['color'],
                                     title=f"Choose color for {measurement}")
        if color[1]:  # color[1] is hex string
            self.graph_settings[measurement]['color'] = color[1]
            self._update_graph_display()
    
    def _change_style(self, measurement, style_name):
        """Change line style for a measurement"""
        self.graph_settings[measurement]['style'] = '-' if style_name == 'Solid' else '--'
        self._update_graph_display()
    
    def _change_width(self, measurement, width_str):
        """Change line width for a measurement"""
        try:
            width = float(width_str)
            self.graph_settings[measurement]['width'] = width
            self._update_graph_display()
        except ValueError:
            pass
    
    def _update_graph_display(self):
        """Redraw graph with current display settings"""
        if self.test_results and self.test_results.data_points:
            # Draw final graph with current settings
            self._draw_graph(self.test_results.data_points, is_final=True)
    
    def _create_bottom_section(self, parent):
        """Create bottom section with START, STOP, UPLOAD buttons"""
        
        bottom_frame = ttk.Frame(parent, padding="15")
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        # Create button style for large buttons
        self.style.configure('Action.TButton', font=('Segoe UI', 14, 'bold'))
        
        # START button (green)
        self.start_btn = tk.Button(bottom_frame, text="START TEST",
                                   command=self._start_test,
                                   bg="#28a745", fg="white",
                                   font=('Segoe UI', 14, 'bold'),
                                   height=2, width=15,
                                   cursor="hand2")
        self.start_btn.pack(side="left", padx=10, expand=True, fill="x")
        
        # STOP button (bright red when active, dull red when disabled)
        self.stop_btn = tk.Button(bottom_frame, text="STOP TEST",
                                  command=self._stop_test,
                                  bg="#8b4545", fg="white",
                                  font=('Segoe UI', 14, 'bold'),
                                  height=2, width=15,
                                  state="disabled")
        self.stop_btn.pack(side="left", padx=10, expand=True, fill="x")
        
        # UPLOAD button (blue)
        self.upload_btn = tk.Button(bottom_frame, text="UPLOAD RESULTS",
                                    command=self._upload_results,
                                    bg="#007bff", fg="white",
                                    font=('Segoe UI', 14, 'bold'),
                                    height=2, width=15,
                                    cursor="hand2",
                                    state="disabled")
        self.upload_btn.pack(side="left", padx=10, expand=True, fill="x")
        
        # Separator for jog controls
        ttk.Separator(bottom_frame, orient='vertical').pack(side="left", fill="y", padx=15)
        
        # Jog controls label
        jog_label = ttk.Label(bottom_frame, text="Jog:", font=('Segoe UI', 11, 'bold'))
        jog_label.pack(side="left", padx=(0, 5))
        
        # UP button (orange) - jog motor forward at 30 RPM while held
        self.jog_up_btn = tk.Button(bottom_frame, text="▲ UP",
                                    bg="#fd7e14", fg="white",
                                    font=('Segoe UI', 12, 'bold'),
                                    height=2, width=8,
                                    cursor="hand2")
        self.jog_up_btn.pack(side="left", padx=5)
        # Bind press and release events for continuous jogging
        self.jog_up_btn.bind('<ButtonPress-1>', lambda e: self._start_jog(30))
        self.jog_up_btn.bind('<ButtonRelease-1>', lambda e: self._stop_jog())
        
        # DOWN button (purple) - jog motor reverse at 30 RPM while held
        self.jog_down_btn = tk.Button(bottom_frame, text="▼ DOWN",
                                      bg="#6f42c1", fg="white",
                                      font=('Segoe UI', 12, 'bold'),
                                      height=2, width=8,
                                      cursor="hand2")
        self.jog_down_btn.pack(side="left", padx=5)
        # Bind press and release events for continuous jogging
        self.jog_down_btn.bind('<ButtonPress-1>', lambda e: self._start_jog(-30))
        self.jog_down_btn.bind('<ButtonRelease-1>', lambda e: self._stop_jog())
    
    def _show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self, self.settings)
        self.wait_window(dialog)
        
        if dialog.result:
            self.settings.update(dialog.result)
            self._save_settings()
            # Reconnect hardware with new settings (including direction, gear ratio, etc.)
            if self.motor_connected:
                self._connect_hardware()
            messagebox.showinfo("Settings Saved", "Settings have been saved.")
    
    def _show_add_motor(self):
        """Show add motor dialog"""
        dialog = AddMotorDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            # Show hourglass cursor while refreshing
            self.config(cursor="wait")
            self.update()
            
            # Reload motor cache from server
            self._load_motors_cache()
            
            # Restore normal cursor
            self.config(cursor="")
            
            # Select the new motor in combobox
            motor_id = dialog.result.get('motor_id')
            if motor_id:
                self.motor_id_var.set(motor_id)
                # Trigger the selection event to display motor info
                self._on_motor_selected()
    
    def _load_motors_cache(self):
        """Load all motors from server into cache"""
        if not self.settings.get('server_url'):
            return
        
        server_url = self.settings.get('server_url').rstrip('/')
        username = self.settings.get('username')
        password = self.settings.get('password')
        
        if not username or not password:
            return
        
        try:
            # Login to get token with 10 second timeout
            login_url = f"{server_url}/auth/login"
            login_response = requests.post(
                login_url,
                params={"username": username, "password": password},
                timeout=10
            )
            
            if login_response.status_code != 200:
                messagebox.showerror("Connection Error",
                                   f"Unable to connect to server.\n\n"
                                   f"Server returned status code: {login_response.status_code}")
                return
            
            token_data = login_response.json()
            token = token_data.get('token')
            
            if not token:
                messagebox.showerror("Connection Error",
                                   "Unable to connect to server.\n\n"
                                   "Server did not return authentication token.")
                return
            
            # Get all motors with 10 second timeout
            motors_url = f"{server_url}/motors"
            headers = {"Authorization": f"Bearer {token}"}
            
            motors_response = requests.get(motors_url, headers=headers, timeout=10)
            
            if motors_response.status_code == 200:
                self.motors_cache = motors_response.json()
                print(f"Loaded {len(self.motors_cache)} motors into cache")
                self._update_motor_id_list()
            else:
                messagebox.showerror("Connection Error",
                                   f"Unable to connect to server.\n\n"
                                   f"Could not retrieve motor list.")
        
        except Timeout:
            messagebox.showerror("Connection Timeout",
                               "Unable to connect to server.\n\n"
                               "Connection timed out after 10 seconds.")
        except ConnectionError:
            messagebox.showerror("Connection Error",
                               f"Unable to connect to server at {server_url}.\n\n"
                               f"Please check your network connection and server settings.")
        except Exception as e:
            messagebox.showerror("Connection Error",
                               f"Unable to connect to server.\n\n"
                               f"Error: {str(e)}")
    
    def _update_motor_id_list(self):
        """Update the motor ID combobox with cached motor IDs"""
        motor_ids = [motor.get('motor_id') for motor in self.motors_cache if motor.get('motor_id')]
        motor_ids.sort()  # Sort alphabetically
        # Add blank option at the top for running tests without specific motor
        motor_ids.insert(0, '')
        self.motor_id_combo['values'] = motor_ids
    
    def _on_motor_selected(self, event=None):
        """Handle motor selection from combobox"""
        motor_id = self.motor_id_var.get()
        
        if not motor_id:
            # Blank selection - clear motor info
            self.current_motor_info = None
            self.motor_info_label.config(text="No Motor Selected", foreground='#6c757d')
            return
        
        # Look up motor in cache
        motor_data = None
        for motor in self.motors_cache:
            if motor.get('motor_id') == motor_id:
                motor_data = motor
                break
        
        if motor_data:
            # Display motor info
            # Determine purchase date display
            date_of_purchase = motor_data.get('date_of_purchase')
            purchase_season = motor_data.get('purchase_season')
            purchase_year = motor_data.get('purchase_year')
            
            if date_of_purchase:
                date_display = str(date_of_purchase)
            elif purchase_season and purchase_year:
                date_display = f"{purchase_season} {purchase_year}"
            elif purchase_year:
                date_display = str(purchase_year)
            else:
                date_display = 'Unknown'
            
            self.current_motor_info = {
                'type': motor_data.get('motor_type', 'Unknown'),
                'date_purchase': date_display,
                'nickname': motor_data.get('nickname', '') or motor_data.get('name', '')
            }
            
            info_text = (f"Motor ID: {motor_id} | "
                        f"Type: {self.current_motor_info['type']} | "
                        f"Purchased: {self.current_motor_info['date_purchase']} | "
                        f"Nickname: {self.current_motor_info['nickname']}")
            
            self.motor_info_label.config(text=info_text, foreground='#28a745')
        else:
            # Motor not in cache
            self.current_motor_info = None
            self.motor_info_label.config(text="Motor Not Known", foreground='#dc3545')
        
        # Update upload button state based on motor selection and test results
        self._update_upload_button_state()
    
    def _update_upload_button_state(self):
        """Enable/disable upload button based on motor selection and test data"""
        has_test_data = hasattr(self, 'test_results') and self.test_results is not None
        has_motor_id = bool(self.motor_id_var.get())
        test_not_uploaded = not self._is_test_uploaded(self.test_uuid) if hasattr(self, 'test_uuid') and self.test_uuid else True
        
        if has_test_data and has_motor_id and test_not_uploaded:
            self.upload_btn.config(state="normal", cursor="hand2")
        else:
            self.upload_btn.config(state="disabled", cursor="")
    
    def _refresh_motor(self):
        """Refresh motor list from server and display selected motor"""
        if not self.settings.get('server_url'):
            messagebox.showwarning("No Server Configured", 
                                 "Please configure server settings first.\n"
                                 "Click the Setup button.")
            return
        
        server_url = self.settings.get('server_url').rstrip('/')
        username = self.settings.get('username')
        password = self.settings.get('password')
        
        if not username or not password:
            messagebox.showwarning("Missing Credentials", 
                                 "Please configure username and password in Setup.")
            return
        
        try:
            # Login to get token
            login_url = f"{server_url}/auth/login"
            login_response = requests.post(
                login_url,
                params={"username": username, "password": password},
                timeout=10
            )
            
            if login_response.status_code != 200:
                messagebox.showerror("Login Failed", 
                                   f"Could not authenticate with server.\n"
                                   f"Status code: {login_response.status_code}")
                return
            
            token_data = login_response.json()
            token = token_data.get('token')
            
            if not token:
                messagebox.showerror("Login Error", 
                                   "Server did not return authentication token.")
                return
            
            # Always reload motors from server
            motors_url = f"{server_url}/motors"
            headers = {"Authorization": f"Bearer {token}"}
            
            motors_response = requests.get(motors_url, headers=headers, timeout=10)
            
            if motors_response.status_code != 200:
                messagebox.showerror("Error", 
                                   f"Could not retrieve motors from server.\n"
                                   f"Status code: {motors_response.status_code}")
                return
            
            # Update cache and combobox list
            self.motors_cache = motors_response.json()
            self._update_motor_id_list()
            
            # If a motor is selected, display its updated info
            motor_id = self.motor_id_var.get()
            if motor_id:
                motor_data = None
                for motor in self.motors_cache:
                    if motor.get('motor_id') == motor_id:
                        motor_data = motor
                        break
                
                if motor_data:
                    # Determine purchase date display
                    date_of_purchase = motor_data.get('date_of_purchase')
                    purchase_season = motor_data.get('purchase_season')
                    purchase_year = motor_data.get('purchase_year')
                    
                    if date_of_purchase:
                        date_display = str(date_of_purchase)
                    elif purchase_season and purchase_year:
                        date_display = f"{purchase_season} {purchase_year}"
                    elif purchase_year:
                        date_display = str(purchase_year)
                    else:
                        date_display = 'Unknown'
                    
                    self.current_motor_info = {
                        'type': motor_data.get('motor_type', 'Unknown'),
                        'date_purchase': date_display,
                        'nickname': motor_data.get('nickname', '') or motor_data.get('name', '')
                    }
                    
                    info_text = (f"Motor ID: {motor_id} | "
                                f"Type: {self.current_motor_info['type']} | "
                                f"Purchased: {self.current_motor_info['date_purchase']} | "
                                f"Nickname: {self.current_motor_info['nickname']}")
                    
                    self.motor_info_label.config(text=info_text, foreground='#28a745')
                else:
                    self.current_motor_info = None
                    self.motor_info_label.config(text="Motor Not Known", foreground='#dc3545')
                    messagebox.showerror("Motor Not Found", 
                                       f"Motor ID '{motor_id}' does not exist in the database.\n\n"
                                       f"Please check the ID or use 'Add Motor' to create it.")
        
        except Timeout:
            messagebox.showerror("Timeout", 
                               f"Request timed out. Please check your connection.")
        except ConnectionError:
            messagebox.showerror("Connection Error", 
                               f"Could not connect to server at {server_url}")
    
    def _start_test(self):
        """Start motor test - weight lift test"""
        motor_id = self.motor_id_var.get()
        max_amps = float(self.max_amps_var.get())
        
        # Check if motor controller is connected
        if not self.motor_connected or not self.motor_controller:
            messagebox.showwarning("Motor Not Connected", 
                                 "No motor is connected.\n\n"
                                 "Please connect to a motor before starting test.")
            return
        
        # Check if motor controller is initialized
        if not self.motor_controller.is_initialized:
            messagebox.showerror("Controller Not Ready",
                               "Motor controller is not initialized.\n\n"
                               "Please reconnect to the motor.")
            return
        
        # Update UI state
        self.is_testing = True
        self.start_btn.config(state="disabled", bg="#6c757d", cursor="")
        self.stop_btn.config(state="normal", bg="#dc3545", cursor="hand2")
        self.save_csv_btn.config(state="disabled", cursor="")
        self.upload_btn.config(state="disabled", cursor="")
        self.test_results = None
        self.test_uuid = str(uuid.uuid4())  # Generate unique UUID for this test
        print(f"Generated test UUID: {self.test_uuid}")
        self.avg_power_label.config(text="")  # Clear average power display
        self.test_max_amps = max_amps  # Store for graph scaling
        
        # Get weight lift settings for display
        max_lift_distance = self.settings.get('max_lift_distance', 18.0)
        weight_lbs = self.settings.get('weight_lbs', 5.0)
        
        # Clear the graph
        self.ax.clear()
        self.ax.set_xlabel('Time (s)', fontsize=10)
        self.ax.set_ylabel('RPM', fontsize=10, color='blue')
        self.ax.tick_params(axis='y', labelcolor='blue')
        self.ax.set_xlim(0, 30)  # 30 second time limit for weight lift
        self.ax.set_ylim(0, max_lift_distance * 1.1)  # 10% headroom on distance
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # Display test info
        if motor_id:
            print(f"Starting weight lift test for Motor ID: {motor_id}")
        print(f"  Max Amps: {max_amps}")
        print(f"  Weight: {weight_lbs} lbs")
        print(f"  Max Distance: {max_lift_distance} inches")
        
        # Run the test in a separate thread to keep UI responsive
        import threading
        test_thread = threading.Thread(
            target=self._run_test_thread,
            args=(motor_id, max_amps),
            daemon=True
        )
        test_thread.start()
    
    def _run_test_thread(self, motor_id, max_amps):
        """Run the motor test in a separate thread"""
        try:
            # Run the weight lift test with callback for real-time graph updates
            result = self.motor_controller.run_test(
                motor_id or "test",
                max_amps,
                callback=self._update_graph_callback
            )
            
            # Store results
            self.test_results = result
            
            # Update UI on main thread
            self.after(0, lambda: self._test_completed(result))
            
        except Exception as e:
            error_msg = f"Test error: {str(e)}"
            print(error_msg)
            self.after(0, lambda: self._test_error(error_msg))
    
    def _update_graph_callback(self, data_point):
        """Callback for real-time graph updates during test"""
        # Schedule graph update on main thread
        self.after(0, lambda: self._update_graph(data_point))
    
    def _update_graph(self, data_point):
        """Update graph with new data point"""
        if not self.is_testing:
            return
        
        # Collect all data points from test results
        if self.test_results and self.test_results.data_points:
            self._draw_graph(self.test_results.data_points, is_final=False)
        else:
            # First data point - initialize the graph
            self.test_results = type('obj', (object,), {'data_points': [data_point]})
    
    def _draw_graph(self, data_points, is_final=False):
        """Draw graph with specified data points and current display settings"""
        times = [dp.timestamp for dp in data_points]
        rpms = [dp.rpm for dp in data_points]
        currents = [dp.current for dp in data_points]
        voltages = [dp.voltage for dp in data_points]
        bus_voltages = [dp.bus_voltage for dp in data_points]
        input_powers = [dp.input_power for dp in data_points]
        output_powers = [dp.output_power for dp in data_points]
        distances = [dp.distance for dp in data_points]
        
        # Clear the main axis
        self.ax.clear()
        
        # Remove any existing twin axes
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        
        # Adjust subplot margins to show all Y-axes
        self.fig.subplots_adjust(left=0.155, right=0.84)
        
        # Determine which axes are needed
        show_current = self.graph_settings['Current']['visible'].get()
        show_motor_voltage = self.graph_settings['Motor Voltage']['visible'].get()
        show_bus_voltage = self.graph_settings['Bus Voltage']['visible'].get()
        show_voltage = show_motor_voltage or show_bus_voltage
        show_rpm = self.graph_settings['RPM']['visible'].get()
        show_distance = self.graph_settings['Distance']['visible'].get()
        show_power = (self.graph_settings['Input Power']['visible'].get() or 
                     self.graph_settings['Output Power']['visible'].get())
        
        # Track active axes for positioning
        left_axes = []
        right_axes = []
        
        # Create axes only if needed
        ax_current = None
        ax_voltage = None
        ax_rpm = None
        ax_distance = None
        ax_power = None
        
        # Set up scales
        max_rpm = self.test_max_rpm * 1.1 if hasattr(self, 'test_max_rpm') and self.test_max_rpm > 0 else 6600
        max_amps = self.test_max_amps * 1.1 if hasattr(self, 'test_max_amps') and self.test_max_amps > 0 else 44
        
        # Build left side axes (Current, Voltage)
        if show_current:
            ax_current = self.ax
            left_axes.append(ax_current)
            ax_current.set_ylim(0, max_amps)
            
            settings = self.graph_settings['Current']
            ax_current.plot(times, currents,
                          color=settings['color'],
                          linestyle=settings['style'],
                          linewidth=settings['width'],
                          label='Current (A)')
            ax_current.set_ylabel('Current (A)', fontsize=10, color=settings['color'])
            ax_current.tick_params(axis='y', labelcolor=settings['color'])
        
        if show_voltage:
            if ax_current is None:
                ax_voltage = self.ax
                left_axes.append(ax_voltage)
            else:
                ax_voltage = self.ax.twinx()
                left_axes.append(ax_voltage)
                # Position on left side
                ax_voltage.spines['left'].set_position(('outward', 60))
                ax_voltage.yaxis.set_label_position('left')
                ax_voltage.yaxis.set_ticks_position('left')
            
            ax_voltage.set_ylim(0, 14)
            
            # Plot motor voltage if enabled
            settings = self.graph_settings['Motor Voltage']
            if settings['visible'].get():
                ax_voltage.plot(times, voltages,
                              color=settings['color'],
                              linestyle=settings['style'],
                              linewidth=settings['width'],
                              label='Motor Voltage (V)')
            
            # Plot bus voltage if enabled
            settings = self.graph_settings['Bus Voltage']
            if settings['visible'].get():
                ax_voltage.plot(times, bus_voltages,
                              color=settings['color'],
                              linestyle=settings['style'],
                              linewidth=settings['width'],
                              label='Bus Voltage (V)')
            
            ax_voltage.set_ylabel('Voltage (V)', fontsize=10, color='#2ca02c')
            ax_voltage.tick_params(axis='y', labelcolor='#2ca02c')
        
        # Build right side axes (RPM, Power)
        if show_rpm:
            if not left_axes:
                ax_rpm = self.ax
            else:
                ax_rpm = self.ax.twinx()
            right_axes.append(ax_rpm)
            ax_rpm.set_ylim(0, max_rpm)
            
            settings = self.graph_settings['RPM']
            ax_rpm.plot(times, rpms,
                       color=settings['color'],
                       linestyle=settings['style'],
                       linewidth=settings['width'],
                       label='RPM')
            ax_rpm.set_ylabel('RPM', fontsize=10, color=settings['color'])
            ax_rpm.tick_params(axis='y', labelcolor=settings['color'])
        
        if show_power:
            if not left_axes and not right_axes:
                ax_power = self.ax
            else:
                ax_power = self.ax.twinx()
            right_axes.append(ax_power)
            
            # Position on right side
            if len(right_axes) > 1:
                ax_power.spines['right'].set_position(('outward', 60))
            
            ax_power.set_ylim(0, 600)
            
            settings_input = self.graph_settings['Input Power']
            if settings_input['visible'].get():
                ax_power.plot(times, input_powers,
                            color=settings_input['color'],
                            linestyle=settings_input['style'],
                            linewidth=settings_input['width'],
                            label='Input Power (W)')
            
            settings_output = self.graph_settings['Output Power']
            if settings_output['visible'].get():
                ax_power.plot(times, output_powers,
                            color=settings_output['color'],
                            linestyle=settings_output['style'],
                            linewidth=settings_output['width'],
                            label='Output Power (W)')
            
            ax_power.set_ylabel('Power (W)', fontsize=10, color='#d62728')
            ax_power.tick_params(axis='y', labelcolor='#d62728')
        
        # Plot Distance on right side
        if show_distance:
            if not left_axes and not right_axes:
                ax_distance = self.ax
            else:
                ax_distance = self.ax.twinx()
            right_axes.append(ax_distance)
            
            # Position on right side
            if len(right_axes) > 1:
                ax_distance.spines['right'].set_position(('outward', 60 * (len(right_axes) - 1)))
            
            max_lift = self.settings.get('max_lift_distance', 18.0) * 1.1
            ax_distance.set_ylim(0, max_lift)
            
            settings = self.graph_settings['Distance']
            ax_distance.plot(times, distances,
                           color=settings['color'],
                           linestyle=settings['style'],
                           linewidth=settings['width'],
                           label='Distance (in)')
            ax_distance.set_ylabel('Distance (in)', fontsize=10, color=settings['color'])
            ax_distance.tick_params(axis='y', labelcolor=settings['color'])
        
        # Configure X axis on the primary axis
        self.ax.set_xlabel('Time (s)', fontsize=10)
        
        # Set X-axis limit based on whether test is complete
        if is_final and data_points:
            import math
            last_time = data_points[-1].timestamp
            max_time = math.ceil(last_time)  # Round up to nearest second
            self.ax.set_xlim(0, max_time)
        else:
            self.ax.set_xlim(0, 10)  # Default 10 second time limit during test
        
        self.ax.grid(True, alpha=0.3)
        
        # If no measurements are visible, show a message
        if not (show_current or show_voltage or show_rpm or show_distance or show_power):
            self.ax.text(0.5, 0.5, 'No measurements selected', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=14, color='gray')
            self.ax.set_ylabel('')
            
        # Display calculated average power if test is complete
        if is_final and data_points and hasattr(self, 'test_results'):
            avg_power = getattr(self.test_results, 'avg_power', None)
            if avg_power is not None:
                title_text = f"Calculated Avg Power: {avg_power:.1f} W (4\"-12\")"
                self.ax.set_title(title_text, fontsize=12, fontweight='bold', color='#333333')
        
        self.canvas.draw()
    
    def _test_completed(self, result):
        """Handle test completion"""
        self.is_testing = False
        self.start_btn.config(state="normal", bg="#28a745", cursor="hand2")
        self.stop_btn.config(state="disabled", bg="#8b4545", cursor="")
        
        # Enable Save CSV button if we have data
        if result.data_points:
            self.save_csv_btn.config(state="normal", cursor="hand2")
        
        # Update upload button state based on data and motor selection
        self._update_upload_button_state()
        
        # Calculate and display average power
        self._calculate_average_power(result)
        
        # Display final graph
        if result.data_points:
            self._draw_graph(result.data_points, is_final=True)
        
        # Show completion message
        status = "Completed" if result.completed else "Timed Out"
        msg = f"Test {status}\n\n" \
              f"Duration: {result.test_duration:.2f}s\n" \
              f"Max RPM Achieved: {result.max_rpm_achieved:.1f}\n" \
              f"Data Points: {len(result.data_points)}"
        
        if result.error_message:
            msg += f"\n\nError: {result.error_message}"
        
        messagebox.showinfo("Test Complete", msg)
    
    def _calculate_average_power(self, result):
        """Calculate and display average power based on time to reach RPM goal"""
        if not result.data_points or not hasattr(self, 'test_target_rpm'):
            self.avg_power_label.config(text="")
            self.calculated_avg_power = None
            return
        
        # Get moment of inertia from settings
        inertia = self.settings.get('flywheel_inertia', 0.0256)
        target_rpm = self.test_target_rpm
        
        # Find the time and measured RPM when RPM goal was reached
        delta_t = None
        measured_rpm = None
        for dp in result.data_points:
            if dp.rpm >= target_rpm:
                delta_t = dp.timestamp
                measured_rpm = dp.rpm
                break
        
        if delta_t is None or delta_t <= 0 or measured_rpm is None:
            self.avg_power_label.config(text="")
            self.calculated_avg_power = None
            return
        
        # Calculate average power: P_avg = (I * pi^2 * RPM^2) / (1800 * delta_t)
        # Use the measured RPM at the time target was reached
        import math
        p_avg = (inertia * math.pi**2 * measured_rpm**2) / (1800 * delta_t)
        
        # Store the calculated value for uploading
        self.calculated_avg_power = p_avg
        
        # Display the result
        self.avg_power_label.config(text=f"Avg Power: {p_avg:.1f} W")
    
    def _test_error(self, error_msg):
        """Handle test error"""
        self.is_testing = False
        self.start_btn.config(state="normal", bg="#28a745", cursor="hand2")
        self.stop_btn.config(state="disabled", bg="#8b4545", cursor="")
        messagebox.showerror("Test Error", error_msg)
    
    def _stop_test(self):
        """Stop motor test"""
        if self.motor_controller:
            self.motor_controller.stop_test()
        
        # Update UI state
        self.is_testing = False
        self.start_btn.config(state="normal", bg="#28a745", cursor="hand2")
        self.stop_btn.config(state="disabled", bg="#8b4545", cursor="")
    
    def _start_jog(self, rpm):
        """Start jogging the motor at specified RPM
        
        Args:
            rpm: Target RPM (positive for up/forward, negative for down/reverse)
        """
        # Don't jog if a test is running
        if self.is_testing:
            return
        
        # Check if motor controller is connected
        if not self.motor_connected or not self.motor_controller:
            return
        
        # Store the jog RPM for continuous feeding
        self._jog_rpm = rpm
        
        # Start jogging
        if self.motor_controller.jog_motor(rpm):
            self._jog_feed_enable()
    
    def _jog_feed_enable(self):
        """Continuously feed the motor enable signal while jogging"""
        if self.motor_controller and self.motor_controller.is_jogging and hasattr(self, '_jog_rpm'):
            # Feed the enable signal by re-sending the jog command
            self.motor_controller.jog_motor(self._jog_rpm)
            # Schedule next feed in 50ms
            self.after(50, self._jog_feed_enable)
    
    def _stop_jog(self):
        """Stop jogging the motor"""
        if hasattr(self, '_jog_rpm'):
            del self._jog_rpm
        if self.motor_controller:
            self.motor_controller.stop_jog()
    
    def _save_csv(self):
        """Save test data to CSV file"""
        if not self.test_results or not self.test_results.data_points:
            messagebox.showwarning("No Data", "No test data to save.")
            return
        
        # Get output folder from settings
        output_folder = self.settings.get('output_folder', os.path.join(os.path.expanduser('~'), 'Documents', 'MotorTests'))
        
        # Create folder if it doesn't exist
        try:
            os.makedirs(output_folder, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create output folder:\n{e}")
            return
        
        # Determine base filename
        motor_id = self.motor_id_var.get().strip()
        if motor_id:
            base_name = motor_id
        else:
            base_name = "test"
        
        # Find next sequence number
        sequence = 1
        while True:
            filename = f"{base_name}-{sequence:03d}.csv"
            filepath = os.path.join(output_folder, filename)
            if not os.path.exists(filepath):
                break
            sequence += 1
        
        # Write CSV file
        try:
            import csv
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['timestamp', 'voltage', 'bus_voltage', 'current', 'rpm', 'input_power', 'output_power'])
                # Write data
                for dp in self.test_results.data_points:
                    writer.writerow([dp.timestamp, dp.voltage, dp.bus_voltage, dp.current, dp.rpm, dp.input_power, dp.output_power])
            
            messagebox.showinfo("Success", f"Test data saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save CSV file:\n{e}")
    
    def _upload_results(self):
        """Upload test results to server"""
        # Check if test was already uploaded
        if self._is_test_uploaded(self.test_uuid):
            messagebox.showwarning("Already Uploaded", 
                                 "This test has already been uploaded.\n\n"
                                 f"Test UUID: {self.test_uuid}")
            return
        
        # Validate server settings
        if not self.settings.get('server_url'):
            messagebox.showwarning("No Server Configured", 
                                 "Please configure server settings first.\n"
                                 "Click the Setup button in the top right.")
            return
        
        # Validate motor ID is selected
        motor_id = self.motor_id_var.get()
        if not motor_id:
            messagebox.showwarning("Motor Required for Upload", 
                                 "Please select a Motor ID before uploading.\n\n"
                                 "Test results must be associated with a specific motor.")
            return
        
        # Validate test results exist
        if not hasattr(self, 'test_results') or self.test_results is None:
            messagebox.showwarning("No Test Data", 
                                 "No test data available to upload.\n"
                                 "Please run a test first.")
            return
        
        # Get authentication token
        server_url = self.settings.get('server_url')
        username = self.settings.get('username')
        password = self.settings.get('password')
        
        if not username or not password:
            messagebox.showwarning("Authentication Required", 
                                 "Please configure username and password in settings.")
            return
        
        try:
            # Authenticate and get token
            auth_response = requests.post(
                f"{server_url}/auth/login",
                params={"username": username, "password": password},
                timeout=10
            )
            
            if auth_response.status_code != 200:
                messagebox.showerror("Authentication Failed", 
                                   f"Could not authenticate:\n{auth_response.text}")
                return
            
            token = auth_response.json().get('token')
            
            if not token:
                messagebox.showerror("Authentication Failed", 
                                   "No token received from server")
                return
            
            # Prepare test data
            from datetime import datetime
            
            test_data = {
                "test_uuid": self.test_uuid,
                "test_date": datetime.now().isoformat(),
                "max_current": self.max_amps_var.get(),
                "gear_ratio": self.settings.get('gear_ratio', 1.0),
                "spool_diameter": self.settings.get('spool_diameter', 2.0),
                "weight_lbs": self.settings.get('weight_lbs', 5.0),
                "lift_direction_cw": self.settings.get('lift_direction_cw', True),
                "max_lift_distance": self.settings.get('max_lift_distance', 18.0),
                "distance_lifted": self.test_results.distance_lifted,
                "hardware_description": self.settings.get('hardware_description', ''),
                "avg_power_10a": None,
                "avg_power_20a": None,
                "avg_power_40a": None,
                "data_points": []
            }
            
            # Add data points
            for dp in self.test_results.data_points:
                test_data["data_points"].append({
                    "timestamp": dp.timestamp,
                    "voltage": dp.voltage,
                    "bus_voltage": dp.bus_voltage,
                    "current": dp.current,
                    "rpm": dp.rpm,
                    "distance": dp.distance,
                    "input_power": dp.input_power,
                    "output_power": dp.output_power
                })
            
            # Add average power for the current test
            max_current = int(self.max_amps_var.get())
            avg_power = self.test_results.avg_power  # Use avg_power from test result
            
            print(f"Debug - max_current: {max_current}, avg_power: {avg_power}")
            
            if avg_power is not None and avg_power > 0:
                if max_current == 10:
                    test_data["avg_power_10a"] = avg_power
                elif max_current == 20:
                    test_data["avg_power_20a"] = avg_power
                elif max_current == 40:
                    test_data["avg_power_40a"] = avg_power
            
            # Upload test data
            headers = {"Authorization": f"Bearer {token}"}
            upload_response = requests.post(
                f"{server_url}/motors/{motor_id}/tests",
                json=test_data,
                headers=headers,
                timeout=30
            )
            
            if upload_response.status_code == 200 or upload_response.status_code == 201:
                # Mark test as uploaded
                self._mark_test_uploaded(self.test_uuid)
                
                # Disable upload button to prevent re-upload
                self.upload_btn.config(state="disabled", cursor="")
                
                messagebox.showinfo("Upload Successful", 
                                  f"Test data uploaded successfully!\n\n"
                                  f"Motor ID: {motor_id}\n"
                                  f"Test Date: {test_data['test_date']}\n"
                                  f"Data Points: {len(test_data['data_points'])}\n\n"
                                  f"This test cannot be uploaded again.")
            else:
                messagebox.showerror("Upload Failed", 
                                   f"Could not upload test data:\n"
                                   f"Status: {upload_response.status_code}\n"
                                   f"{upload_response.text}")
        
        except Timeout:
            messagebox.showerror("Upload Failed", 
                               "Request timed out. Please check your network connection.")
        except ConnectionError:
            messagebox.showerror("Upload Failed", 
                               f"Could not connect to server:\n{server_url}\n\n"
                               "Please check the server URL in settings.")
        except Exception as e:
            messagebox.showerror("Upload Failed", 
                               f"An error occurred:\n{str(e)}")
    
    def _load_uploaded_tests(self):
        """Load the list of uploaded test UUIDs from file"""
        try:
            if os.path.exists(UPLOADED_TESTS_FILE):
                with open(UPLOADED_TESTS_FILE, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            print(f"Error loading uploaded tests: {e}")
            return set()
    
    def _save_uploaded_tests(self, uploaded_tests):
        """Save the list of uploaded test UUIDs to file"""
        try:
            with open(UPLOADED_TESTS_FILE, 'w') as f:
                json.dump(list(uploaded_tests), f, indent=2)
        except Exception as e:
            print(f"Error saving uploaded tests: {e}")
    
    def _is_test_uploaded(self, test_uuid):
        """Check if a test UUID has already been uploaded"""
        if not test_uuid:
            return False
        uploaded_tests = self._load_uploaded_tests()
        return test_uuid in uploaded_tests
    
    def _mark_test_uploaded(self, test_uuid):
        """Mark a test UUID as uploaded"""
        if test_uuid:
            uploaded_tests = self._load_uploaded_tests()
            uploaded_tests.add(test_uuid)
            self._save_uploaded_tests(uploaded_tests)
            print(f"Marked test as uploaded: {test_uuid}")

    
    def _on_close(self):
        """Handle window close event"""
        if self.is_testing:
            response = messagebox.askyesno("Test In Progress", 
                                          "A test is currently running.\n"
                                          "Are you sure you want to exit?")
            if not response:
                return
        
        self.destroy()
    
    def _connect_hardware(self):
        """Connect to CANivore and motor with specified device ID"""
        try:
            # Shutdown existing controller if present
            if self.motor_controller is not None:
                try:
                    self.motor_controller.shutdown()
                except:
                    pass  # Ignore errors during shutdown
            
            # Reset all status flags
            self.canivore_connected = False
            self.motor_connected = False
            
            # Get device ID from input
            try:
                device_id = int(self.device_id_var.get())
            except ValueError:
                messagebox.showerror("Invalid Device ID", "Device ID must be a number")
                self.canivore_status_label.config(text="No Connection", foreground='#dc3545')
                self.motor_status_label.config(text="No Motor Found", foreground='#dc3545')
                return
            
            # Create motor controller with specified device ID and weight lift settings
            gear_ratio = self.settings.get('gear_ratio', 1.0)
            spool_diameter = self.settings.get('spool_diameter', 2.0)
            weight_lbs = self.settings.get('weight_lbs', 5.0)
            lift_direction_cw = self.settings.get('lift_direction_cw', True)
            max_lift_distance = self.settings.get('max_lift_distance', 18.0)
            self.motor_controller = MotorTestController(
                talon_can_id=device_id, 
                gear_ratio=gear_ratio,
                spool_diameter=spool_diameter,
                weight_lbs=weight_lbs,
                lift_direction_cw=lift_direction_cw,
                max_lift_distance=max_lift_distance
            )
            
            # Check if CANivore hardware is available
            self.canivore_connected = self.motor_controller.check_canivore_available()
            
            if self.canivore_connected:
                self.canivore_status_label.config(text="Ready", foreground='#28a745')
            else:
                self.canivore_status_label.config(text="No Connection", foreground='#dc3545')
                self.motor_connected = False
                self.motor_status_label.config(text="No Motor Found", foreground='#dc3545')
                return
            
            # Try to initialize and connect to motor
            success, message = self.motor_controller.initialize()
            
            if success:
                self.motor_connected = True
                self.motor_status_label.config(text="Connected", foreground='#28a745')
            else:
                self.motor_connected = False
                self.motor_status_label.config(text="No Motor Found", foreground='#dc3545')
                print(f"Motor connection failed: {message}")
                
        except Exception as e:
            print(f"Error connecting to hardware: {e}")
            self.canivore_connected = False
            self.motor_connected = False
            self.canivore_status_label.config(text="No Connection", foreground='#dc3545')
            self.motor_status_label.config(text="No Motor Found", foreground='#dc3545')
    
    def _on_device_id_changed(self):
        """Handle device ID change - attempt reconnection after brief delay"""
        # Cancel any pending reconnection
        if hasattr(self, '_reconnect_timer') and self._reconnect_timer:
            self.after_cancel(self._reconnect_timer)
        
        # Schedule reconnection after 500ms (allows user to finish typing)
        self._reconnect_timer = self.after(500, self._connect_hardware)
    
    def _check_website_status(self):
        """Check if website is accessible"""
        if not self.settings.get('server_url'):
            self.website_connected = False
            self.website_status_label.config(text="Off-Line", foreground='#dc3545')
            return
        
        server_url = self.settings.get('server_url').rstrip('/')
        
        try:
            # Quick ping to check if server is accessible
            response = requests.get(f"{server_url}/", timeout=3)
            self.website_connected = response.status_code == 200
            
            if self.website_connected:
                self.website_status_label.config(text="Connected", foreground='#28a745')
            else:
                self.website_status_label.config(text="Off-Line", foreground='#dc3545')
        except:
            self.website_connected = False
            self.website_status_label.config(text="Off-Line", foreground='#dc3545')
    
    def _start_website_polling(self):
        """Start periodic polling of website status every 30 seconds"""
        self._check_website_status()
        # Schedule next check in 30 seconds (30000 milliseconds)
        self.after(30000, self._start_website_polling)


def main():
    """Main entry point"""
    app = MotorTestApp()
    app.mainloop()


if __name__ == "__main__":
    main()
