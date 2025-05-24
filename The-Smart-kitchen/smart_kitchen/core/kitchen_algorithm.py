"""
Kitchen Resource Management Algorithm based on Banker's Algorithm
"""

class KitchenResourceManager:
    """
    Implements Banker's Algorithm for kitchen resource management.
    Helps prevent deadlocks in kitchen operations where multiple
    staff members (processes) need to use various equipment (resources).
    """
    
    def __init__(self, available_resources, max_resources, allocated_resources):
        """
        Initialize the Kitchen Resource Manager.
        
        Args:
            available_resources: List of available equipment counts
            max_resources: Matrix of maximum equipment needs for each staff
            allocated_resources: Matrix of currently allocated equipment to each staff
        """
        self.available = available_resources
        self.max_resources = max_resources
        self.allocated = allocated_resources
        self.num_staff = len(max_resources)
        self.num_equipment = len(available_resources)
        
    def calculate_need(self):
        """Calculate the equipment still needed by each staff member."""
        return [
            [self.max_resources[i][j] - self.allocated[i][j] 
             for j in range(self.num_equipment)] 
            for i in range(self.num_staff)
        ]
    
    def is_safe(self):
        """
        Determine if the kitchen is in a safe state, meaning all staff
        can complete their tasks without deadlock.
        
        Returns:
            (bool, list): Tuple with safety status and safe sequence if available
        """
        need = self.calculate_need()
        work = self.available[:]
        finished = [False] * self.num_staff
        safe_sequence = []
        
        # Try to find a safe sequence
        for _ in range(self.num_staff):
            found = False
            for i in range(self.num_staff):
                # If staff member can finish their task with available equipment
                if not finished[i] and all(need[i][j] <= work[j] for j in range(self.num_equipment)):
                    # Release all allocated equipment
                    for j in range(self.num_equipment):
                        work[j] += self.allocated[i][j]
                    finished[i] = True
                    safe_sequence.append(i)
                    found = True
                    break
            
            if not found:
                # No staff can finish with available equipment - unsafe state
                return False, []
                
        return True, safe_sequence
    
    def request_resources(self, staff_id, request):
        """
        Process a request for additional equipment from a staff member.
        
        Args:
            staff_id: Index of the staff member making the request
            request: List of requested equipment counts
            
        Returns:
            bool: True if request can be granted safely, False otherwise
        """
        need = self.calculate_need()
        
        # Check if request exceeds need
        for j in range(self.num_equipment):
            if request[j] > need[staff_id][j]:
                return False, "Request exceeds maximum need"
        
        # Check if request exceeds available
        for j in range(self.num_equipment):
            if request[j] > self.available[j]:
                return False, "Insufficient resources available"
        
        # Try to allocate the resources
        old_available = self.available[:]
        old_allocated = [row[:] for row in self.allocated]
        
        # Temporarily allocate the resources
        for j in range(self.num_equipment):
            self.available[j] -= request[j]
            self.allocated[staff_id][j] += request[j]
        
        # Check if resulting state is safe
        safe, _ = self.is_safe()
        
        if not safe:
            # Restore original state
            self.available = old_available
            self.allocated = old_allocated
            return False, "Request would lead to unsafe state"
            
        return True, "Request granted"
    
    def release_resources(self, staff_id, release):
        """
        Release equipment back to the available pool.
        
        Args:
            staff_id: Index of the staff member releasing equipment
            release: List of equipment counts to release
        """
        for j in range(self.num_equipment):
            if release[j] > self.allocated[staff_id][j]:
                # Cannot release more than allocated
                return False, "Cannot release more than allocated"
                
        # Release the resources
        for j in range(self.num_equipment):
            self.available[j] += release[j]
            self.allocated[staff_id][j] -= release[j]
            
        return True, "Resources released"

    def detect_deadlock(self):
        """
        Detect if there is a deadlock in the current state.
        
        Returns:
            bool: True if deadlock detected, False otherwise
        """
        safe, _ = self.is_safe()
        return not safe 