#!/usr/bin/env python3
"""
Smart Kitchen Resource Management System

A kitchen resource management application based on Banker's Algorithm
for preventing deadlocks in kitchen operations.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_kitchen.ui.main_application import SmartKitchenApp
from smart_kitchen.data.user_database import UserDatabase


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Kitchen - Login")
        self.root.geometry("500x400")
        self.root.configure(bg="#F5F7FA")
        
        # Initialize database
        self.db = UserDatabase()
        
        # Load saved credentials if they exist
        self.saved_credentials = self._load_saved_credentials()
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        title_label = ttk.Label(
            main_frame,
            text="Smart Kitchen Login",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create login tab
        self.login_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.login_tab, text="Login")
        
        # Create register tab
        self.register_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.register_tab, text="Register")
        
        # Create password reset tab
        self.reset_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reset_tab, text="Reset Password")
        
        # Setup all tabs
        self._setup_login_tab()
        self._setup_register_tab()
        self._setup_reset_tab()
        
        # Check for saved credentials
        if self.saved_credentials:
            self._try_auto_login()
    
    def _load_saved_credentials(self):
        """Load saved credentials from file"""
        cred_file = Path.home() / ".smart_kitchen_credentials"
        if cred_file.exists():
            try:
                with open(cred_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _save_credentials(self, username, token):
        """Save credentials to file"""
        cred_file = Path.home() / ".smart_kitchen_credentials"
        with open(cred_file, 'w') as f:
            json.dump({'username': username, 'token': token}, f)
    
    def _clear_saved_credentials(self):
        """Clear saved credentials"""
        cred_file = Path.home() / ".smart_kitchen_credentials"
        if cred_file.exists():
            cred_file.unlink()
    
    def _try_auto_login(self):
        """Attempt automatic login with saved credentials"""
        if self.saved_credentials:
            user = self.db.verify_remember_token(
                self.saved_credentials['username'],
                self.saved_credentials['token']
            )
            if user:
                self._launch_main_app(user)
    
    def _setup_login_tab(self):
        """Setup the login tab"""
        form_frame = ttk.Frame(self.login_tab)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Username
        ttk.Label(form_frame, text="Username:", font=("Helvetica", 12)).pack(pady=5)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.pack(pady=5)
        
        # Password
        ttk.Label(form_frame, text="Password:", font=("Helvetica", 12)).pack(pady=5)
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.pack(pady=5)
        
        # Remember me checkbox
        self.remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            form_frame,
            text="Remember me",
            variable=self.remember_var
        ).pack(pady=5)
        
        # Login button
        login_button = ttk.Button(
            form_frame,
            text="Login",
            command=self.authenticate,
            style="Accent.TButton"
        )
        login_button.pack(pady=20)
        
        # Configure style for accent button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Helvetica", 12))
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.authenticate())
        
        # Set focus to username entry
        self.username_entry.focus()
    
    def _setup_register_tab(self):
        """Setup the registration tab"""
        form_frame = ttk.Frame(self.register_tab)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Username
        ttk.Label(form_frame, text="Username:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_username_entry = ttk.Entry(form_frame, width=30)
        self.reg_username_entry.pack(pady=5)
        
        # Email
        ttk.Label(form_frame, text="Email:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_email_entry = ttk.Entry(form_frame, width=30)
        self.reg_email_entry.pack(pady=5)
        
        # Password
        ttk.Label(form_frame, text="Password:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.reg_password_entry.pack(pady=5)
        
        # Confirm Password
        ttk.Label(form_frame, text="Confirm Password:", font=("Helvetica", 12)).pack(pady=5)
        self.reg_confirm_entry = ttk.Entry(form_frame, width=30, show="*")
        self.reg_confirm_entry.pack(pady=5)
        
        # Role selection
        ttk.Label(form_frame, text="Role:", font=("Helvetica", 12)).pack(pady=5)
        self.role_var = tk.StringVar(value="user")
        role_frame = ttk.Frame(form_frame)
        role_frame.pack(pady=5)
        ttk.Radiobutton(role_frame, text="User", variable=self.role_var, value="user").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(role_frame, text="Admin", variable=self.role_var, value="admin").pack(side=tk.LEFT, padx=5)
        
        # Register button
        ttk.Button(
            form_frame,
            text="Register",
            command=self.register,
            style="Accent.TButton"
        ).pack(pady=20)
    
    def _setup_reset_tab(self):
        """Setup the password reset tab"""
        form_frame = ttk.Frame(self.reset_tab)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Email
        ttk.Label(form_frame, text="Email:", font=("Helvetica", 12)).pack(pady=5)
        self.reset_email_entry = ttk.Entry(form_frame, width=30)
        self.reset_email_entry.pack(pady=5)
        
        # Reset button
        ttk.Button(
            form_frame,
            text="Request Reset Link",
            command=self.request_password_reset,
            style="Accent.TButton"
        ).pack(pady=20)
        
        # Reset token entry
        ttk.Label(form_frame, text="Reset Token:", font=("Helvetica", 12)).pack(pady=5)
        self.reset_token_entry = ttk.Entry(form_frame, width=30)
        self.reset_token_entry.pack(pady=5)
        
        # New password
        ttk.Label(form_frame, text="New Password:", font=("Helvetica", 12)).pack(pady=5)
        self.reset_password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.reset_password_entry.pack(pady=5)
        
        # Reset password button
        ttk.Button(
            form_frame,
            text="Reset Password",
            command=self.reset_password,
            style="Accent.TButton"
        ).pack(pady=20)
    
    def authenticate(self):
        """Authenticate user"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        remember = self.remember_var.get()
        
        user = self.db.authenticate_user(username, password, remember)
        
        if user:
            if remember and 'remember_token' in user:
                self._save_credentials(username, user['remember_token'])
            self._launch_main_app(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def register(self):
        """Register new user"""
        username = self.reg_username_entry.get()
        email = self.reg_email_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        role = self.role_var.get()
        
        if not all([username, email, password, confirm]):
            messagebox.showerror("Error", "All fields are required")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if self.db.create_user(username, password, role, email):
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.notebook.select(0)  # Switch to login tab
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.username_entry.insert(0, username)
            self.password_entry.focus()
        else:
            messagebox.showerror("Error", "Username or email already exists")
    
    def request_password_reset(self):
        """Request password reset"""
        email = self.reset_email_entry.get()
        if not email:
            messagebox.showerror("Error", "Please enter your email")
            return
        
        token = self.db.request_password_reset(email)
        if token:
            messagebox.showinfo(
                "Reset Link Sent",
                f"Password reset token: {token}\n"
                "Please use this token to reset your password."
            )
        else:
            messagebox.showerror("Error", "Email not found in our system")
    
    def reset_password(self):
        """Reset password using token"""
        token = self.reset_token_entry.get()
        new_password = self.reset_password_entry.get()
        
        if not all([token, new_password]):
            messagebox.showerror("Error", "Please enter both token and new password")
            return
        
        if self.db.reset_password(token, new_password):
            messagebox.showinfo("Success", "Password reset successful! Please login.")
            self.notebook.select(0)  # Switch to login tab
        else:
            messagebox.showerror("Error", "Invalid or expired token")
    
    def _launch_main_app(self, user):
        """Launch the main application"""
        self.root.destroy()
        root = tk.Tk()
        app = SmartKitchenApp(root, user)
        root.mainloop()


def main():
    """Start the Smart Kitchen application"""
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main() 