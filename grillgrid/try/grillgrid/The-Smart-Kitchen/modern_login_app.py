import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')

# Add the current directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from smart_kitchen_app import SmartKitchenApp
except ImportError:
    SmartKitchenApp = None

class BankersAlgorithm:
    def __init__(self):
        self.available = []  # Available resources
        self.maximum = []    # Maximum resources needed
        self.allocation = [] # Currently allocated resources
        self.need = []       # Resources still needed
        self.processes = []  # Process names
        self.resources = []  # Resource names

    def set_resources(self, resource_names, available_resources):
        self.resources = resource_names
        self.available = available_resources

    def add_process(self, process_name, max_resources, allocated_resources):
        self.processes.append(process_name)
        self.maximum.append(max_resources)
        self.allocation.append(allocated_resources)
        # Calculate need
        need = [max_resources[i] - allocated_resources[i] for i in range(len(max_resources))]
        self.need.append(need)

    def is_safe_state(self):
        work = self.available.copy()
        finish = [False] * len(self.processes)
        safe_sequence = []

        while True:
            found = False
            for i in range(len(self.processes)):
                if not finish[i] and all(self.need[i][j] <= work[j] for j in range(len(work))):
                    work = [work[j] + self.allocation[i][j] for j in range(len(work))]
                    finish[i] = True
                    safe_sequence.append(self.processes[i])
                    found = True
                    break
            
            if not found:
                break

        return all(finish), safe_sequence

    def request_resources(self, process_index, request):
        if not all(request[i] <= self.need[process_index][i] for i in range(len(request))):
            return False, "Request exceeds maximum need"

        if not all(request[i] <= self.available[i] for i in range(len(request))):
            return False, "Resources not available"

        # Try allocation
        old_available = self.available.copy()
        old_allocation = [row[:] for row in self.allocation]
        old_need = [row[:] for row in self.need]

        self.available = [self.available[i] - request[i] for i in range(len(request))]
        self.allocation[process_index] = [self.allocation[process_index][i] + request[i] for i in range(len(request))]
        self.need[process_index] = [self.need[process_index][i] - request[i] for i in range(len(request))]

        is_safe, sequence = self.is_safe_state()

        if not is_safe:
            # Revert changes
            self.available = old_available
            self.allocation = old_allocation
            self.need = old_need
            return False, "Allocation would lead to unsafe state"

        return True, f"Request granted. Safe sequence: {' -> '.join(sequence)}"

# Persistent user store using SQLite
class SQLiteUserStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )''')
            conn.commit()

    def add_user(self, username, password, email, role):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)',
                               (username, password, role, email))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate(self, username, password):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email, role FROM users WHERE username = ? AND password_hash = ?', (username, password))
            row = cursor.fetchone()
            if row:
                return {'username': row[0], 'email': row[1], 'role': row[2]}
            return None

    def get_all_users(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email, role FROM users ORDER BY username')
            return cursor.fetchall()

    def set_role(self, username, role):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = ? WHERE username = ?', (role, username))
            conn.commit()
            return cursor.rowcount > 0

    def delete_user(self, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            return cursor.rowcount > 0

def maximize_window(root):
    # Cross-platform maximize
    try:
        root.state('zoomed')  # Windows/Linux
    except:
        try:
            root.attributes('-zoomed', True)  # macOS
        except:
            root.attributes('-fullscreen', True)

class LoginRegisterWindow:
    def __init__(self, root, user_store):
        self.root = root
        self.user_store = user_store
        self.root.title("Smart Kitchen - Login")
        self.root.geometry("500x400")
        self.root.configure(bg="#F5F7FA")
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.login_tab = ttk.Frame(self.notebook)
        self.register_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.login_tab, text="Login")
        self.notebook.add(self.register_tab, text="Register")

        self._setup_login_tab()
        self._setup_register_tab()

    def _setup_login_tab(self):
        frame = ttk.Frame(self.login_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:", font=("Helvetica", 12)).pack(pady=5)
        self.login_username = ttk.Entry(frame, width=30)
        self.login_username.pack(pady=5)

        ttk.Label(frame, text="Password:", font=("Helvetica", 12)).pack(pady=5)
        self.login_password = ttk.Entry(frame, show="*", width=30)
        self.login_password.pack(pady=5)

        ttk.Button(frame, text="Login", command=self.login, style="Accent.TButton").pack(pady=15)

    def _setup_register_tab(self):
        frame = ttk.Frame(self.register_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_username = ttk.Entry(frame, width=30)
        self.reg_username.pack(pady=5)

        ttk.Label(frame, text="Email:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_email = ttk.Entry(frame, width=30)
        self.reg_email.pack(pady=5)

        ttk.Label(frame, text="Password:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_password = ttk.Entry(frame, show="*", width=30)
        self.reg_password.pack(pady=5)

        ttk.Label(frame, text="Confirm Password:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_confirm = ttk.Entry(frame, show="*", width=30)
        self.reg_confirm.pack(pady=5)

        ttk.Label(frame, text="Role:", font=("Helvetica", 12)).pack(pady=5)
        self.role_var = tk.StringVar(value="user")
        role_frame = ttk.Frame(frame)
        role_frame.pack(pady=5)
        ttk.Radiobutton(role_frame, text="User", variable=self.role_var, value="user").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(role_frame, text="Admin", variable=self.role_var, value="admin").pack(side=tk.LEFT, padx=5)

        ttk.Button(frame, text="Register", command=self.register, style="Accent.TButton").pack(pady=15)

    def login(self):
        username = self.login_username.get()
        password = self.login_password.get()
        user = self.user_store.authenticate(username, password)
        if user:
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.root.destroy()
            open_main_app(username, user, self.user_store)
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    def register(self):
        username = self.reg_username.get()
        email = self.reg_email.get()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        role = self.role_var.get()
        if not all([username, email, password, confirm]):
            messagebox.showerror("Error", "All fields are required.")
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        if self.user_store.add_user(username, password, email, role):
            messagebox.showinfo("Success", "Registration successful! Please log in.")
            self.notebook.select(0)
        else:
            messagebox.showerror("Error", "Username or email already exists.")

def open_main_app(username, user, user_store):
    if SmartKitchenApp is not None:
        root = tk.Tk()
        app = SmartKitchenApp(root, {"username": username, "email": user["email"], "role": user["role"]})
        root.mainloop()
    else:
        # Fallback: show algorithm demonstration if SmartKitchenApp is not available
        main_root = tk.Tk()
        main_root.title("Algorithm Demonstration")
        main_root.geometry("1200x800")
        
        # Create main frame
        main_frame = ttk.Frame(main_root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Algorithm Demonstrations", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Result Section
        result_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        result_frame.pack(fill=tk.X, pady=10)
        
        result_text = tk.Text(result_frame, height=10, width=70)
        result_text.pack(pady=5)
        
        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Algorithm Buttons
        ttk.Button(button_frame, text="Banker's Algorithm", 
                  command=lambda: show_bankers_inputs(result_text), 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="FCFS", 
                  command=lambda: show_fcfs_inputs(result_text), 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="FIFO", 
                  command=lambda: show_fifo_inputs(result_text), 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="RAG", 
                  command=lambda: show_rag_inputs(result_text), 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        main_root.mainloop()

def show_bankers_inputs(result_text):
    # Create input window
    input_window = tk.Toplevel()
    input_window.title("Banker's Algorithm Inputs")
    input_window.geometry("600x800")
    
    frame = ttk.Frame(input_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Resource Input Section
    resource_frame = ttk.LabelFrame(frame, text="Resource Configuration", padding=10)
    resource_frame.pack(fill=tk.X, pady=10)

    ttk.Label(resource_frame, text="Resource Names (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    resource_names = ttk.Entry(resource_frame, width=50)
    resource_names.pack(pady=5)
    resource_names.insert(0, "Oven,Stove,Cutting Board")

    ttk.Label(resource_frame, text="Available Resources (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    available_resources = ttk.Entry(resource_frame, width=50)
    available_resources.pack(pady=5)
    available_resources.insert(0, "3,2,4")

    # Process Input Section
    process_frame = ttk.LabelFrame(frame, text="Process Configuration", padding=10)
    process_frame.pack(fill=tk.X, pady=10)

    ttk.Label(process_frame, text="Process Names (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    process_names = ttk.Entry(process_frame, width=50)
    process_names.pack(pady=5)
    process_names.insert(0, "Chef1,Chef2,Chef3")

    ttk.Label(process_frame, text="Maximum Resources (one row per process, comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    maximum_resources = tk.Text(process_frame, height=3, width=50)
    maximum_resources.pack(pady=5)
    maximum_resources.insert("1.0", "2,1,2\n1,2,1\n2,1,3")

    ttk.Label(process_frame, text="Allocated Resources (one row per process, comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    allocated_resources = tk.Text(process_frame, height=3, width=50)
    allocated_resources.pack(pady=5)
    allocated_resources.insert("1.0", "1,0,1\n0,1,0\n1,0,2")

    # Request Section
    request_frame = ttk.LabelFrame(frame, text="Resource Request", padding=10)
    request_frame.pack(fill=tk.X, pady=10)

    ttk.Label(request_frame, text="Process Index (0-based):", font=("Helvetica", 10)).pack(pady=5)
    request_process = ttk.Entry(request_frame, width=10)
    request_process.pack(pady=5)

    ttk.Label(request_frame, text="Requested Resources (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    request_resources = ttk.Entry(request_frame, width=50)
    request_resources.pack(pady=5)

    # Buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Check Safety", command=lambda: check_safety(
        resource_names.get(), available_resources.get(), process_names.get(),
        maximum_resources.get("1.0", tk.END), allocated_resources.get("1.0", tk.END),
        result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    ttk.Button(button_frame, text="Request Resources", command=lambda: request_resources(
        resource_names.get(), available_resources.get(), process_names.get(),
        maximum_resources.get("1.0", tk.END), allocated_resources.get("1.0", tk.END),
        request_process.get(), request_resources.get(), result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    ttk.Button(button_frame, text="Clear", command=lambda: clear_fields(
        resource_names, available_resources, process_names,
        maximum_resources, allocated_resources, request_process,
        request_resources, result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

def show_fcfs_inputs(result_text):
    # Create input window
    input_window = tk.Toplevel()
    input_window.title("FCFS Inputs")
    input_window.geometry("500x400")
    
    frame = ttk.Frame(input_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Process Input Section
    process_frame = ttk.LabelFrame(frame, text="Process Configuration", padding=10)
    process_frame.pack(fill=tk.X, pady=10)

    ttk.Label(process_frame, text="Process Names (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    process_names = ttk.Entry(process_frame, width=50)
    process_names.pack(pady=5)
    process_names.insert(0, "P1,P2,P3,P4")

    ttk.Label(process_frame, text="Arrival Times (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    arrival_times = ttk.Entry(process_frame, width=50)
    arrival_times.pack(pady=5)
    arrival_times.insert(0, "0,1,2,3")

    ttk.Label(process_frame, text="Burst Times (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    burst_times = ttk.Entry(process_frame, width=50)
    burst_times.pack(pady=5)
    burst_times.insert(0, "4,3,1,2")

    # Buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Run FCFS", command=lambda: demonstrate_fcfs(
        process_names.get(), arrival_times.get(), burst_times.get(), result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    ttk.Button(button_frame, text="Clear", command=lambda: clear_fcfs_fields(
        process_names, arrival_times, burst_times, result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

def show_fifo_inputs(result_text):
    # Create input window
    input_window = tk.Toplevel()
    input_window.title("FIFO Inputs")
    input_window.geometry("500x300")
    
    frame = ttk.Frame(input_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Input Section
    input_frame = ttk.LabelFrame(frame, text="Page Reference Configuration", padding=10)
    input_frame.pack(fill=tk.X, pady=10)

    ttk.Label(input_frame, text="Page Reference String (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    page_references = ttk.Entry(input_frame, width=50)
    page_references.pack(pady=5)
    page_references.insert(0, "1,2,3,4,1,2,5,1,2,3,4,5")

    ttk.Label(input_frame, text="Number of Frames:", font=("Helvetica", 10)).pack(pady=5)
    num_frames = ttk.Entry(input_frame, width=10)
    num_frames.pack(pady=5)
    num_frames.insert(0, "3")

    # Buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Run FIFO", command=lambda: demonstrate_fifo(
        page_references.get(), num_frames.get(), result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    ttk.Button(button_frame, text="Clear", command=lambda: clear_fifo_fields(
        page_references, num_frames, result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

def show_rag_inputs(result_text):
    # Create input window
    input_window = tk.Toplevel()
    input_window.title("RAG Inputs")
    input_window.geometry("600x600")
    
    frame = ttk.Frame(input_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Process Input Section
    process_frame = ttk.LabelFrame(frame, text="Process Configuration", padding=10)
    process_frame.pack(fill=tk.X, pady=10)

    ttk.Label(process_frame, text="Process Names (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    process_names = ttk.Entry(process_frame, width=50)
    process_names.pack(pady=5)
    process_names.insert(0, "P1,P2,P3,P4")

    ttk.Label(process_frame, text="Resource Names (comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    resource_names = ttk.Entry(process_frame, width=50)
    resource_names.pack(pady=5)
    resource_names.insert(0, "R1,R2,R3")

    ttk.Label(process_frame, text="Allocation Matrix (one row per process, comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    allocation_matrix = tk.Text(process_frame, height=4, width=50)
    allocation_matrix.pack(pady=5)
    allocation_matrix.insert("1.0", "1,0,1\n0,1,0\n1,0,0\n0,0,1")

    ttk.Label(process_frame, text="Request Matrix (one row per process, comma-separated):", font=("Helvetica", 10)).pack(pady=5)
    request_matrix = tk.Text(process_frame, height=4, width=50)
    request_matrix.pack(pady=5)
    request_matrix.insert("1.0", "0,1,0\n1,0,1\n0,0,1\n1,0,0")

    # Buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Check Deadlock", command=lambda: check_deadlock(
        process_names.get(), resource_names.get(),
        allocation_matrix.get("1.0", tk.END), request_matrix.get("1.0", tk.END),
        result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    ttk.Button(button_frame, text="Clear", command=lambda: clear_rag_fields(
        process_names, resource_names, allocation_matrix,
        request_matrix, result_text
    ), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

def check_safety(resource_names, available_resources, process_names, maximum_resources, allocated_resources, result_text):
    try:
        # Parse inputs
        resource_names = [r.strip() for r in resource_names.split(',')]
        available = [int(r.strip()) for r in available_resources.split(',')]
        process_names = [p.strip() for p in process_names.split(',')]
        
        maximum = []
        for line in maximum_resources.strip().split('\n'):
            maximum.append([int(x.strip()) for x in line.split(',')])
        
        allocation = []
        for line in allocated_resources.strip().split('\n'):
            allocation.append([int(x.strip()) for x in line.split(',')])

        # Initialize algorithm
        banker = BankersAlgorithm()
        banker.set_resources(resource_names, available)
        
        for i in range(len(process_names)):
            banker.add_process(process_names[i], maximum[i], allocation[i])

        # Check safety
        is_safe, sequence = banker.is_safe_state()
        
        # Display results
        result_text.delete("1.0", tk.END)
        if is_safe:
            result_text.insert("1.0", f"System is in a safe state!\nSafe sequence: {' -> '.join(sequence)}")
        else:
            result_text.insert("1.0", "System is in an unsafe state!")

    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")

def request_resources(resource_names, available_resources, process_names, maximum_resources, allocated_resources, request_process, request_resources, result_text):
    try:
        # Parse inputs
        resource_names = [r.strip() for r in resource_names.split(',')]
        available = [int(r.strip()) for r in available_resources.split(',')]
        process_names = [p.strip() for p in process_names.split(',')]
        
        maximum = []
        for line in maximum_resources.strip().split('\n'):
            maximum.append([int(x.strip()) for x in line.split(',')])
        
        allocation = []
        for line in allocated_resources.strip().split('\n'):
            allocation.append([int(x.strip()) for x in line.split(',')])

        # Get request
        process_index = int(request_process)
        request = [int(x.strip()) for x in request_resources.split(',')]

        # Initialize algorithm
        banker = BankersAlgorithm()
        banker.set_resources(resource_names, available)
        
        for i in range(len(process_names)):
            banker.add_process(process_names[i], maximum[i], allocation[i])

        # Process request
        success, message = banker.request_resources(process_index, request)
        
        # Display results
        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", message)

    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")

def clear_fields(resource_names, available_resources, process_names, maximum_resources, allocated_resources, request_process, request_resources, result_text):
    resource_names.delete(0, tk.END)
    available_resources.delete(0, tk.END)
    process_names.delete(0, tk.END)
    maximum_resources.delete("1.0", tk.END)
    allocated_resources.delete("1.0", tk.END)
    request_process.delete(0, tk.END)
    request_resources.delete(0, tk.END)
    result_text.delete("1.0", tk.END)

def demonstrate_fcfs(process_names, arrival_times, burst_times, result_text):
    try:
        # Parse inputs
        processes = [p.strip() for p in process_names.split(',')]
        arrivals = [int(t.strip()) for t in arrival_times.split(',')]
        bursts = [int(t.strip()) for t in burst_times.split(',')]
        
        # Calculate completion time, turnaround time, and waiting time
        completion_times = []
        turnaround_times = []
        waiting_times = []
        current_time = 0
        
        for i in range(len(processes)):
            if current_time < arrivals[i]:
                current_time = arrivals[i]
            completion_times.append(current_time + bursts[i])
            turnaround_times.append(completion_times[i] - arrivals[i])
            waiting_times.append(turnaround_times[i] - bursts[i])
            current_time = completion_times[i]
        
        # Calculate averages
        avg_turnaround = sum(turnaround_times) / len(turnaround_times)
        avg_waiting = sum(waiting_times) / len(waiting_times)
        
        # Display results
        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", "FCFS Scheduling Results:\n\n")
        result_text.insert(tk.END, f"{'Process':<10}{'Arrival':<10}{'Burst':<10}{'Completion':<10}{'Turnaround':<10}{'Waiting':<10}\n")
        result_text.insert(tk.END, "-" * 60 + "\n")
        
        for i in range(len(processes)):
            result_text.insert(tk.END, f"{processes[i]:<10}{arrivals[i]:<10}{bursts[i]:<10}{completion_times[i]:<10}{turnaround_times[i]:<10}{waiting_times[i]:<10}\n")
        
        result_text.insert(tk.END, "\n")
        result_text.insert(tk.END, f"Average Turnaround Time: {avg_turnaround:.2f}\n")
        result_text.insert(tk.END, f"Average Waiting Time: {avg_waiting:.2f}\n")
        
    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")

def demonstrate_fifo(page_references, num_frames, result_text):
    try:
        # Parse inputs
        references = [int(p.strip()) for p in page_references.split(',')]
        frames = int(num_frames.strip())
        
        # Initialize variables
        page_faults = 0
        frame_list = []
        result = []
        
        # Simulate FIFO page replacement
        for page in references:
            if page not in frame_list:
                page_faults += 1
                if len(frame_list) >= frames:
                    frame_list.pop(0)
                frame_list.append(page)
            result.append(frame_list.copy())
        
        # Display results
        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", "FIFO Page Replacement Results:\n\n")
        result_text.insert(tk.END, f"Page Reference String: {', '.join(map(str, references))}\n")
        result_text.insert(tk.END, f"Number of Frames: {frames}\n")
        result_text.insert(tk.END, f"Total Page Faults: {page_faults}\n\n")
        
        result_text.insert(tk.END, "Frame Status After Each Reference:\n")
        for i, frame_state in enumerate(result):
            result_text.insert(tk.END, f"Step {i+1}: {frame_state}\n")
        
    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")

def check_deadlock(process_names, resource_names, allocation_matrix, request_matrix, result_text):
    try:
        # Parse inputs
        processes = [p.strip() for p in process_names.split(',')]
        resources = [r.strip() for r in resource_names.split(',')]
        
        allocation = []
        for line in allocation_matrix.strip().split('\n'):
            allocation.append([int(x.strip()) for x in line.split(',')])
        
        request = []
        for line in request_matrix.strip().split('\n'):
            request.append([int(x.strip()) for x in line.split(',')])
        
        # Check for deadlock using RAG
        n = len(processes)
        work = [False] * n
        finish = [False] * n
        
        # Find a process that can be allocated resources
        while True:
            found = False
            for i in range(n):
                if not finish[i] and all(request[i][j] <= sum(row[j] for row in allocation) for j in range(len(resources))):
                    finish[i] = True
                    found = True
                    break
            if not found:
                break
        
        # Check if all processes can finish
        deadlock = not all(finish)
        
        # Display results
        result_text.delete("1.0", tk.END)
        if deadlock:
            result_text.insert("1.0", "Deadlock Detected!\n\n")
            result_text.insert(tk.END, "Processes involved in deadlock:\n")
            for i in range(n):
                if not finish[i]:
                    result_text.insert(tk.END, f"{processes[i]}\n")
        else:
            result_text.insert("1.0", "No Deadlock Detected\n")
            result_text.insert(tk.END, "All processes can complete successfully.\n")
        
    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")

def clear_fcfs_fields(process_names, arrival_times, burst_times, result_text):
    process_names.delete(0, tk.END)
    arrival_times.delete(0, tk.END)
    burst_times.delete(0, tk.END)
    result_text.delete("1.0", tk.END)

def clear_fifo_fields(page_references, num_frames, result_text):
    page_references.delete(0, tk.END)
    num_frames.delete(0, tk.END)
    result_text.delete("1.0", tk.END)

def clear_rag_fields(process_names, resource_names, allocation_matrix, request_matrix, result_text):
    process_names.delete(0, tk.END)
    resource_names.delete(0, tk.END)
    allocation_matrix.delete("1.0", tk.END)
    request_matrix.delete("1.0", tk.END)
    result_text.delete("1.0", tk.END)

def main():
    root = tk.Tk()
    user_store = SQLiteUserStore()
    app = LoginRegisterWindow(root, user_store)
    root.mainloop()

if __name__ == "__main__":
    main() 