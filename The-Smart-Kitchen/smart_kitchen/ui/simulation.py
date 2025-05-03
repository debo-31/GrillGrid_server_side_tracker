"""
Kitchen simulation components for visualizing kitchen workflows and resource utilization
"""
import tkinter as tk
from tkinter import ttk, messagebox
import time
import random
import sys
import os

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_kitchen.core.kitchen_algorithm import KitchenResourceManager
from smart_kitchen.data.kitchen_data import (
    STAFF_TYPES, EQUIPMENT_TYPES, STAFF_ICONS, EQUIPMENT_ICONS,
    KITCHEN_SCENARIOS, FOOD_TASKS, TASK_EQUIPMENT_NEEDS
)


class KitchenSimulation:
    """Simulates kitchen workflows and resource utilization"""
    
    def __init__(self, parent):
        """Initialize the kitchen simulation UI"""
        self.parent = parent
        
        # Initialize simulation variables
        self.running = False
        self.current_step = 0
        self.scenario = None
        self.kitchen_manager = None
        self.staff_names = []
        self.equipment_names = []
        self.staff_tasks = {}
        self.task_progress = {}
        self.deadlock_detected = False
        
        # Create UI components
        self.create_ui()
    
    def create_ui(self):
        """Create the simulation UI"""
        # Create header
        header_frame = ttk.Frame(self.parent)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text="Kitchen Workflow Simulation",
            font=("Helvetica", 16, "bold")
        ).pack(side=tk.LEFT, padx=10)
        
        # Create controls
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Scenario selection
        ttk.Label(controls_frame, text="Scenario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.scenario_var = tk.StringVar()
        scenario_combobox = ttk.Combobox(
            controls_frame,
            textvariable=self.scenario_var,
            values=list(KITCHEN_SCENARIOS.keys()),
            state="readonly",
            width=20
        )
        scenario_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        scenario_combobox.bind("<<ComboboxSelected>>", lambda _: self.load_scenario())
        
        # Simulation mode
        ttk.Label(controls_frame, text="Mode:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.mode_var = tk.StringVar(value="Normal")
        mode_combobox = ttk.Combobox(
            controls_frame,
            textvariable=self.mode_var,
            values=["Normal", "Deadlock Scenario", "Banker's Prevention"],
            state="readonly",
            width=20
        )
        mode_combobox.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Simulation speed
        ttk.Label(controls_frame, text="Speed:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(
            controls_frame,
            from_=0.5,
            to=2.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=100
        )
        speed_scale.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        # Simulation controls
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=0, column=6, padx=20, pady=5, sticky="e")
        
        self.start_button = ttk.Button(buttons_frame, text="Start", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(buttons_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        # Create simulation display
        self.simulation_frame = ttk.Frame(self.parent)
        self.simulation_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Split into left and right panels
        left_panel = ttk.Frame(self.simulation_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_panel = ttk.Frame(self.simulation_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Kitchen layout visual
        kitchen_frame = ttk.LabelFrame(left_panel, text="Kitchen Layout")
        kitchen_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.kitchen_canvas = tk.Canvas(kitchen_frame, bg="white", height=300)
        self.kitchen_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Staff activity display
        activity_frame = ttk.LabelFrame(right_panel, text="Staff Activity")
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Use a Treeview for staff activity
        self.activity_tree = ttk.Treeview(
            activity_frame,
            columns=("Staff", "Current Task", "Equipment", "Progress", "Status"),
            show="headings",
            height=10
        )
        
        # Configure columns
        self.activity_tree.heading("Staff", text="Staff")
        self.activity_tree.heading("Current Task", text="Current Task")
        self.activity_tree.heading("Equipment", text="Equipment")
        self.activity_tree.heading("Progress", text="Progress")
        self.activity_tree.heading("Status", text="Status")
        
        self.activity_tree.column("Staff", width=100)
        self.activity_tree.column("Current Task", width=150)
        self.activity_tree.column("Equipment", width=150)
        self.activity_tree.column("Progress", width=100)
        self.activity_tree.column("Status", width=100)
        
        self.activity_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Resource utilization
        utilization_frame = ttk.LabelFrame(right_panel, text="Resource Utilization")
        utilization_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.utilization_canvas = tk.Canvas(utilization_frame, bg="white", height=100)
        self.utilization_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status information
        status_frame = ttk.Frame(self.parent)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(status_frame, text="Simulation Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Helvetica", 10, "bold"))
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Simulation step and time
        time_frame = ttk.Frame(status_frame)
        time_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(time_frame, text="Step:").pack(side=tk.LEFT, padx=5)
        self.step_var = tk.StringVar(value="0")
        step_label = ttk.Label(time_frame, textvariable=self.step_var)
        step_label.pack(side=tk.LEFT, padx=5)
        
        # Set default scenario
        self.scenario_var.set("small_kitchen")
        self.load_scenario()
    
    def load_scenario(self):
        """Load the selected kitchen scenario"""
        scenario_key = self.scenario_var.get()
        if not scenario_key or scenario_key not in KITCHEN_SCENARIOS:
            return
            
        self.scenario = KITCHEN_SCENARIOS[scenario_key]
        
        # Set up staff and equipment
        self.staff_names = self.scenario["staff"]
        self.equipment_names = self.scenario["equipment"]
        
        # Set up resources
        available = self.scenario["available"].copy()
        max_resources = [row[:] for row in self.scenario["max_needs"]]
        allocated = [row[:] for row in self.scenario["allocated"]]
        
        # Initialize kitchen manager
        self.kitchen_manager = KitchenResourceManager(
            available,
            max_resources,
            allocated
        )
        
        # Initialize staff tasks
        self.staff_tasks = {}
        self.task_progress = {}
        
        for i, staff in enumerate(self.staff_names):
            # Assign random tasks from the staff's task list
            if staff in FOOD_TASKS:
                task = random.choice(FOOD_TASKS[staff])
                self.staff_tasks[staff] = task
                self.task_progress[staff] = 0
        
        # Reset simulation
        self.current_step = 0
        self.step_var.set(str(self.current_step))
        self.status_var.set("Ready")
        self.deadlock_detected = False
        
        # Update UI
        self.update_kitchen_display()
        self.update_activity_display()
        self.update_utilization_display()
    
    def start_simulation(self):
        """Start the kitchen simulation"""
        if not self.kitchen_manager:
            messagebox.showwarning("No Scenario", "Please select a kitchen scenario first.")
            return
            
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.status_var.set("Running")
        
        # Run the simulation
        self.simulate_step()
    
    def stop_simulation(self):
        """Stop the kitchen simulation"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.status_var.set("Paused")
    
    def reset_simulation(self):
        """Reset the kitchen simulation to initial state"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Reload the current scenario
        self.load_scenario()
        
        self.status_var.set("Reset")
    
    def simulate_step(self):
        """Simulate a single step in the kitchen workflow"""
        if not self.running:
            return
            
        # Increment step counter
        self.current_step += 1
        self.step_var.set(str(self.current_step))
        
        # Check for deadlock if not using Banker's prevention
        if self.mode_var.get() != "Banker's Prevention":
            if self.kitchen_manager.detect_deadlock():
                self.deadlock_detected = True
                self.status_var.set("Deadlock Detected!")
                messagebox.showwarning(
                    "Deadlock Detected",
                    "A deadlock has occurred in the kitchen!\n\n"
                    "Some staff members cannot complete their tasks because "
                    "they're waiting for equipment that won't be released."
                )
                self.stop_simulation()
                return
        
        # Process each staff member
        for staff in self.staff_names:
            # Skip if no task assigned
            if staff not in self.staff_tasks:
                continue
                
            current_task = self.staff_tasks[staff]
            staff_idx = self.staff_names.index(staff)
            
            # If task is complete, assign a new one
            if self.task_progress[staff] >= 100:
                # Release all equipment
                for j, equipment in enumerate(self.equipment_names):
                    if self.kitchen_manager.allocated[staff_idx][j] > 0:
                        release = [0] * len(self.equipment_names)
                        release[j] = self.kitchen_manager.allocated[staff_idx][j]
                        self.kitchen_manager.release_resources(staff_idx, release)
                
                # Assign new task
                if staff in FOOD_TASKS:
                    new_task = random.choice(FOOD_TASKS[staff])
                    self.staff_tasks[staff] = new_task
                    self.task_progress[staff] = 0
            
            # Otherwise, progress the current task if equipment is available
            else:
                # Check if all needed equipment is allocated
                needed_equipment = TASK_EQUIPMENT_NEEDS.get(current_task, [])
                has_all_equipment = True
                
                for equipment in needed_equipment:
                    if equipment in self.equipment_names:
                        equipment_idx = self.equipment_names.index(equipment)
                        if self.kitchen_manager.allocated[staff_idx][equipment_idx] == 0:
                            has_all_equipment = False
                            break
                
                # If staff has all needed equipment, progress the task
                if has_all_equipment:
                    # Progress by random amount (5-15%)
                    progress_increment = random.randint(5, 15)
                    self.task_progress[staff] = min(100, self.task_progress[staff] + progress_increment)
                # Otherwise, try to request needed equipment if using Banker's prevention
                elif self.mode_var.get() == "Banker's Prevention":
                    for equipment in needed_equipment:
                        if equipment in self.equipment_names:
                            equipment_idx = self.equipment_names.index(equipment)
                            
                            # Skip if already allocated
                            if self.kitchen_manager.allocated[staff_idx][equipment_idx] > 0:
                                continue
                                
                            # Request the equipment
                            request = [0] * len(self.equipment_names)
                            request[equipment_idx] = 1
                            
                            success, _ = self.kitchen_manager.request_resources(staff_idx, request)
                            # If request granted, update UI and break
                            if success:
                                break
        
        # Update displays
        self.update_kitchen_display()
        self.update_activity_display()
        self.update_utilization_display()
        
        # Schedule next step if still running
        if self.running:
            delay = int(1000 / self.speed_var.get())  # Adjust delay based on speed
            self.parent.after(delay, self.simulate_step)
    
    def update_kitchen_display(self):
        """Update the kitchen layout display"""
        # Clear canvas
        self.kitchen_canvas.delete("all")
        
        # Set dimensions
        canvas_width = self.kitchen_canvas.winfo_width()
        canvas_height = self.kitchen_canvas.winfo_height()
        
        if canvas_width < 50 or canvas_height < 50:  # Canvas not yet properly sized
            canvas_width = 400
            canvas_height = 300
        
        # Draw kitchen background
        self.kitchen_canvas.create_rectangle(
            10, 10, canvas_width-10, canvas_height-10,
            fill="#F5F5F5", outline="#BDBDBD", width=2
        )
        
        # Draw kitchen stations
        equipment_positions = {}
        y_offset = 40
        x_step = canvas_width / (len(self.equipment_names) + 1)
        
        for i, equipment in enumerate(self.equipment_names):
            x_pos = (i + 1) * x_step
            y_pos = y_offset
            
            # Store position for later reference
            equipment_positions[equipment] = (x_pos, y_pos)
            
            # Draw equipment icon
            icon = EQUIPMENT_ICONS.get(equipment, "🔧")
            self.kitchen_canvas.create_text(
                x_pos, y_pos,
                text=icon,
                font=("TkDefaultFont", 20)
            )
            
            # Draw equipment name
            self.kitchen_canvas.create_text(
                x_pos, y_pos + 25,
                text=equipment,
                font=("Helvetica", 8)
            )
            
            # Draw available count
            available_count = self.kitchen_manager.available[i]
            self.kitchen_canvas.create_text(
                x_pos, y_pos + 40,
                text=f"Available: {available_count}",
                font=("Helvetica", 8)
            )
        
        # Draw staff members
        staff_positions = {}
        y_offset = canvas_height - 60
        x_step = canvas_width / (len(self.staff_names) + 1)
        
        for i, staff in enumerate(self.staff_names):
            x_pos = (i + 1) * x_step
            y_pos = y_offset
            
            # Store position for later reference
            staff_positions[staff] = (x_pos, y_pos)
            
            # Draw staff icon
            icon = STAFF_ICONS.get(staff, "👤")
            self.kitchen_canvas.create_text(
                x_pos, y_pos,
                text=icon,
                font=("TkDefaultFont", 20)
            )
            
            # Draw staff name
            self.kitchen_canvas.create_text(
                x_pos, y_pos + 25,
                text=staff,
                font=("Helvetica", 8)
            )
            
            # Draw staff task if assigned
            if staff in self.staff_tasks:
                task = self.staff_tasks[staff]
                progress = self.task_progress[staff]
                
                # Draw task and progress
                self.kitchen_canvas.create_text(
                    x_pos, y_pos - 20,
                    text=task,
                    font=("Helvetica", 8)
                )
                
                # Draw progress bar
                bar_width = 60
                self.kitchen_canvas.create_rectangle(
                    x_pos - bar_width/2, y_pos - 10,
                    x_pos + bar_width/2, y_pos - 5,
                    fill="white", outline="black"
                )
                
                progress_width = bar_width * (progress / 100)
                self.kitchen_canvas.create_rectangle(
                    x_pos - bar_width/2, y_pos - 10,
                    x_pos - bar_width/2 + progress_width, y_pos - 5,
                    fill="#4CAF50", outline=""
                )
                
                # Draw lines to allocated equipment
                for equipment in TASK_EQUIPMENT_NEEDS.get(task, []):
                    if equipment in self.equipment_names:
                        equipment_idx = self.equipment_names.index(equipment)
                        staff_idx = self.staff_names.index(staff)
                        
                        if self.kitchen_manager.allocated[staff_idx][equipment_idx] > 0:
                            # Draw connection line
                            if equipment in equipment_positions:
                                equip_x, equip_y = equipment_positions[equipment]
                                
                                self.kitchen_canvas.create_line(
                                    x_pos, y_pos - 30,
                                    equip_x, equip_y + 50,
                                    fill="#673AB7", width=2,
                                    dash=(4, 2)
                                )
        
        # If deadlock detected, show warning
        if self.deadlock_detected:
            self.kitchen_canvas.create_rectangle(
                canvas_width/2 - 100, canvas_height/2 - 30,
                canvas_width/2 + 100, canvas_height/2 + 30,
                fill="#F44336", outline="black", width=2
            )
            
            self.kitchen_canvas.create_text(
                canvas_width/2, canvas_height/2,
                text="DEADLOCK DETECTED!",
                font=("Helvetica", 14, "bold"),
                fill="white"
            )
    
    def update_activity_display(self):
        """Update the staff activity display"""
        # Clear existing items
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
            
        # Add current activity for each staff
        for staff in self.staff_names:
            staff_idx = self.staff_names.index(staff)
            
            # Get current task
            task = self.staff_tasks.get(staff, "Idle")
            progress = self.task_progress.get(staff, 0)
            
            # Get equipment being used
            equipment_used = []
            for j, equipment in enumerate(self.equipment_names):
                if self.kitchen_manager.allocated[staff_idx][j] > 0:
                    equipment_used.append(equipment)
            
            equipment_str = ", ".join(equipment_used) if equipment_used else "None"
            
            # Determine status
            status = "Working"
            if progress >= 100:
                status = "Completed"
            elif not equipment_used and task != "Idle":
                status = "Waiting"
            elif self.deadlock_detected:
                status = "Deadlocked"
                
            # Add to tree
            self.activity_tree.insert(
                "", "end",
                values=(staff, task, equipment_str, f"{progress}%", status)
            )
    
    def update_utilization_display(self):
        """Update the resource utilization display"""
        # Clear canvas
        self.utilization_canvas.delete("all")
        
        # Set dimensions
        canvas_width = self.utilization_canvas.winfo_width()
        canvas_height = self.utilization_canvas.winfo_height()
        
        if canvas_width < 50 or canvas_height < 50:  # Canvas not yet properly sized
            canvas_width = 400
            canvas_height = 100
        
        # Draw title
        self.utilization_canvas.create_text(
            canvas_width/2, 15,
            text="Equipment Utilization",
            font=("Helvetica", 9, "bold")
        )
        
        # Draw utilization bars
        bar_height = 20
        y_offset = 40
        x_step = canvas_width / (len(self.equipment_names) + 1)
        
        for i, equipment in enumerate(self.equipment_names):
            x_pos = (i + 1) * x_step
            
            # Calculate utilization percentage
            total = self.kitchen_manager.available[i]
            for staff_idx in range(len(self.staff_names)):
                total += self.kitchen_manager.allocated[staff_idx][i]
                
            if total > 0:
                utilized = total - self.kitchen_manager.available[i]
                utilization_pct = (utilized / total) * 100
            else:
                utilization_pct = 0
                
            # Draw label
            self.utilization_canvas.create_text(
                x_pos, y_offset - 10,
                text=equipment,
                font=("Helvetica", 8)
            )
            
            # Draw bar background
            bar_width = 80
            self.utilization_canvas.create_rectangle(
                x_pos - bar_width/2, y_offset,
                x_pos + bar_width/2, y_offset + bar_height,
                fill="white", outline="black"
            )
            
            # Draw utilization bar
            utilized_width = bar_width * (utilization_pct / 100)
            self.utilization_canvas.create_rectangle(
                x_pos - bar_width/2, y_offset,
                x_pos - bar_width/2 + utilized_width, y_offset + bar_height,
                fill="#2196F3", outline=""
            )
            
            # Draw percentage
            self.utilization_canvas.create_text(
                x_pos, y_offset + bar_height/2,
                text=f"{int(utilization_pct)}%",
                font=("Helvetica", 8),
                fill="black"
            ) 