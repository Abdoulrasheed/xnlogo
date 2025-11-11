"""Test file with invalid Python syntax."""
from xnlogo.runtime import Model, breed


class BrokenModel(Model):
    def __init__(self):
        super().__init__()
        self.agents = breed("agents", "agent")
    
    def bad_method(self):
        # Missing closing parenthesis
        print("hello"
        self.x = 5
