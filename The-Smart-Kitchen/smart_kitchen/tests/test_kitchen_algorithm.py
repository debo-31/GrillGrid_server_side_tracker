"""
Unit tests for the kitchen resource management algorithm.
"""
import unittest
import sys
import os

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from smart_kitchen.core.kitchen_algorithm import KitchenResourceManager
from smart_kitchen.data.kitchen_data import KITCHEN_SCENARIOS


class TestKitchenResourceManager(unittest.TestCase):
    """Test cases for the KitchenResourceManager class"""
    
    def setUp(self):
        """Set up test cases"""
        # Create a simple test kitchen with 3 staff and 3 equipment types
        self.available = [3, 3, 2]  # Available equipment
        self.max_resources = [
            [7, 5, 3],  # Head Chef
            [3, 2, 2],  # Sous Chef
            [9, 0, 2]   # Line Cook
        ]
        self.allocated = [
            [0, 1, 0],  # Head Chef
            [2, 0, 0],  # Sous Chef
            [3, 0, 2]   # Line Cook
        ]
        
        self.kitchen_manager = KitchenResourceManager(
            self.available.copy(),
            [row[:] for row in self.max_resources],
            [row[:] for row in self.allocated]
        )
    
    def test_calculate_need(self):
        """Test calculation of needed resources"""
        expected_need = [
            [7, 4, 3],  # Head Chef needs
            [1, 2, 2],  # Sous Chef needs
            [6, 0, 0]   # Line Cook needs
        ]
        
        actual_need = self.kitchen_manager.calculate_need()
        
        for i in range(len(expected_need)):
            for j in range(len(expected_need[i])):
                self.assertEqual(expected_need[i][j], actual_need[i][j])
    
    def test_is_safe_with_safe_state(self):
        """Test detecting a safe state"""
        safe, sequence = self.kitchen_manager.is_safe()
        
        self.assertTrue(safe)
        self.assertEqual(len(sequence), 3)  # Should have all 3 staff in the sequence
    
    def test_is_safe_with_unsafe_state(self):
        """Test detecting an unsafe state"""
        # Create an unsafe state by allocating too many resources
        unsafe_manager = KitchenResourceManager(
            [0, 0, 0],  # No available equipment
            self.max_resources,
            self.allocated
        )
        
        safe, sequence = unsafe_manager.is_safe()
        
        self.assertFalse(safe)
        self.assertEqual(len(sequence), 0)  # No safe sequence possible
    
    def test_request_resources_success(self):
        """Test successful resource request"""
        request = [1, 0, 1]  # Request 1 oven and 1 knife
        success, message = self.kitchen_manager.request_resources(0, request)
        
        self.assertTrue(success)
        self.assertEqual(self.kitchen_manager.available, [2, 3, 1])
        self.assertEqual(self.kitchen_manager.allocated[0], [1, 1, 1])
    
    def test_request_resources_exceeds_need(self):
        """Test resource request that exceeds need"""
        request = [8, 0, 0]  # Request more than max need
        success, message = self.kitchen_manager.request_resources(0, request)
        
        self.assertFalse(success)
        self.assertEqual(message, "Request exceeds maximum need")
        # Ensure resources remain unchanged
        self.assertEqual(self.kitchen_manager.available, [3, 3, 2])
        self.assertEqual(self.kitchen_manager.allocated[0], [0, 1, 0])
    
    def test_request_resources_exceeds_available(self):
        """Test resource request that exceeds available resources"""
        request = [4, 0, 0]  # Request more than available
        success, message = self.kitchen_manager.request_resources(0, request)
        
        self.assertFalse(success)
        self.assertEqual(message, "Insufficient resources available")
        # Ensure resources remain unchanged
        self.assertEqual(self.kitchen_manager.available, [3, 3, 2])
        self.assertEqual(self.kitchen_manager.allocated[0], [0, 1, 0])
    
    def test_request_resources_unsafe(self):
        """Test resource request that would lead to unsafe state"""
        # Create a kitchen manager with a state that would become unsafe
        # after a specific request
        unsafe_manager = KitchenResourceManager(
            [2, 1, 0],  # Limited available equipment
            self.max_resources,
            self.allocated
        )
        
        # This request would take all remaining resources
        request = [2, 1, 0]
        success, message = unsafe_manager.request_resources(0, request)
        
        # Should be denied since it would lead to unsafe state
        self.assertFalse(success)
        self.assertEqual(message, "Request would lead to unsafe state")
    
    def test_release_resources(self):
        """Test releasing resources back to available pool"""
        release = [0, 1, 0]  # Release 1 stove
        success, message = self.kitchen_manager.release_resources(0, release)
        
        self.assertTrue(success)
        self.assertEqual(self.kitchen_manager.available, [3, 4, 2])
        self.assertEqual(self.kitchen_manager.allocated[0], [0, 0, 0])
    
    def test_release_resources_invalid(self):
        """Test releasing more resources than allocated"""
        release = [1, 0, 0]  # Try to release 1 oven that is not allocated
        success, message = self.kitchen_manager.release_resources(0, release)
        
        self.assertFalse(success)
        self.assertEqual(message, "Cannot release more than allocated")
        # Ensure resources remain unchanged
        self.assertEqual(self.kitchen_manager.available, [3, 3, 2])
        self.assertEqual(self.kitchen_manager.allocated[0], [0, 1, 0])
    
    def test_deadlock_scenario(self):
        """Test deadlock detection with a predefined deadlock scenario"""
        # Load the deadlock scenario from kitchen_data
        scenario = KITCHEN_SCENARIOS["deadlock_scenario"]
        
        deadlock_manager = KitchenResourceManager(
            scenario["available"].copy(),
            [row[:] for row in scenario["max_needs"]],
            [row[:] for row in scenario["allocated"]]
        )
        
        # Check if deadlock is detected
        deadlock = deadlock_manager.detect_deadlock()
        
        self.assertTrue(deadlock)


if __name__ == "__main__":
    unittest.main() 