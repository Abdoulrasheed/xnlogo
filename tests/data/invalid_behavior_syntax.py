"""Test file with valid Python class but invalid behavior syntax."""
from xnlogo.runtime import Model, breed


class BuggyModel(Model):
    """Model with syntax errors in behavior statements."""
    
    def __init__(self):
        super().__init__()
        self.agents = breed("agents", "agent")
    
    def setup(self):
        """This method has valid syntax."""
        for i in range(5):
            agent = self.agents.create(1)
            agent.x = 0
            agent.y = 0
    
    def broken_move(self, agent):
        """This method has invalid syntax in a statement."""
        agent.x = 5
        # Invalid syntax - missing closing parenthesis
        print("moving"
        agent.y += 1
