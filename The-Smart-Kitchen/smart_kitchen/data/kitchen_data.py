"""
Kitchen data module containing predefined staff types, equipment, and kitchen scenarios.
"""

# Define kitchen staff roles
STAFF_TYPES = [
    "Head Chef",
    "Sous Chef",
    "Pastry Chef",
    "Line Cook",
    "Prep Cook",
    "Kitchen Assistant"
]

# Define kitchen equipment types
EQUIPMENT_TYPES = [
    "Oven",
    "Stove",
    "Mixer",
    "Cutting Board",
    "Knife Set",
    "Food Processor"
]

# Define staff icons for visualization
STAFF_ICONS = {
    "Head Chef": "👨‍🍳",
    "Sous Chef": "👩‍🍳",
    "Pastry Chef": "🧁",
    "Line Cook": "🍲",
    "Prep Cook": "🔪",
    "Kitchen Assistant": "🧑‍🍳"
}

# Define equipment icons for visualization
EQUIPMENT_ICONS = {
    "Oven": "🔥",
    "Stove": "🍳",
    "Mixer": "🥣",
    "Cutting Board": "🪓",
    "Knife Set": "🔪",
    "Food Processor": "⚙️"
}

# Predefined kitchen scenarios
KITCHEN_SCENARIOS = {
    "small_kitchen": {
        "name": "Small Restaurant Kitchen",
        "description": "A small kitchen with limited resources serving a casual restaurant",
        "staff": ["Head Chef", "Line Cook", "Kitchen Assistant"],
        "equipment": ["Oven", "Stove", "Cutting Board", "Knife Set"],
        "available": [4, 3, 4, 3],  # Available equipment counts
        "max_needs": [  # Maximum equipment needs for each staff
            [2, 3, 2, 2],  # Head Chef
            [2, 1, 1, 2],  # Line Cook
            [2, 0, 1, 1],  # Kitchen Assistant
        ],
        "allocated": [  # Initially allocated equipment to each staff
            [0, 1, 0, 0],  # Head Chef
            [0, 0, 1, 1],  # Line Cook
            [0, 1, 0, 1],  # Kitchen Assistant
        ]
    },
    
    "busy_restaurant": {
        "name": "Busy Full-Service Restaurant",
        "description": "A busy restaurant kitchen with multiple staff handling different tasks",
        "staff": ["Head Chef", "Sous Chef", "Line Cook", "Prep Cook", "Kitchen Assistant"],
        "equipment": ["Oven", "Stove", "Mixer", "Cutting Board", "Knife Set", "Food Processor"],
        "available": [7, 8, 10, 8, 9, 8],
        "max_needs": [
            [5, 5, 5, 5, 5, 5],  # Head Chef
            [3, 4, 3, 5, 3, 4],  # Sous Chef
            [1, 1, 0, 1, 1, 0],  # Line Cook
            [0, 0, 1, 1, 1, 1],  # Prep Cook
            [0, 0, 0, 1, 1, 0],  # Kitchen Assistant
        ],
        "allocated": [
            [1, 1, 0, 0, 0, 0],  # Head Chef
            [0, 1, 0, 1, 1, 0],  # Sous Chef
            [0, 1, 0, 0, 1, 0],  # Line Cook
            [0, 0, 1, 1, 0, 0],  # Prep Cook
            [0, 0, 0, 0, 0, 0],  # Kitchen Assistant
        ]
    },
    
    "deadlock_scenario": {
        "name": "Potential Deadlock Scenario",
        "description": "A kitchen scenario that may lead to deadlock if not managed properly",
        "staff": ["Head Chef", "Sous Chef", "Pastry Chef", "Line Cook"],
        "equipment": ["Oven", "Stove", "Mixer", "Cutting Board", "Knife Set"],
        "available": [1, 0, 1, 0, 0],  # Very limited available equipment
        "max_needs": [
            [2, 1, 2, 3, 1],  # Head Chef
            [1, 1, 0, 2, 1],  # Sous Chef
            [1, 0, 1, 0, 0],  # Pastry Chef
            [0, 1, 0, 1, 1],  # Line Cook
        ],
        "allocated": [
            [1, 1, 0, 0, 1],  # Head Chef
            [1, 0, 0, 0, 0],  # Sous Chef
            [0, 0, 1, 0, 0],  # Pastry Chef
            [0, 1, 0, 1, 1],  # Line Cook
        ]
    }
}

# Food preparation tasks for each staff role
FOOD_TASKS = {
    "Head Chef": ["Searing Steaks", "Preparing Sauce", "Plating Dishes", "Final Inspection"],
    "Sous Chef": ["Sautéing Vegetables", "Cooking Proteins", "Preparing Sides", "Assisting Head Chef"],
    "Pastry Chef": ["Baking Desserts", "Preparing Dough", "Decorating", "Making Ice Cream"],
    "Line Cook": ["Grilling", "Frying", "Boiling Pasta", "Preparing Appetizers"],
    "Prep Cook": ["Chopping Vegetables", "Marinating Meat", "Preparing Ingredients", "Making Stocks"],
    "Kitchen Assistant": ["Washing Dishes", "Organizing Ingredients", "Basic Prep", "Cleaning Workstations"]
}

# Equipment requirements for different tasks
TASK_EQUIPMENT_NEEDS = {
    "Searing Steaks": ["Stove", "Knife Set"],
    "Preparing Sauce": ["Stove", "Food Processor"],
    "Plating Dishes": ["Cutting Board"],
    "Final Inspection": [],
    "Sautéing Vegetables": ["Stove", "Knife Set", "Cutting Board"],
    "Cooking Proteins": ["Stove", "Oven"],
    "Preparing Sides": ["Cutting Board", "Knife Set"],
    "Assisting Head Chef": ["Cutting Board"],
    "Baking Desserts": ["Oven", "Mixer"],
    "Preparing Dough": ["Mixer", "Cutting Board"],
    "Decorating": [],
    "Making Ice Cream": ["Mixer", "Food Processor"],
    "Grilling": ["Stove"],
    "Frying": ["Stove"],
    "Boiling Pasta": ["Stove"],
    "Preparing Appetizers": ["Cutting Board", "Knife Set"],
    "Chopping Vegetables": ["Cutting Board", "Knife Set"],
    "Marinating Meat": ["Cutting Board", "Knife Set"],
    "Preparing Ingredients": ["Cutting Board", "Knife Set", "Food Processor"],
    "Making Stocks": ["Stove"],
    "Washing Dishes": [],
    "Organizing Ingredients": [],
    "Basic Prep": ["Cutting Board"],
    "Cleaning Workstations": []
} 