"""
Visualization components for the Smart Kitchen system
"""
import tkinter as tk
from tkinter import ttk, Toplevel
import time
import math
import sys
import os

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_kitchen.data.kitchen_data import STAFF_ICONS, EQUIPMENT_ICONS


class KitchenVisualization:
    """Kitchen visualization utilities"""
    
    # Colors for different states
    SAFE_COLOR = "#4CAF50"  # Green
    UNSAFE_COLOR = "#F44336"  # Red
    NEUTRAL_COLOR = "#2196F3"  # Blue
    
    # Colors for resource matrix
    MATRIX_HEADER_BG = "#1976D2"  # Dark blue
    MATRIX_HEADER_FG = "#FFFFFF"  # White
    MATRIX_STAFF_BG = "#2196F3"   # Light blue
    MATRIX_STAFF_FG = "#FFFFFF"   # White
    MATRIX_MAX_BG = "#E3F2FD"     # Very light blue
    MATRIX_ALLOC_BG = "#E8F5E9"   # Very light green
    MATRIX_NEED_BG = "#FFF8E1"    # Very light yellow
    MATRIX_AVAIL_BG = "#F5F5F5"   # Light gray
    
    @staticmethod
    def draw_kitchen(canvas, staff_names, equipment_names, available, allocated):
        """Draw a kitchen visualization on the canvas"""
        # Clear canvas
        canvas.delete("all")
        
        # Set dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width < 50 or canvas_height < 50:  # Canvas not yet properly sized
            canvas_width = 500
            canvas_height = 300
        
        # Draw kitchen background
        canvas.create_rectangle(
            10, 10, canvas_width-10, canvas_height-10,
            fill="#F5F5F5", outline="#BDBDBD", width=2
        )
        
        # Draw staff section
        staff_area_width = canvas_width / 3
        canvas.create_rectangle(
            20, 20, staff_area_width-10, canvas_height-20,
            fill="#E3F2FD", outline="#90CAF9", width=1
        )
        canvas.create_text(
            staff_area_width/2, 35,
            text="KITCHEN STAFF",
            font=("Helvetica", 12, "bold")
        )
        
        # Draw equipment section
        equipment_area_left = staff_area_width
        equipment_area_width = canvas_width - staff_area_width
        canvas.create_rectangle(
            equipment_area_left, 20, canvas_width-20, canvas_height-20,
            fill="#FFF8E1", outline="#FFECB3", width=1
        )
        canvas.create_text(
            equipment_area_left + equipment_area_width/2, 35,
            text="KITCHEN EQUIPMENT",
            font=("Helvetica", 12, "bold")
        )
        
        # Draw staff
        staff_y_start = 70
        staff_height = min(40, (canvas_height - 100) / max(len(staff_names), 1))
        for i, staff_name in enumerate(staff_names):
            y_pos = staff_y_start + i * staff_height * 1.5
            
            # Staff icon
            icon = STAFF_ICONS.get(staff_name, "👤")
            canvas.create_text(
                40, y_pos,
                text=icon,
                font=("TkDefaultFont", 16)
            )
            
            # Staff name
            canvas.create_text(
                120, y_pos,
                text=staff_name,
                font=("Helvetica", 10),
                anchor="w"
            )
        
        # Draw equipment
        equipment_y_start = 70
        equipment_height = min(40, (canvas_height - 100) / max(len(equipment_names), 1))
        equipment_x = equipment_area_left + 40
        
        for i, equipment_name in enumerate(equipment_names):
            y_pos = equipment_y_start + i * equipment_height * 1.5
            
            # Equipment icon
            icon = EQUIPMENT_ICONS.get(equipment_name, "🔧")
            canvas.create_text(
                equipment_x, y_pos,
                text=icon,
                font=("TkDefaultFont", 16)
            )
            
            # Equipment name and count
            canvas.create_text(
                equipment_x + 80, y_pos,
                text=f"{equipment_name} (Available: {available[i]})",
                font=("Helvetica", 10),
                anchor="w"
            )
        
        # Draw allocation lines
        for i, staff_name in enumerate(staff_names):
            staff_y = staff_y_start + i * staff_height * 1.5
            
            for j, equipment_name in enumerate(equipment_names):
                if allocated[i][j] > 0:
                    equipment_y = equipment_y_start + j * equipment_height * 1.5
                    
                    # Draw line from staff to equipment
                    canvas.create_line(
                        staff_area_width-20, staff_y,
                        equipment_x - 20, equipment_y,
                        fill="#673AB7", width=2,
                        dash=(4, 2)
                    )
                    
                    # Show allocation count
                    canvas.create_oval(
                        equipment_area_left - 15, equipment_y - 10,
                        equipment_area_left - 5, equipment_y + 10,
                        fill="#673AB7", outline=""
                    )
                    canvas.create_text(
                        equipment_area_left - 10, equipment_y,
                        text=str(allocated[i][j]),
                        fill="white",
                        font=("Helvetica", 8, "bold")
                    )
    
    @staticmethod
    def update_resource_matrix(canvas, staff_names, equipment_names, available, max_resources, allocated, need):
        """Update the resource matrix display on the canvas with improved visualization"""
        # Clear canvas
        canvas.delete("all")
        
        # Set dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width < 50 or canvas_height < 50:  # Canvas not yet properly sized
            canvas_width = 500
            canvas_height = 300
        
        # Add title
        canvas.create_text(
            canvas_width/2, 15,
            text="Kitchen Resource Matrix",
            font=("Helvetica", 14, "bold"),
            fill="#1565C0"
        )
        
        # Calculate cell dimensions
        padding = 20
        num_rows = len(staff_names) + 2  # +1 for header, +1 for available row
        num_cols = len(equipment_names) + 1  # +1 for staff names column
        
        total_width = canvas_width - 2 * padding
        total_height = canvas_height - 40  # Leave space for title and padding
        
        cell_width = total_width / num_cols
        cell_height = total_height / num_rows
        
        # Draw the matrix header (equipment names)
        # First cell (empty corner)
        canvas.create_rectangle(
            padding, 40,
            padding + cell_width, 40 + cell_height,
            fill=KitchenVisualization.MATRIX_HEADER_BG,
            outline="white",
            width=2
        )
        
        canvas.create_text(
            padding + cell_width/2, 40 + cell_height/2,
            text="Staff / Equipment",
            font=("Helvetica", 9, "bold"),
            fill=KitchenVisualization.MATRIX_HEADER_FG
        )
        
        # Draw equipment names in header
        for j, equipment in enumerate(equipment_names):
            x = padding + (j+1) * cell_width
            y = 40
            
            # Equipment cell
            canvas.create_rectangle(
                x, y,
                x + cell_width, y + cell_height,
                fill=KitchenVisualization.MATRIX_HEADER_BG,
                outline="white",
                width=2
            )
            
            # Equipment name with icon
            icon = EQUIPMENT_ICONS.get(equipment, "🔧")
            canvas.create_text(
                x + cell_width/2, y + cell_height/3,
                text=icon,
                font=("TkDefaultFont", 12)
            )
            
            canvas.create_text(
                x + cell_width/2, y + cell_height * 2/3,
                text=equipment,
                font=("Helvetica", 9, "bold"),
                fill=KitchenVisualization.MATRIX_HEADER_FG
            )
        
        # Draw staff rows
        for i, staff in enumerate(staff_names):
            y = 40 + (i+1) * cell_height
            
            # Staff name cell
            canvas.create_rectangle(
                padding, y,
                padding + cell_width, y + cell_height,
                fill=KitchenVisualization.MATRIX_STAFF_BG,
                outline="white",
                width=2
            )
            
            # Staff name with icon
            icon = STAFF_ICONS.get(staff, "👤")
            staff_text = f"{icon} {staff}"
            
            canvas.create_text(
                padding + cell_width/2, y + cell_height/2,
                text=staff_text,
                font=("Helvetica", 9, "bold"),
                fill=KitchenVisualization.MATRIX_STAFF_FG
            )
            
            # Draw allocation cells
            for j, equipment in enumerate(equipment_names):
                x = padding + (j+1) * cell_width
                
                # Create cell background
                canvas.create_rectangle(
                    x, y,
                    x + cell_width, y + cell_height,
                    fill="#FFFFFF",
                    outline="#E0E0E0",
                    width=1
                )
                
                # Add allocation info
                max_val = max_resources[i][j]
                allocated_val = allocated[i][j]
                need_val = need[i][j]
                
                # Split the cell into 3 parts
                third_width = cell_width / 3
                
                # Max box (left third)
                canvas.create_rectangle(
                    x, y,
                    x + third_width, y + cell_height,
                    fill=KitchenVisualization.MATRIX_MAX_BG,
                    outline="#E0E0E0",
                    width=1
                )
                
                # Allocation box (middle third)
                canvas.create_rectangle(
                    x + third_width, y,
                    x + 2*third_width, y + cell_height,
                    fill=KitchenVisualization.MATRIX_ALLOC_BG,
                    outline="#E0E0E0",
                    width=1
                )
                
                # Need box (right third)
                canvas.create_rectangle(
                    x + 2*third_width, y,
                    x + 3*third_width, y + cell_height,
                    fill=KitchenVisualization.MATRIX_NEED_BG,
                    outline="#E0E0E0",
                    width=1
                )
                
                # Display the values
                # Max
                canvas.create_text(
                    x + third_width/2, y + cell_height/2,
                    text=str(max_val),
                    font=("Helvetica", 9, "bold")
                )
                
                # Allocated
                canvas.create_text(
                    x + third_width + third_width/2, y + cell_height/2,
                    text=str(allocated_val),
                    font=("Helvetica", 9, "bold")
                )
                
                # Need
                canvas.create_text(
                    x + 2*third_width + third_width/2, y + cell_height/2,
                    text=str(need_val),
                    font=("Helvetica", 9, "bold")
                )
        
        # Draw available resources row
        y = 40 + (len(staff_names) + 1) * cell_height
        
        # Available header cell
        canvas.create_rectangle(
            padding, y,
            padding + cell_width, y + cell_height,
            fill=KitchenVisualization.MATRIX_HEADER_BG,
            outline="white",
            width=2
        )
        
        canvas.create_text(
            padding + cell_width/2, y + cell_height/2,
            text="Available",
            font=("Helvetica", 9, "bold"),
            fill=KitchenVisualization.MATRIX_HEADER_FG
        )
        
        # Available values
        for j, equipment in enumerate(equipment_names):
            x = padding + (j+1) * cell_width
            
            canvas.create_rectangle(
                x, y,
                x + cell_width, y + cell_height,
                fill=KitchenVisualization.MATRIX_AVAIL_BG,
                outline="#E0E0E0",
                width=1
            )
            
            canvas.create_text(
                x + cell_width/2, y + cell_height/2,
                text=str(available[j]),
                font=("Helvetica", 10, "bold"),
                fill="#1565C0"
            )
        
        # Add legend
        legend_y = y + cell_height + 10
        legend_text = "Legend: Max | Allocated | Need"
        canvas.create_text(
            padding + cell_width, legend_y,
            text=legend_text,
            font=("Helvetica", 9),
            fill="#757575",
            anchor="w"
        )
        
        # Add color samples
        color_width = 15
        color_height = 10
        color_spacing = 5
        
        # Max color
        x_offset = padding + cell_width + len(legend_text)*4 + 20
        canvas.create_rectangle(
            x_offset, legend_y - color_height/2,
            x_offset + color_width, legend_y + color_height/2,
            fill=KitchenVisualization.MATRIX_MAX_BG,
            outline="#BDBDBD"
        )
        canvas.create_text(
            x_offset + color_width + color_spacing, legend_y,
            text="Max",
            font=("Helvetica", 8),
            fill="#757575",
            anchor="w"
        )
        
        # Allocated color
        x_offset += color_width + color_spacing + 30
        canvas.create_rectangle(
            x_offset, legend_y - color_height/2,
            x_offset + color_width, legend_y + color_height/2,
            fill=KitchenVisualization.MATRIX_ALLOC_BG,
            outline="#BDBDBD"
        )
        canvas.create_text(
            x_offset + color_width + color_spacing, legend_y,
            text="Allocated",
            font=("Helvetica", 8),
            fill="#757575",
            anchor="w"
        )
        
        # Need color
        x_offset += color_width + color_spacing + 60
        canvas.create_rectangle(
            x_offset, legend_y - color_height/2,
            x_offset + color_width, legend_y + color_height/2,
            fill=KitchenVisualization.MATRIX_NEED_BG,
            outline="#BDBDBD"
        )
        canvas.create_text(
            x_offset + color_width + color_spacing, legend_y,
            text="Need",
            font=("Helvetica", 8),
            fill="#757575",
            anchor="w"
        )
        
        # Available color
        x_offset += color_width + color_spacing + 40
        canvas.create_rectangle(
            x_offset, legend_y - color_height/2,
            x_offset + color_width, legend_y + color_height/2,
            fill=KitchenVisualization.MATRIX_AVAIL_BG,
            outline="#BDBDBD"
        )
        canvas.create_text(
            x_offset + color_width + color_spacing, legend_y,
            text="Available",
            font=("Helvetica", 8),
            fill="#757575",
            anchor="w"
        )
    
    @staticmethod
    def create_resource_matrix_detail_window(parent, staff_names, equipment_names, available, max_resources, allocated, need):
        """Create a detailed resource matrix window"""
        detail_window = Toplevel(parent)
        detail_window.title("Detailed Kitchen Resource Matrix")
        detail_window.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(detail_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        ttk.Label(
            main_frame,
            text="Kitchen Resource Matrix - Detailed View",
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)
        
        # Add description
        description = ttk.Label(
            main_frame,
            text="This matrix shows the allocation of kitchen equipment among staff members.\n"
                 "Each cell shows Max, Allocated, and Need values for each staff-equipment pair.",
            wraplength=700,
            justify="center"
        )
        description.pack(pady=5)
        
        # Create matrix frame
        matrix_frame = ttk.Frame(main_frame)
        matrix_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create matrix headers
        ttk.Label(matrix_frame, text="Staff", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        
        # Equipment headers
        for j, equipment in enumerate(equipment_names):
            icon = EQUIPMENT_ICONS.get(equipment, "🔧")
            header_frame = ttk.Frame(matrix_frame)
            header_frame.grid(row=0, column=j+1, padx=5, pady=5)
            
            ttk.Label(header_frame, text=icon, font=("TkDefaultFont", 12)).pack()
            ttk.Label(header_frame, text=equipment, font=("Helvetica", 9, "bold")).pack()
        
        # Create staff rows
        for i, staff in enumerate(staff_names):
            # Staff name cell
            icon = STAFF_ICONS.get(staff, "👤")
            staff_frame = ttk.Frame(matrix_frame)
            staff_frame.grid(row=i+1, column=0, padx=5, pady=5, sticky="w")
            
            ttk.Label(staff_frame, text=icon, font=("TkDefaultFont", 12)).pack(side=tk.LEFT)
            ttk.Label(staff_frame, text=staff, font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
            
            # Resource cells
            for j, equipment in enumerate(equipment_names):
                cell_frame = ttk.Frame(matrix_frame, padding=3)
                cell_frame.grid(row=i+1, column=j+1, padx=5, pady=5)
                
                # Background color for cell
                cell_style = ttk.Style()
                cell_style.configure("Cell.TFrame", background="#F5F5F5")
                cell_frame.configure(style="Cell.TFrame")
                
                # Add Max value
                max_label = ttk.Label(
                    cell_frame,
                    text=f"Max: {max_resources[i][j]}",
                    font=("Helvetica", 9),
                    background=KitchenVisualization.MATRIX_MAX_BG,
                    padding=(3, 1)
                )
                max_label.pack(fill=tk.X)
                
                # Add Allocated value
                allocated_label = ttk.Label(
                    cell_frame,
                    text=f"Allocated: {allocated[i][j]}",
                    font=("Helvetica", 9),
                    background=KitchenVisualization.MATRIX_ALLOC_BG,
                    padding=(3, 1)
                )
                allocated_label.pack(fill=tk.X)
                
                # Add Need value
                need_label = ttk.Label(
                    cell_frame,
                    text=f"Need: {need[i][j]}",
                    font=("Helvetica", 9),
                    background=KitchenVisualization.MATRIX_NEED_BG,
                    padding=(3, 1)
                )
                need_label.pack(fill=tk.X)
        
        # Add available resources row
        ttk.Label(
            matrix_frame,
            text="Available",
            font=("Helvetica", 10, "bold")
        ).grid(row=len(staff_names)+1, column=0, padx=5, pady=5, sticky="w")
        
        for j, equipment in enumerate(equipment_names):
            avail_frame = ttk.Frame(matrix_frame)
            avail_frame.grid(row=len(staff_names)+1, column=j+1, padx=5, pady=5)
            
            avail_label = ttk.Label(
                avail_frame,
                text=str(available[j]),
                font=("Helvetica", 10, "bold"),
                background=KitchenVisualization.MATRIX_AVAIL_BG,
                padding=(10, 5)
            )
            avail_label.pack()
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Add close button
        ttk.Button(
            button_frame,
            text="Close",
            command=detail_window.destroy
        ).pack()
    
    @staticmethod
    def show_safe_sequence(parent, staff_names, equipment_names, sequence, max_resources, allocated, need, available):
        """Show a visualization of the safe sequence"""
        # Create a new window
        sequence_window = Toplevel(parent)
        sequence_window.title("Safe Sequence Visualization")
        sequence_window.geometry("800x600")
        
        # Create frame for sequence display
        sequence_frame = ttk.Frame(sequence_window, padding=10)
        sequence_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        ttk.Label(
            sequence_frame,
            text="Safe Kitchen Operation Sequence",
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)
        
        # Create sequence visualization
        canvas = tk.Canvas(sequence_frame, bg="white", height=400)
        canvas.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Start animation button
        ttk.Button(
            sequence_frame,
            text="Start Animation",
            command=lambda: KitchenVisualization._animate_sequence(
                canvas, staff_names, equipment_names, sequence,
                max_resources, allocated, need, available
            )
        ).pack(pady=10)
        
        # Explanation text
        explanation = ttk.Label(
            sequence_frame,
            text="This visualization shows the safe sequence of kitchen operations that prevents deadlock.\n"
                 "Each staff member completes their tasks and releases equipment in a sequence that ensures\n"
                 "no staff member will be waiting indefinitely for equipment.",
            justify="center",
            wraplength=700
        )
        explanation.pack(pady=10)
    
    @staticmethod
    def _animate_sequence(canvas, staff_names, equipment_names, sequence, max_resources, allocated, need, available):
        """Animate the execution of a safe sequence"""
        # Clear canvas
        canvas.delete("all")
        
        # Set dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # Draw timeline
        timeline_y = 50
        canvas.create_line(50, timeline_y, canvas_width-50, timeline_y, width=2, arrow=tk.LAST)
        canvas.create_text(canvas_width-40, timeline_y, text="Time", font=("Helvetica", 10))
        
        # Draw sequence title
        sequence_str = " → ".join([staff_names[i] for i in sequence])
        canvas.create_text(canvas_width/2, 20, text=f"Safe Sequence: {sequence_str}", font=("Helvetica", 12, "bold"))
        
        # Calculate timeline segments
        segment_width = (canvas_width - 100) / len(sequence)
        
        # Create work vector (available resources)
        work = available.copy()
        
        # Create finish vector
        finish = [False] * len(staff_names)
        
        # Schedule animation
        canvas.after(100, lambda: KitchenVisualization._animate_sequence_step(
            canvas, 0, staff_names, equipment_names, sequence,
            max_resources, allocated, need, work, finish,
            timeline_y, segment_width
        ))
    
    @staticmethod
    def _animate_sequence_step(canvas, step, staff_names, equipment_names, sequence,
                              max_resources, allocated, need, work, finish,
                              timeline_y, segment_width):
        """Animate a single step in the safe sequence"""
        if step >= len(sequence):
            # Animation complete
            canvas.create_text(
                canvas.winfo_width()/2, canvas.winfo_height()-20,
                text="All kitchen tasks completed successfully without deadlock!",
                font=("Helvetica", 12, "bold"),
                fill=KitchenVisualization.SAFE_COLOR
            )
            return
            
        # Get the staff index for this step
        staff_idx = sequence[step]
        staff_name = staff_names[staff_idx]
        
        # Calculate position on timeline
        x_pos = 50 + (step + 0.5) * segment_width
        
        # Draw staff icon
        icon = STAFF_ICONS.get(staff_name, "👤")
        canvas.create_text(x_pos, timeline_y-20, text=icon, font=("TkDefaultFont", 16))
        
        # Draw step marker
        canvas.create_oval(x_pos-5, timeline_y-5, x_pos+5, timeline_y+5, fill=KitchenVisualization.NEUTRAL_COLOR)
        canvas.create_text(x_pos, timeline_y+20, text=staff_name, font=("Helvetica", 10))
        
        # Draw resource changes
        y_start = timeline_y + 40
        
        canvas.create_text(
            x_pos, y_start,
            text=f"Step {step+1}: {staff_name} completes task",
            font=("Helvetica", 10, "bold")
        )
        
        # Show allocated resources that will be released
        y_pos = y_start + 20
        canvas.create_text(
            x_pos, y_pos,
            text=f"Releasing equipment:",
            font=("Helvetica", 9)
        )
        
        for j, equipment in enumerate(equipment_names):
            if allocated[staff_idx][j] > 0:
                y_pos += 15
                icon = EQUIPMENT_ICONS.get(equipment, "🔧")
                canvas.create_text(
                    x_pos, y_pos,
                    text=f"{icon} {equipment} ({allocated[staff_idx][j]})",
                    font=("Helvetica", 8)
                )
                
        # Update work vector
        for j in range(len(equipment_names)):
            work[j] += allocated[staff_idx][j]
        
        # Mark process as finished
        finish[staff_idx] = True
        
        # Show available resources after this step
        y_pos += 30
        canvas.create_text(
            x_pos, y_pos,
            text="Available equipment:",
            font=("Helvetica", 9)
        )
        
        for j, equipment in enumerate(equipment_names):
            y_pos += 15
            icon = EQUIPMENT_ICONS.get(equipment, "🔧")
            canvas.create_text(
                x_pos, y_pos,
                text=f"{icon} {equipment} ({work[j]})",
                font=("Helvetica", 8)
            )
        
        # Schedule next step
        canvas.after(1500, lambda: KitchenVisualization._animate_sequence_step(
            canvas, step+1, staff_names, equipment_names, sequence,
            max_resources, allocated, need, work, finish,
            timeline_y, segment_width
        ))


def create_resource_allocation_canvas(parent):
    """Create a canvas for resource allocation matrix display"""
    canvas = tk.Canvas(parent, bg="white", height=200)
    canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    return canvas