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
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )''')
            conn.commit()

    def add_user(self, username, password, email, role):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                               (username, password, role, email))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate(self, username, password):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email, role FROM users WHERE username = ? AND password = ?', (username, password))
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
        self.root.title("Login/Register")
        self.root.geometry("900x600")
        maximize_window(self.root)
        self.root.resizable(True, True)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.login_tab = ttk.Frame(self.notebook)
        self.register_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.login_tab, text="Login")
        self.notebook.add(self.register_tab, text="Register")

        self._setup_login_tab()
        self._setup_register_tab()

    def _setup_login_tab(self):
        frame = ttk.Frame(self.login_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:").pack(pady=5)
        self.login_username = ttk.Entry(frame)
        self.login_username.pack(pady=5)

        ttk.Label(frame, text="Password:").pack(pady=5)
        self.login_password = ttk.Entry(frame, show="*")
        self.login_password.pack(pady=5)

        ttk.Button(frame, text="Login", command=self.login).pack(pady=15)

    def _setup_register_tab(self):
        frame = ttk.Frame(self.register_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:").pack(pady=5)
        self.reg_username = ttk.Entry(frame)
        self.reg_username.pack(pady=5)

        ttk.Label(frame, text="Email:").pack(pady=5)
        self.reg_email = ttk.Entry(frame)
        self.reg_email.pack(pady=5)

        ttk.Label(frame, text="Password:").pack(pady=5)
        self.reg_password = ttk.Entry(frame, show="*")
        self.reg_password.pack(pady=5)

        ttk.Label(frame, text="Confirm Password:").pack(pady=5)
        self.reg_confirm = ttk.Entry(frame, show="*")
        self.reg_confirm.pack(pady=5)

        ttk.Label(frame, text="Role:").pack(pady=5)
        self.role_var = tk.StringVar(value="user")
        role_frame = ttk.Frame(frame)
        role_frame.pack(pady=5)
        ttk.Radiobutton(role_frame, text="User", variable=self.role_var, value="user").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(role_frame, text="Admin", variable=self.role_var, value="admin").pack(side=tk.LEFT, padx=5)

        ttk.Button(frame, text="Register", command=self.register).pack(pady=15)

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
        # Fallback: show a simple message if SmartKitchenApp is not available
        main_root = tk.Tk()
        main_root.title("Main Application")
        main_root.geometry("1200x800")
        ttk.Label(main_root, text=f"Welcome, {username}! (SmartKitchenApp not found)", font=("Helvetica", 16)).pack(pady=20)
        main_root.mainloop()

class UserManager:
    def __init__(self, parent, user_store, current_user):
        self.user_store = user_store
        self.current_user = current_user
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.user_list = tk.Listbox(self.frame, height=10)
        self.user_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.user_list.yview)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.user_list.config(yscrollcommand=self.scrollbar.set)
        self._populate_users()

        # Role and delete controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(control_frame, text="Change Role:").pack(pady=5)
        self.role_var = tk.StringVar(value="user")
        ttk.Radiobutton(control_frame, text="User", variable=self.role_var, value="user").pack(anchor="w")
        ttk.Radiobutton(control_frame, text="Admin", variable=self.role_var, value="admin").pack(anchor="w")
        ttk.Button(control_frame, text="Apply Role", command=self.change_role).pack(pady=10)
        ttk.Button(control_frame, text="Delete User", command=self.delete_user).pack(pady=10)

    def _populate_users(self):
        self.user_list.delete(0, tk.END)
        for user in self.user_store.get_all_users():
            self.user_list.insert(tk.END, user)

    def change_role(self):
        selection = self.user_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a user to change role.")
            return
        username = self.user_list.get(selection[0])
        if username == self.current_user:
            messagebox.showerror("Error", "You cannot change your own role.")
            return
        role = self.role_var.get()
        if self.user_store.set_role(username, role):
            messagebox.showinfo("Success", f"Role for {username} set to {role}.")
        else:
            messagebox.showerror("Error", "Failed to change role.")

    def delete_user(self):
        selection = self.user_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a user to delete.")
            return
        username = self.user_list.get(selection[0])
        if username == self.current_user:
            messagebox.showerror("Error", "You cannot delete your own account.")
            return
        if self.user_store.delete_user(username):
            messagebox.showinfo("Success", f"User {username} deleted.")
            self._populate_users()
        else:
            messagebox.showerror("Error", "Failed to delete user.")

if __name__ == "__main__":
    user_store = SQLiteUserStore()
    root = tk.Tk()
    app = LoginRegisterWindow(root, user_store)
    root.mainloop() 