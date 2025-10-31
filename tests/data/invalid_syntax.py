"""Test file with invalid Python syntax."""
from xnlogo import agent


@agent(breed="broken")
class BrokenAgent:
    def bad_method(self):
        # Missing closing parenthesis
        print("hello"
        self.x = 5
