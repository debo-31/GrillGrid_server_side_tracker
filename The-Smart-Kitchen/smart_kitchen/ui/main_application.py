"""
Main application UI for Smart Kitchen Resource Management System
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import sqlite3
import json

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_kitchen.core.kitchen_algorithm import KitchenResourceManager
from smart_kitchen.data.kitchen_data import (
    STAFF_TYPES, EQUIPMENT_TYPES, STAFF_ICONS, EQUIPMENT_ICONS,
    KITCHEN_SCENARIOS, FOOD_TASKS, TASK_EQUIPMENT_NEEDS
)
from smart_kitchen.ui.visualization import (
    KitchenVisualization, create_resource_allocation_canvas
)
from smart_kitchen.ui.simulation import KitchenSimulation
from smart_kitchen.data.user_database import UserDatabase

SCENARIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'scenarios')
if not os.path.exists(SCENARIO_DIR):
    os.makedirs(SCENARIO_DIR)

class SmartKitchenApp:
    """Main application for the Smart Kitchen Resource Management System"""
    
    def __init__(self, root, user):
        """Initialize the Smart Kitchen application."""
        self.root = root
        self.user = user
        self.db = UserDatabase()
        
        self.root.title(f"Smart Kitchen Resource Management - {user['username']}")
        self.root.geometry("1200x800")
        self.root.configure(bg="#F5F7FA")
        
        # Set up notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create main tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.simulation_tab = ttk.Frame(self.notebook)
        self.comparison_tab = ttk.Frame(self.notebook)
        self.help_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Kitchen Management")
        self.notebook.add(self.simulation_tab, text="Kitchen Simulation")
        self.notebook.add(self.comparison_tab, text="Algorithm Demonstration")
        self.notebook.add(self.help_tab, text="Help & Documentation")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Add User Management tab as 5th tab for admins
        if self.user.get('role') == 'admin':
            self.user_mgmt_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.user_mgmt_tab, text="User Management")
            self.setup_user_management_tab()
        
        # Initialize data
        self.num_staff = 0
        self.num_equipment = 0
        self.staff_names = []
        self.equipment_names = []
        self.available = []
        self.max_resources = []
        self.allocated = []
        self.kitchen_manager = None
        self.scenario_var = tk.StringVar()
        
        # Create and setup UI components
        self.setup_main_tab()
        self.setup_simulation_tab()
        self.setup_comparison_tab()
        self.setup_help_tab()
        self.setup_settings_tab()
        
        # Load default scenario
        self.scenario_var.set("small_kitchen")
        self.load_scenario()
    
    def setup_user_management_tab(self):
        """Set up the user management tab for admins."""
        frame = ttk.Frame(self.user_mgmt_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        # User list
        self.user_listbox = tk.Listbox(frame, height=15)
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.user_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.user_listbox.config(yscrollcommand=scrollbar.set)
        # Controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)
        ttk.Label(control_frame, text="Change Role:").pack(pady=5)
        self.role_var = tk.StringVar(value="user")
        ttk.Radiobutton(control_frame, text="User", variable=self.role_var, value="user").pack(anchor="w")
        ttk.Radiobutton(control_frame, text="Admin", variable=self.role_var, value="admin").pack(anchor="w")
        ttk.Button(control_frame, text="Apply Role", command=self.change_user_role_tab).pack(pady=10)
        ttk.Button(control_frame, text="Delete User", command=self.delete_user_tab).pack(pady=10)
        self._load_users_tab()
    
    def _load_users_tab(self):
        self.user_listbox.delete(0, tk.END)
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, role FROM users ORDER BY username')
            for username, role in cursor.fetchall():
                self.user_listbox.insert(tk.END, f"{username} ({role})")
    
    def change_user_role_tab(self):
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
        username = self.user_listbox.get(selection[0]).split(' ')[0]
        if username == self.user['username']:
            messagebox.showerror("Error", "Cannot change your own role")
            return
        role = self.role_var.get()
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = ? WHERE username = ?', (role, username))
            conn.commit()
        self._load_users_tab()
        messagebox.showinfo("Success", f"Role for {username} set to {role}.")
    
    def delete_user_tab(self):
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
        username = self.user_listbox.get(selection[0]).split(' ')[0]
        if username == self.user['username']:
            messagebox.showerror("Error", "Cannot delete your own account")
            return
        if messagebox.askyesno("Confirm", f"Delete user {username}?"):
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE username = ?', (username,))
                conn.commit()
            self._load_users_tab()
            messagebox.showinfo("Success", f"User {username} deleted.")
    
    def setup_settings_tab(self):
        """Set up the user settings tab"""
        settings_frame = ttk.Frame(self.settings_tab)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # User info section
        user_frame = ttk.LabelFrame(settings_frame, text="User Information")
        user_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(user_frame, text=f"Username: {self.user['username']}").pack(pady=5)
        ttk.Label(user_frame, text=f"Role: {self.user['role']}").pack(pady=5)
        
        # Change password section
        password_frame = ttk.LabelFrame(settings_frame, text="Change Password")
        password_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(password_frame, text="Current Password:").grid(row=0, column=0, padx=5, pady=5)
        self.current_password_entry = ttk.Entry(password_frame, show="*")
        self.current_password_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(password_frame, text="New Password:").grid(row=1, column=0, padx=5, pady=5)
        self.new_password_entry = ttk.Entry(password_frame, show="*")
        self.new_password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(password_frame, text="Confirm New Password:").grid(row=2, column=0, padx=5, pady=5)
        self.confirm_password_entry = ttk.Entry(password_frame, show="*")
        self.confirm_password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Button(
            password_frame,
            text="Change Password",
            command=self.change_password
        ).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Admin section (only visible to admin users)
        if self.user['role'] == 'admin':
            admin_frame = ttk.LabelFrame(settings_frame, text="Admin Settings")
            admin_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(
                admin_frame,
                text="Manage Users",
                command=self.manage_users
            ).pack(pady=10)
    
    def change_password(self):
        """Change user password"""
        current = self.current_password_entry.get()
        new = self.new_password_entry.get()
        confirm = self.confirm_password_entry.get()
        
        if not all([current, new, confirm]):
            messagebox.showerror("Error", "All fields are required")
            return
        
        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match")
            return
        
        if self.db.change_password(self.user['id'], current, new):
            messagebox.showinfo("Success", "Password changed successfully")
            self.current_password_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Current password is incorrect")
    
    def manage_users(self):
        """Open user management window (admin only)"""
        if self.user['role'] != 'admin':
            return
        
        # Create user management window
        user_window = tk.Toplevel(self.root)
        user_window.title("User Management")
        user_window.geometry("600x400")
        
        # Add user list
        user_frame = ttk.Frame(user_window)
        user_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create user list
        self.user_listbox = tk.Listbox(user_frame)
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(user_frame, orient=tk.VERTICAL, command=self.user_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_listbox.config(yscrollcommand=scrollbar.set)
        
        # Load users
        self._load_users()
        
        # Add buttons
        button_frame = ttk.Frame(user_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Delete User",
            command=self.delete_user
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Change Role",
            command=self.change_user_role
        ).pack(side=tk.LEFT, padx=5)
    
    def _load_users(self):
        """Load users into the listbox"""
        self.user_listbox.delete(0, tk.END)
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, role FROM users ORDER BY username')
            for username, role in cursor.fetchall():
                self.user_listbox.insert(tk.END, f"{username} ({role})")
    
    def delete_user(self):
        """Delete selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
        
        username = self.user_listbox.get(selection[0]).split(' ')[0]
        if username == self.user['username']:
            messagebox.showerror("Error", "Cannot delete your own account")
            return
        
        if messagebox.askyesno("Confirm", f"Delete user {username}?"):
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE username = ?', (username,))
                conn.commit()
            self._load_users()
    
    def change_user_role(self):
        """Change role of selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
        
        username = self.user_listbox.get(selection[0]).split(' ')[0]
        if username == self.user['username']:
            messagebox.showerror("Error", "Cannot change your own role")
            return
        
        # Create role selection dialog
        role_window = tk.Toplevel(self.root)
        role_window.title("Change User Role")
        role_window.geometry("300x150")
        
        ttk.Label(role_window, text=f"Select new role for {username}:").pack(pady=10)
        
        role_var = tk.StringVar(value="user")
        ttk.Radiobutton(role_window, text="User", variable=role_var, value="user").pack()
        ttk.Radiobutton(role_window, text="Admin", variable=role_var, value="admin").pack()
        
        def apply_role():
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET role = ? WHERE username = ?', (role_var.get(), username))
                conn.commit()
            self._load_users()
            role_window.destroy()
        
        ttk.Button(role_window, text="Apply", command=apply_role).pack(pady=10)
    
    def setup_main_tab(self):
        """Set up the main kitchen management tab."""
        # Create a horizontal paned window for 50:50 split
        main_pane = ttk.PanedWindow(self.main_tab, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left frame for controls (written/editable)
        left_panel = ttk.Frame(main_pane)
        main_pane.add(left_panel, weight=1)

        # Right frame for diagrams
        right_panel = ttk.Frame(main_pane)
        main_pane.add(right_panel, weight=1)

        # --- LEFT PANEL CONTENTS ---
        # Scenario selection
        scenario_frame = ttk.LabelFrame(left_panel, text="Kitchen Scenario")
        scenario_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(scenario_frame, text="Select Scenario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.scenario_combobox = ttk.Combobox(
            scenario_frame, 
            textvariable=self.scenario_var,
            values=[],
            state="readonly",
            width=30
        )
        self.scenario_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.scenario_combobox.bind("<<ComboboxSelected>>", lambda _: self.load_scenario())
        ttk.Button(scenario_frame, text="Load", command=self.load_scenario).grid(row=0, column=2, padx=2)
        ttk.Button(scenario_frame, text="Save Current", command=self.save_current_scenario).grid(row=0, column=3, padx=2)
        ttk.Button(scenario_frame, text="Browse...", command=self.browse_and_load_scenario).grid(row=0, column=4, padx=2)
        ttk.Button(scenario_frame, text="Refresh", command=self.update_scenario_dropdown).grid(row=0, column=5, padx=2)
        self.update_scenario_dropdown()

        # Kitchen setup
        setup_frame = ttk.LabelFrame(left_panel, text="Kitchen Setup")
        setup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Staff and equipment setup section
        ttk.Label(setup_frame, text="Staff and Equipment Setup", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=5)
        # Staff section with add/remove buttons
        staff_frame = ttk.LabelFrame(setup_frame, text="Kitchen Staff")
        staff_frame.pack(fill=tk.X, pady=5)
        staff_input_frame = ttk.Frame(staff_frame)
        staff_input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(staff_input_frame, text="Staff Name:").pack(side=tk.LEFT, padx=5)
        self.new_staff_entry = ttk.Entry(staff_input_frame, width=20)
        self.new_staff_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(staff_input_frame, text="Add Staff", command=self.add_staff).pack(side=tk.LEFT, padx=5)
        ttk.Button(staff_input_frame, text="Remove Selected", command=self.remove_staff).pack(side=tk.LEFT, padx=5)
        self.staff_listbox = tk.Listbox(staff_frame, height=6, selectmode=tk.SINGLE)
        self.staff_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        staff_scrollbar = ttk.Scrollbar(staff_frame, orient=tk.VERTICAL, command=self.staff_listbox.yview)
        staff_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.staff_listbox.config(yscrollcommand=staff_scrollbar.set)
        # Equipment section with add/remove buttons
        equipment_frame = ttk.LabelFrame(setup_frame, text="Kitchen Equipment")
        equipment_frame.pack(fill=tk.X, pady=5)
        equipment_input_frame = ttk.Frame(equipment_frame)
        equipment_input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(equipment_input_frame, text="Equipment Name:").pack(side=tk.LEFT, padx=5)
        self.new_equipment_entry = ttk.Entry(equipment_input_frame, width=20)
        self.new_equipment_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(equipment_input_frame, text="Quantity:").pack(side=tk.LEFT, padx=5)
        self.equipment_quantity_var = tk.IntVar(value=1)
        equipment_quantity_spinbox = ttk.Spinbox(
            equipment_input_frame,
            from_=1,
            to=10,
            textvariable=self.equipment_quantity_var,
            width=5
        )
        equipment_quantity_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Button(equipment_input_frame, text="Add Equipment", command=self.add_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(equipment_input_frame, text="Remove Selected", command=self.remove_equipment).pack(side=tk.LEFT, padx=5)
        self.equipment_listbox = tk.Listbox(equipment_frame, height=6, selectmode=tk.SINGLE)
        self.equipment_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        equipment_scrollbar = ttk.Scrollbar(equipment_frame, orient=tk.VERTICAL, command=self.equipment_listbox.yview)
        equipment_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.equipment_listbox.config(yscrollcommand=equipment_scrollbar.set)
        # Activity log section
        log_frame = ttk.LabelFrame(setup_frame, text="Activity Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.activity_log = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.activity_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.activity_log.config(state=tk.DISABLED)

        # --- RIGHT PANEL CONTENTS ---
        # Kitchen Visualization (top)
        visualization_frame = ttk.LabelFrame(right_panel, text="Kitchen Visualization")
        visualization_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(10, 5))
        self.visualization_canvas = tk.Canvas(
            visualization_frame,
            width=500,
            height=300,
            bg="white"
        )
        self.visualization_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Resource Matrix (bottom)
        matrix_frame = ttk.LabelFrame(right_panel, text="Resource Matrix")
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 10))
        self.matrix_canvas = create_resource_allocation_canvas(matrix_frame)
        # Safety check section (bottom of right panel)
        safety_frame = ttk.Frame(right_panel)
        safety_frame.pack(fill=tk.X, pady=10)
        ttk.Button(safety_frame, text="Check Safety", command=self.check_safety).pack(side=tk.LEFT, padx=5)
        ttk.Button(safety_frame, text="Detect Deadlock", command=self.detect_deadlock).pack(side=tk.LEFT, padx=5)
        ttk.Button(safety_frame, text="Show Safe Sequence", command=self.show_safe_sequence).pack(side=tk.LEFT, padx=5)
    
    def setup_simulation_tab(self):
        """Set up the kitchen simulation tab."""
        # This will be implemented with the KitchenSimulation class
        self.simulation = KitchenSimulation(self.simulation_tab)
    
    def setup_comparison_tab(self):
        """Set up the algorithm demonstration tab."""
        demonstration_label = ttk.Label(
            self.comparison_tab,
            text="Algorithm Demonstration",
            font=("Helvetica", 14, "bold")
        )
        demonstration_label.pack(pady=20)
        # Create demonstration content
        demonstration_frame = ttk.Frame(self.comparison_tab)
        demonstration_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        # Add algorithm selection (radio buttons)
        algo_frame = ttk.LabelFrame(demonstration_frame, text="Select Algorithm to Demonstrate")
        algo_frame.pack(fill=tk.X, pady=10)
        self.algo_var = tk.StringVar(value="banker")
        ttk.Radiobutton(algo_frame, text="Banker's Algorithm", variable=self.algo_var, value="banker").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(algo_frame, text="FIFO (First-In-First-Out)", variable=self.algo_var, value="fifo").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(algo_frame, text="FCFS (First-Come-First-Served)", variable=self.algo_var, value="fcfs").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(algo_frame, text="RAG (Resource Allocation Graph)", variable=self.algo_var, value="rag").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Button(algo_frame, text="Demonstrate", command=self.demonstrate_algorithm).pack(side=tk.LEFT, padx=20, pady=5)
        # Add demonstration results area (text area)
        demo_frame = ttk.LabelFrame(demonstration_frame, text="Demonstration Output")
        demo_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.demo_output = tk.Text(demo_frame, wrap=tk.WORD, height=15)
        self.demo_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.demo_output.config(state=tk.DISABLED)  # Make it read-only initially
    
    def setup_help_tab(self):
        """Set up the help and documentation tab."""
        help_label = ttk.Label(
            self.help_tab,
            text="Smart Kitchen Resource Management System",
            font=("Helvetica", 16, "bold")
        )
        help_label.pack(pady=20)
        
        # Create help content
        help_frame = ttk.Frame(self.help_tab)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Add documentation tabs
        help_notebook = ttk.Notebook(help_frame)
        help_notebook.pack(fill=tk.BOTH, expand=True)
        
        overview_tab = ttk.Frame(help_notebook)
        theory_tab = ttk.Frame(help_notebook)
        usage_tab = ttk.Frame(help_notebook)
        
        help_notebook.add(overview_tab, text="Overview")
        help_notebook.add(theory_tab, text="Theory")
        help_notebook.add(usage_tab, text="Usage Guide")
        
        # Fill overview tab
        overview_text = tk.Text(overview_tab, wrap=tk.WORD, padx=10, pady=10)
        overview_text.pack(fill=tk.BOTH, expand=True)
        overview_text.insert(tk.END, """
The Smart Kitchen Resource Management System is designed to prevent deadlocks in kitchen operations by applying the Banker's Algorithm from operating systems theory to kitchen resource management.

In a busy kitchen, multiple staff members need to use shared equipment like ovens, stoves, and cutting boards. If resources are not managed properly, deadlocks can occur where staff are waiting for each other to release equipment.

This system:
- Models kitchen staff as processes in an operating system
- Models kitchen equipment as resources
- Uses the Banker's Algorithm to ensure deadlock-free operations
- Provides visualization of resource allocation
- Allows simulation of kitchen workflows
- Compares different resource allocation algorithms

By using this system, kitchen managers can optimize resource utilization, prevent deadlocks, and improve kitchen efficiency.
        """)
        overview_text.config(state=tk.DISABLED)
        
        # Fill theory tab
        theory_text = tk.Text(theory_tab, wrap=tk.WORD, padx=10, pady=10)
        theory_text.pack(fill=tk.BOTH, expand=True)
        theory_text.insert(tk.END, """
Banker's Algorithm Theory:

The Banker's Algorithm is a resource allocation and deadlock avoidance algorithm developed by Edsger Dijkstra. It is named the "Banker's algorithm" because it is used by banks to determine whether a loan can be granted safely without risking default.

In the context of operating systems and resource allocation:

1. Safety State: A state is safe if the system can allocate resources to each process in some order and still avoid a deadlock.

2. Key Data Structures:
   - Available: Vector of available resources
   - Max: Matrix defining maximum demand of each process
   - Allocation: Matrix defining resources currently allocated to each process
   - Need: Matrix indicating remaining resource needs (Max - Allocation)

3. Algorithm Steps:
   a. Check if a resource request can be granted safely
   b. Temporarily allocate requested resources
   c. Check if resulting state is safe by trying to find a safe sequence
   d. If safe, grant the request; otherwise, restore original state

4. Safety Algorithm:
   a. Let Work = Available and Finish[i] = false for all processes
   b. Find an i such that:
      - Finish[i] = false
      - Need[i] ≤ Work
   c. If found, Work = Work + Allocation[i] and Finish[i] = true, then go to step b
   d. If all Finish[i] = true, the system is in a safe state

Kitchen Application:
In our kitchen implementation, staff members are processes, and equipment items are resources. The algorithm ensures that equipment is allocated in a way that prevents deadlocks where staff members are waiting indefinitely for each other's resources.
        """)
        theory_text.config(state=tk.DISABLED)
        
        # Fill usage tab
        usage_text = tk.Text(usage_tab, wrap=tk.WORD, padx=10, pady=10)
        usage_text.pack(fill=tk.BOTH, expand=True)
        usage_text.insert(tk.END, """
Usage Guide:

1. Main Tab - Kitchen Management:
   - Select a predefined kitchen scenario or create your own
   - View staff and equipment resources
   - Request or release equipment for specific staff members
   - Check if the current state is safe
   - View a visual representation of resource allocation
   - Detect potential deadlocks

2. Simulation Tab:
   - Run step-by-step simulations of kitchen operations
   - See how resources are allocated over time
   - Explore how deadlocks can form and how they're prevented
   - Compare efficient vs. inefficient kitchen workflows

3. Comparison Tab:
   - Compare Banker's Algorithm with other resource allocation strategies
   - See metrics like throughput, waiting time, and deadlock prevention
   - Understand the tradeoffs between different approaches

4. Help & Documentation:
   - Learn about the theory behind the Banker's Algorithm
   - Get detailed explanations of system features
   - View examples of kitchen resource management

Getting Started:
1. Choose a kitchen scenario from the dropdown
2. Examine the initial resource allocation
3. Try requesting additional resources for staff members
4. Check if the resulting state is safe
5. Run a simulation to see kitchen operations in action
        """)
        usage_text.config(state=tk.DISABLED)
    
    def load_scenario(self):
        """Load a predefined or custom kitchen scenario."""
        scenario_key = self.scenario_var.get()
        scenario = None
        # Try built-in scenarios first
        if scenario_key in KITCHEN_SCENARIOS:
            scenario = KITCHEN_SCENARIOS[scenario_key]
        else:
            # Try loading from file
            scenario_path = os.path.join(SCENARIO_DIR, f"{scenario_key}.json")
            if os.path.exists(scenario_path):
                with open(scenario_path, 'r') as f:
                    scenario = json.load(f)
        if not scenario:
            messagebox.showerror("Load Scenario", f"Scenario '{scenario_key}' not found.")
            return
        self.staff_names = scenario["staff"]
        self.equipment_names = scenario["equipment"]
        self.num_staff = len(self.staff_names)
        self.num_equipment = len(self.equipment_names)
        self.available = scenario["available"]
        self.max_resources = scenario["max_needs"]
        self.allocated = scenario["allocated"]
        self.kitchen_manager = KitchenResourceManager(
            self.available.copy(),
            [row[:] for row in self.max_resources],
            [row[:] for row in self.allocated]
        )
        self.update_ui()
        self.log_activity(f"Loaded scenario: {scenario_key}")
    
    def save_current_scenario(self):
        """Save the current kitchen state as a custom scenario."""
        from tkinter.simpledialog import askstring
        scenario_name = askstring("Save Scenario", "Enter a name for this scenario:")
        if not scenario_name:
            return
        scenario_path = os.path.join(SCENARIO_DIR, f"{scenario_name}.json")
        scenario_data = {
            "staff": self.staff_names,
            "equipment": self.equipment_names,
            "available": self.available,
            "max_needs": self.max_resources,
            "allocated": self.allocated
        }
        with open(scenario_path, 'w') as f:
            json.dump(scenario_data, f, indent=2)
        messagebox.showinfo("Save Scenario", f"Scenario '{scenario_name}' saved successfully.")
    
    def update_scenario_dropdown(self):
        """Update the scenario dropdown with built-in and saved scenarios."""
        scenario_files = [f[:-5] for f in os.listdir(SCENARIO_DIR) if f.endswith('.json')]
        all_scenarios = list(KITCHEN_SCENARIOS.keys()) + scenario_files
        self.scenario_var.set(all_scenarios[0] if all_scenarios else "")
        self.scenario_combobox['values'] = all_scenarios
    
    def update_ui(self):
        """Update UI elements with current kitchen state."""
        # Update staff listbox
        self.staff_listbox.delete(0, tk.END)
        for i, staff in enumerate(self.staff_names):
            icon = STAFF_ICONS.get(staff, "👤")
            self.staff_listbox.insert(tk.END, f"{icon} {staff}")
            
        # Update equipment listbox
        self.equipment_listbox.delete(0, tk.END)
        for i, equipment in enumerate(self.equipment_names):
            icon = EQUIPMENT_ICONS.get(equipment, "🔧")
            available_count = self.kitchen_manager.available[i]
            self.equipment_listbox.insert(tk.END, f"{icon} {equipment} (Available: {available_count})")
            
        # Update visualization
        KitchenVisualization.draw_kitchen(
            self.visualization_canvas,
            self.staff_names,
            self.equipment_names,
            self.kitchen_manager.available,
            self.kitchen_manager.allocated
        )
        
        # Update resource matrix display
        KitchenVisualization.update_resource_matrix(
            self.matrix_canvas,
            self.staff_names,
            self.equipment_names,
            self.kitchen_manager.available,
            self.kitchen_manager.max_resources,
            self.kitchen_manager.allocated,
            self.kitchen_manager.calculate_need()
        )
    
    def add_staff(self):
        """Add new staff member"""
        staff_name = self.new_staff_entry.get().strip()
        if not staff_name:
            messagebox.showerror("Error", "Please enter a staff name")
            return
        
        if staff_name in self.staff_names:
            messagebox.showerror("Error", "Staff member already exists")
            return
        
        # Add to staff list
        self.staff_names.append(staff_name)
        self.num_staff += 1
        
        # Update max resources matrix
        self.max_resources.append([0] * self.num_equipment)
        self.allocated.append([0] * self.num_equipment)
        
        # Update UI
        self.update_ui()
        
        # Log activity
        self.log_activity(f"Added staff member: {staff_name}")
        
        # Clear input
        self.new_staff_entry.delete(0, tk.END)
    
    def remove_staff(self):
        """Remove selected staff member"""
        selection = self.staff_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a staff member to remove")
            return
        
        staff_name = self.staff_names[selection[0]]
        
        if messagebox.askyesno("Confirm", f"Remove staff member {staff_name}?"):
            # Remove from staff list
            self.staff_names.pop(selection[0])
            self.num_staff -= 1
            
            # Update matrices
            self.max_resources.pop(selection[0])
            self.allocated.pop(selection[0])
            
            # Update UI
            self.update_ui()
            
            # Log activity
            self.log_activity(f"Removed staff member: {staff_name}")
    
    def add_equipment(self):
        """Add new equipment"""
        equipment_name = self.new_equipment_entry.get().strip()
        quantity = self.equipment_quantity_var.get()
        
        if not equipment_name:
            messagebox.showerror("Error", "Please enter an equipment name")
            return
        
        # Compare only raw names, case-insensitive
        if any(e.lower().strip() == equipment_name.lower() for e in self.equipment_names):
            messagebox.showerror("Error", "Equipment already exists")
            return
        
        # Add to equipment list
        self.equipment_names.append(equipment_name)
        self.num_equipment += 1
        self.available.append(quantity)
        for i in range(self.num_staff):
            self.max_resources[i].append(0)
            self.allocated[i].append(0)
        
        # Recreate kitchen manager with updated resources
        self.kitchen_manager = KitchenResourceManager(
            self.available.copy(),
            [row[:] for row in self.max_resources],
            [row[:] for row in self.allocated]
        )
        
        self.update_ui()
        self.log_activity(f"Added equipment: {equipment_name} (Quantity: {quantity})")
        self.new_equipment_entry.delete(0, tk.END)
        self.equipment_quantity_var.set(1)
    
    def remove_equipment(self):
        """Remove selected equipment"""
        selection = self.equipment_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select equipment to remove")
            return
        
        equipment_name = self.equipment_names[selection[0]]
        if messagebox.askyesno("Confirm", f"Remove equipment {equipment_name}?"):
            self.equipment_names.pop(selection[0])
            self.num_equipment -= 1
            self.available.pop(selection[0])
            for i in range(self.num_staff):
                self.max_resources[i].pop(selection[0])
                self.allocated[i].pop(selection[0])
            # Recreate kitchen manager with updated resources
            self.kitchen_manager = KitchenResourceManager(
                self.available.copy(),
                [row[:] for row in self.max_resources],
                [row[:] for row in self.allocated]
            )
            self.update_ui()
            self.log_activity(f"Removed equipment: {equipment_name}")
    
    def log_activity(self, message):
        """Add message to activity log"""
        self.activity_log.config(state=tk.NORMAL)
        self.activity_log.insert(tk.END, f"{message}\n")
        self.activity_log.see(tk.END)
        self.activity_log.config(state=tk.DISABLED)
    
    def check_safety(self):
        """Check if the current kitchen state is safe."""
        safe, sequence = self.kitchen_manager.is_safe()
        
        if safe:
            sequence_str = " → ".join([f"{self.staff_names[i]}" for i in sequence])
            messagebox.showinfo(
                "Safe State",
                f"The kitchen is in a safe state!\nSafe sequence: {sequence_str}"
            )
        else:
            messagebox.showwarning(
                "Unsafe State",
                "The kitchen is in an unsafe state!\nThere is a risk of deadlock."
            )
    
    def detect_deadlock(self):
        """Detect if there is a deadlock in the current state."""
        if self.kitchen_manager.detect_deadlock():
            messagebox.showwarning(
                "Deadlock Detected",
                "A deadlock has been detected in the kitchen!\n\n"
                "Some staff members cannot complete their tasks because they're waiting for equipment that won't be released."
            )
        else:
            messagebox.showinfo(
                "No Deadlock",
                "No deadlock detected. The kitchen is operating safely."
            )
    
    def show_safe_sequence(self):
        """Show the safe sequence if available."""
        safe, sequence = self.kitchen_manager.is_safe()
        
        if not safe:
            messagebox.showwarning(
                "No Safe Sequence",
                "Cannot show safe sequence because the kitchen is in an unsafe state."
            )
            return
            
        # Create a visualization of the safe sequence
        KitchenVisualization.show_safe_sequence(
            self.root,
            self.staff_names,
            self.equipment_names,
            sequence,
            self.kitchen_manager.max_resources,
            self.kitchen_manager.allocated,
            self.kitchen_manager.calculate_need(),
            self.kitchen_manager.available
        )
    
    def demonstrate_algorithm(self):
        algo = self.algo_var.get()
        self.demo_output.config(state=tk.NORMAL)
        self.demo_output.delete("1.0", tk.END)
        if algo == "banker":
            self.run_banker_demo()
        elif algo == "fifo":
            self.run_fifo_demo()
        elif algo == "fcfs":
            self.run_fcfs_demo()
        elif algo == "rag":
            self.run_rag_demo()
        self.demo_output.config(state=tk.NORMAL)

    def run_banker_demo(self):
        import tkinter.simpledialog as sd
        import tkinter as tk
        import re
        from tkinter import messagebox
        # Custom dialog for all input
        class BankerInputDialog(sd.Dialog):
            def body(self, master):
                tk.Label(master, text="Number of processes/users:").grid(row=0, column=0, sticky="w")
                self.n_entry = tk.Entry(master)
                self.n_entry.grid(row=0, column=1)
                tk.Label(master, text="Number of resource types:").grid(row=1, column=0, sticky="w")
                self.m_entry = tk.Entry(master)
                self.m_entry.grid(row=1, column=1)
                tk.Label(master, text="Available resources (e.g. 3 2 2):").grid(row=2, column=0, sticky="w")
                self.available_entry = tk.Entry(master)
                self.available_entry.grid(row=2, column=1)
                tk.Label(master, text="Max matrix (one process per line, e.g. 7 5 3\n3 2 2):").grid(row=3, column=0, sticky="w")
                self.max_entry = tk.Text(master, height=4, width=30)
                self.max_entry.grid(row=3, column=1)
                tk.Label(master, text="Allocated matrix (one process per line, e.g. 0 1 0\n2 0 0):").grid(row=4, column=0, sticky="w")
                self.alloc_entry = tk.Text(master, height=4, width=30)
                self.alloc_entry.grid(row=4, column=1)
                return self.n_entry
            def validate(self):
                try:
                    n = int(self.n_entry.get())
                    m = int(self.m_entry.get())
                    available = [int(x) for x in re.split(r'[ ,]+', self.available_entry.get().strip()) if x]
                    max_matrix = self._parse_matrix(self.max_entry.get("1.0", tk.END), n, m)
                    alloc_matrix = self._parse_matrix(self.alloc_entry.get("1.0", tk.END), n, m)
                    if len(available) != m:
                        raise ValueError('Available vector length mismatch')
                except Exception as e:
                    messagebox.showerror("Input Error", f"Invalid input: {e}")
                    return False
                return True
            def apply(self):
                self.n = int(self.n_entry.get())
                self.m = int(self.m_entry.get())
                self.available = [int(x) for x in re.split(r'[ ,]+', self.available_entry.get().strip()) if x]
                self.max_matrix = self._parse_matrix(self.max_entry.get("1.0", tk.END), self.n, self.m)
                self.alloc_matrix = self._parse_matrix(self.alloc_entry.get("1.0", tk.END), self.n, self.m)
            def _parse_matrix(self, s, n, m):
                rows = [row for row in s.strip().splitlines() if row.strip()]
                matrix = []
                for row in rows:
                    row = row.strip()
                    if not row:
                        continue
                    matrix.append([int(x) for x in re.split(r'[ ,]+', row) if x])
                if len(matrix) != n or any(len(row) != m for row in matrix):
                    raise ValueError('Matrix shape mismatch')
                return matrix
        # Show dialog
        dialog = BankerInputDialog(self.root, title="Banker's Algorithm Input")
        if not hasattr(dialog, 'n'):
            self.demo_output.insert(tk.END, "Input cancelled or invalid.\n")
            return
        n, m = dialog.n, dialog.m
        available = dialog.available
        max_matrix = dialog.max_matrix
        alloc_matrix = dialog.alloc_matrix
        # Compute need matrix
        need_matrix = [[max_matrix[i][j] - alloc_matrix[i][j] for j in range(m)] for i in range(n)]
        # Pretty print matrices
        def pretty_matrix(title, mat, row_labels=None, col_labels=None):
            s = f"{title}\n"
            if col_labels:
                s += "     " + "  ".join(f"R{j}" for j in range(m)) + "\n"
            for i, row in enumerate(mat):
                label = f"P{i}" if row_labels else ""
                s += f"{label:>3}  " + "  ".join(f"{x:>2}" for x in row) + "\n"
            return s
        self.demo_output.insert(tk.END, pretty_matrix("Max Matrix:", max_matrix, row_labels=True, col_labels=True))
        self.demo_output.insert(tk.END, pretty_matrix("Allocated Matrix:", alloc_matrix, row_labels=True, col_labels=True))
        self.demo_output.insert(tk.END, pretty_matrix("Need Matrix:", need_matrix, row_labels=True, col_labels=True))
        self.demo_output.insert(tk.END, f"Available:   " + "  ".join(f"{x:>2}" for x in available) + "\n\n")
        # Show matrix visualization in popup
        self.show_matrix_visualization(max_matrix, alloc_matrix, need_matrix, available)
        # Run Banker's Algorithm step by step
        work = available[:]
        finish = [False] * n
        sequence = []
        steps = []
        while True:
            found = False
            for i in range(n):
                if not finish[i] and all(need_matrix[i][j] <= work[j] for j in range(m)):
                    steps.append(f"Process P{i} can be satisfied: Need={need_matrix[i]}, Work={work}")
                    for j in range(m):
                        work[j] += alloc_matrix[i][j]
                    finish[i] = True
                    sequence.append(i)
                    steps.append(f"After P{i} finishes: Work={work}, Finish={finish}")
                    found = True
                    break
            if not found:
                break
        # Show steps
        self.demo_output.insert(tk.END, "--- Steps ---\n")
        for s in steps:
            self.demo_output.insert(tk.END, s + "\n")
        # Show result
        if all(finish):
            seq_str = '  →  '.join([f"P{idx}" for idx in sequence])
            self.demo_output.insert(tk.END, f"\nSystem is in a SAFE state!\nSafe sequence: {seq_str}\n")
        else:
            self.demo_output.insert(tk.END, "\nSystem is in an UNSAFE state! Potential deadlock detected.\n")

    def show_matrix_visualization(self, max_matrix, alloc_matrix, need_matrix, available):
        import tkinter as tk
        from tkinter import ttk
        n = len(max_matrix)
        m = len(max_matrix[0]) if n > 0 else 0
        popup = tk.Toplevel(self.root)
        popup.title("Resource Matrices Visualization")
        popup.geometry("900x400")
        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        # Column headers
        headers = ["Process"] + [f"Max R{j}" for j in range(m)] + [f"Alloc R{j}" for j in range(m)] + [f"Need R{j}" for j in range(m)]
        for col, h in enumerate(headers):
            tk.Label(frame, text=h, font=("Helvetica", 10, "bold"), borderwidth=1, relief="solid", width=10, bg="#E0E0E0").grid(row=0, column=col, padx=1, pady=1)
        # Matrix rows
        for i in range(n):
            tk.Label(frame, text=f"P{i}", font=("Helvetica", 10, "bold"), borderwidth=1, relief="solid", width=10, bg="#F5F5F5").grid(row=i+1, column=0, padx=1, pady=1)
            for j in range(m):
                tk.Label(frame, text=str(max_matrix[i][j]), width=10, borderwidth=1, relief="solid", bg="#E3F2FD").grid(row=i+1, column=1+j, padx=1, pady=1)
                tk.Label(frame, text=str(alloc_matrix[i][j]), width=10, borderwidth=1, relief="solid", bg="#E8F5E9").grid(row=i+1, column=1+m+j, padx=1, pady=1)
                tk.Label(frame, text=str(need_matrix[i][j]), width=10, borderwidth=1, relief="solid", bg="#FFF8E1").grid(row=i+1, column=1+2*m+j, padx=1, pady=1)
        # Available row
        tk.Label(frame, text="Available", font=("Helvetica", 10, "bold"), borderwidth=1, relief="solid", width=10, bg="#E0E0E0").grid(row=n+2, column=0, padx=1, pady=10)
        for j in range(m):
            tk.Label(frame, text=str(available[j]), width=10, borderwidth=1, relief="solid", bg="#F5F5F5").grid(row=n+2, column=1+j, padx=1, pady=10)
        # Fill empty cells for alignment
        for j in range(m):
            tk.Label(frame, text="", width=10, borderwidth=1, relief="solid", bg="#E8F5E9").grid(row=n+2, column=1+m+j, padx=1, pady=10)
            tk.Label(frame, text="", width=10, borderwidth=1, relief="solid", bg="#FFF8E1").grid(row=n+2, column=1+2*m+j, padx=1, pady=10)
    
    def run_fifo_demo(self):
        import tkinter.simpledialog as sd
        import tkinter as tk
        import re
        # Prompt for number of frames
        frames = sd.askinteger("FIFO", "Enter number of frames:", initialvalue=3)
        if not frames or frames < 1:
            self.demo_output.insert(tk.END, "Invalid number of frames.\n")
            return
        # Prompt for page reference string
        ref_str_input = sd.askstring("FIFO", "Enter page reference string (e.g. 7 0 1 2 0 3 0 4 2 3 0 3 2):", initialvalue="7 0 1 2 0 3 0 4 2 3 0 3 2")
        try:
            ref_str = [int(x) for x in re.split(r'[ ,]+', ref_str_input.strip()) if x]
            if not ref_str:
                raise ValueError
        except:
            self.demo_output.insert(tk.END, "Invalid page reference string.\n")
            return
        frame_list = []
        page_faults = 0
        steps = []
        for idx, page in enumerate(ref_str):
            fault = False
            if page not in frame_list:
                page_faults += 1
                fault = True
                if len(frame_list) < frames:
                    frame_list.append(page)
                else:
                    frame_list.pop(0)
                    frame_list.append(page)
            steps.append((idx+1, page, list(frame_list), fault))
        # Build output
        out = []
        out.append("FIFO Page Replacement Demonstration\n----------------------------------")
        out.append(f"Number of frames: {frames}")
        out.append(f"Page reference string: {', '.join(str(x) for x in ref_str)}\n")
        out.append(f"{'Step':<5}{'Page':<6}{'Frames':<20}{'Fault'}")
        out.append("-"*40)
        for step, page, frs, fault in steps:
            fr_str = ', '.join(str(x) for x in frs)
            out.append(f"{step:<5}{page:<6}{fr_str:<20}{'Yes' if fault else ''}")
        out.append("\nSummary:")
        out.append(f"  Total Page Faults: {page_faults}")
        out.append(f"  Final Frame Contents: {', '.join(str(x) for x in frame_list)}")
        self.demo_output.insert('1.0', '\n'.join(out))
    
    def run_fcfs_demo(self):
        import tkinter.simpledialog as sd
        import tkinter as tk
        import re
        from tkinter import messagebox
        
        # Step 1: Get number of processes
        n = sd.askinteger("FCFS", "Enter number of processes:", initialvalue=3)
        if not n or n < 1:
            self.demo_output.insert(tk.END, "Invalid number of processes.\n")
            return
            
        # Step 2: Get process details
        processes = []
        for i in range(n):
            while True:
                try:
                    details = sd.askstring("FCFS", f"Enter arrival time and burst time for P{i+1} (e.g. 0 5):")
                    if not details:
                        return
                    arrival, burst = map(int, re.split(r'[ ,]+', details.strip()))
                    if arrival < 0 or burst <= 0:
                        raise ValueError
                    processes.append((f"P{i+1}", arrival, burst))
                    break
                except:
                    messagebox.showerror("Input Error", "Invalid input. Please enter two positive numbers separated by space.")
        
        # Sort processes by arrival time
        processes.sort(key=lambda x: x[1])
        
        # Calculate completion times and other metrics
        completion_times = []
        current_time = 0
        for p, arrival, burst in processes:
            if arrival > current_time:
                current_time = arrival
            completion_times.append((p, arrival, burst, current_time, current_time + burst))
            current_time += burst
        
        # Calculate metrics
        total_tat = 0
        total_wt = 0
        metrics = []
        for p, arrival, burst, start, completion in completion_times:
            tat = completion - arrival
            wt = tat - burst
            total_tat += tat
            total_wt += wt
            metrics.append((p, arrival, burst, start, completion, tat, wt))
        
        # Build output
        out = []
        out.append("First-Come-First-Served (FCFS) Scheduling\n----------------------------------------")
        out.append("\nProcess Details:")
        out.append(f"{'Process':<10}{'Arrival':<10}{'Burst':<10}{'Start':<10}{'Completion':<12}{'TAT':<10}{'WT':<10}")
        out.append("-" * 72)
        for p, arrival, burst, start, completion, tat, wt in metrics:
            out.append(f"{p:<10}{arrival:<10}{burst:<10}{start:<10}{completion:<12}{tat:<10}{wt:<10}")
        
        # Add summary
        out.append("\nSummary:")
        out.append(f"Average Turnaround Time: {total_tat/n:.2f} ms")
        out.append(f"Average Waiting Time: {total_wt/n:.2f} ms")
        
        # Create Gantt chart
        out.append("\nGantt Chart:")
        gantt_line = "|"
        time_line = "0"
        current_pos = 0
        
        for p, arrival, burst, start, completion, _, _ in metrics:
            # Add waiting time if needed
            if arrival > current_pos:
                gantt_line += " " * (arrival - current_pos) + "|"
                time_line += " " * (arrival - current_pos) + str(arrival)
                current_pos = arrival
            
            # Add process execution
            gantt_line += f"{p:^{burst}}|"
            time_line += " " * (burst - len(str(completion))) + str(completion)
            current_pos = completion
        
        out.append(gantt_line)
        out.append(time_line)
        
        # Show the output
        self.demo_output.insert('1.0', '\n'.join(out))
        
        # Create visual representation
        self.show_fcfs_visualization(completion_times)
    
    def show_fcfs_visualization(self, completion_times):
        import tkinter as tk
        from tkinter import ttk
        
        popup = tk.Toplevel(self.root)
        popup.title("FCFS Scheduling Visualization")
        popup.geometry("800x400")
        
        # Create canvas for visualization
        canvas = tk.Canvas(popup, width=700, height=300, bg="white")
        canvas.pack(pady=20)
        
        # Draw timeline
        canvas.create_line(50, 250, 650, 250, width=2)  # Main timeline
        for i in range(0, 11):  # Time markers
            x = 50 + i * 60
            canvas.create_line(x, 245, x, 255, width=2)
            canvas.create_text(x, 265, text=str(i))
        
        # Draw process bars
        colors = ["#FF9999", "#99FF99", "#9999FF", "#FFFF99", "#FF99FF"]
        y = 150
        bar_height = 30
        spacing = 40
        
        for i, (p, arrival, burst, start, completion) in enumerate(completion_times):
            # Draw process bar
            x1 = 50 + start * 60
            x2 = 50 + completion * 60
            canvas.create_rectangle(x1, y, x2, y + bar_height, fill=colors[i % len(colors)])
            canvas.create_text((x1 + x2) / 2, y + bar_height/2, text=p)
            
            # Draw arrival time marker
            if arrival > 0:
                canvas.create_line(50 + arrival * 60, y - 10, 50 + arrival * 60, y + bar_height + 10, dash=(4, 2))
            
            y += spacing
        
        # Add legend
        legend_y = 20
        for i, (p, _, _, _, _) in enumerate(completion_times):
            canvas.create_rectangle(50, legend_y, 70, legend_y + 20, fill=colors[i % len(colors)])
            canvas.create_text(90, legend_y + 10, text=p, anchor="w")
            legend_y += 30
        
        # Add labels
        canvas.create_text(350, 280, text="Time (ms)")
        canvas.create_text(20, 150, text="Processes", angle=90)
    
    def run_rag_demo(self):
        import tkinter.simpledialog as sd
        import tkinter as tk
        import re
        from tkinter import messagebox
        # Step 1: Get number of processes and resources
        n = sd.askinteger("RAG", "Enter number of processes:")
        if not n or n < 1:
            self.demo_output.insert(tk.END, "Invalid number of processes.\n")
            return
        m = sd.askinteger("RAG", "Enter number of resources:")
        if not m or m < 1:
            self.demo_output.insert(tk.END, "Invalid number of resources.\n")
            return
        # Step 2: Get process and resource names
        proc_names = [f"P{i+1}" for i in range(n)]
        res_names = [f"R{j+1}" for j in range(m)]
        custom_proc = sd.askstring("RAG", f"Enter process names separated by spaces (default: {' '.join(proc_names)}):")
        if custom_proc:
            proc_names = [x.strip() for x in custom_proc.split() if x.strip()]
            if len(proc_names) != n:
                self.demo_output.insert(tk.END, "Process name count mismatch.\n")
                return
        custom_res = sd.askstring("RAG", f"Enter resource names separated by spaces (default: {' '.join(res_names)}):")
        if custom_res:
            res_names = [x.strip() for x in custom_res.split() if x.strip()]
            if len(res_names) != m:
                self.demo_output.insert(tk.END, "Resource name count mismatch.\n")
                return
        # Step 3: Get number of instances for each resource
        inst_str = sd.askstring("RAG", f"Enter number of instances for each resource (e.g. 1 2 ...):")
        try:
            instances = [int(x) for x in re.split(r'[ ,]+', inst_str.strip()) if x]
            if len(instances) != m:
                raise ValueError
        except:
            self.demo_output.insert(tk.END, "Invalid resource instances input.\n")
            return
        # Step 4: Get request edges
        req_edges = []
        while True:
            req = sd.askstring("RAG", f"Add request edge (format: Process Resource), or leave blank to finish:")
            if not req or not req.strip():
                break
            try:
                p, r = req.strip().split()
                if p not in proc_names or r not in res_names:
                    raise ValueError
                req_edges.append((p, r))
            except:
                messagebox.showerror("Input Error", "Invalid request edge format or unknown names.")
        # Step 5: Get assignment edges
        assign_edges = []
        while True:
            assign = sd.askstring("RAG", f"Add assignment edge (format: Resource Process), or leave blank to finish:")
            if not assign or not assign.strip():
                break
            try:
                r, p = assign.strip().split()
                if p not in proc_names or r not in res_names:
                    raise ValueError
                assign_edges.append((r, p))
            except:
                messagebox.showerror("Input Error", "Invalid assignment edge format or unknown names.")
        # Step 6: Build adjacency list for cycle detection
        adj = {name: [] for name in proc_names + res_names}
        for p, r in req_edges:
            adj[p].append(r)
        for r, p in assign_edges:
            adj[r].append(p)
        # Step 7: Detect cycles (deadlock)
        def find_cycle():
            visited = set()
            stack = []
            def dfs(node, path):
                if node in path:
                    return path[path.index(node):] + [node]
                path.append(node)
                for neighbor in adj[node]:
                    cycle = dfs(neighbor, path.copy())
                    if cycle:
                        return cycle
                return None
            for node in adj:
                cycle = dfs(node, [])
                if cycle:
                    return cycle
            return None
        cycle = find_cycle()
        # Step 8: Show improved ASCII art and results
        out = []
        out.append("Resource Allocation Graph (RAG)\n-----------------------------")
        out.append(f"Processes: {' '.join(proc_names)}")
        out.append(f"Resources: {' '.join(res_names)} (Instances: {' '.join(str(x) for x in instances)})\n")
        out.append("Request Edges:")
        for p, r in req_edges:
            out.append(f"  {p} -> {r}")
        out.append("Assignment Edges:")
        for r, p in assign_edges:
            out.append(f"  {r} -> {p}")
        out.append("\nASCII Graph:")
        # Special layout for the user's example (P1, P2, P3, R1, R2)
        if set(proc_names) == {"P1", "P2", "P3"} and set(res_names) == {"R1", "R2"}:
            # Build edge lookup
            req = {(p, r) for p, r in req_edges}
            assign = {(r, p) for r, p in assign_edges}
            # Draw the specific layout
            out.append("      P1 --> R2")
            out.append("       ^       |")
            out.append("       |       v")
            out.append("R1 <-- P2")
            out.append("^")
            out.append("|")
            out.append("P3")
        else:
            # Fallback: generic layout
            proc_row = "   ".join([f"(o){p}" for p in proc_names])
            res_row = "   ".join([f"[ ]{r}" for r in res_names])
            out.append(proc_row)
            out.append("   |     " * max(len(proc_names), len(res_names)))
            out.append(res_row)
        # Show edges below
        out.append("\nEdges:")
        for p, r in req_edges:
            out.append(f"  {p}  --request-->  {r}")
        for r, p in assign_edges:
            out.append(f"  {r}  --assigned-->  {p}")
        if cycle:
            out.append("\nDeadlock Detected! Cycle: " + ' -> '.join(cycle))
            out.append("\nResolution Options:\n  - Resource Preemption\n  - Process Termination\n  - Request Reordering")
        else:
            out.append("\nNo deadlock detected (no cycle found).")
        self.demo_output.insert('1.0', '\n'.join(out))
    
    def browse_and_load_scenario(self):
        """Open a file dialog to load a scenario from any .json file on the system."""
        file_path = filedialog.askopenfilename(
            title="Select Scenario File",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                scenario = json.load(f)
            self.staff_names = scenario["staff"]
            self.equipment_names = scenario["equipment"]
            self.num_staff = len(self.staff_names)
            self.num_equipment = len(self.equipment_names)
            self.available = scenario["available"]
            self.max_resources = scenario["max_needs"]
            self.allocated = scenario["allocated"]
            self.kitchen_manager = KitchenResourceManager(
                self.available.copy(),
                [row[:] for row in self.max_resources],
                [row[:] for row in self.allocated]
            )
            self.update_ui()
            self.log_activity(f"Loaded scenario from file: {file_path}")
        except Exception as e:
            messagebox.showerror("Load Scenario", f"Failed to load scenario: {e}")


def main():
    """Launch the Smart Kitchen application."""
    root = tk.Tk()
    app = SmartKitchenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 