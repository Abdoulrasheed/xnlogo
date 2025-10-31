"""Test file with valid Python class but invalid behavior syntax."""
from xnlogo import agent


@agent(breed="buggy", state=["x", "y"])
class BuggyAgent:
    """Agent with syntax errors in behavior statements."""
    
    def setup(self):
        """This method has valid syntax."""
        self.x = 0
        self.y = 0
    
    def broken_move(self):
        """This method has invalid syntax in a statement."""
        self.x = 5
        # Invalid syntax - missing closing parenthesis
        print("moving"
        self.y += 1
