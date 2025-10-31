"""Test statements that might be valid in context but invalid when parsed alone."""

from xnlogo import agent


@agent(breed="walker", state=["position"])
class Walker:
    """Agent for testing statement validation."""

    def setup(self):
        """Initialize walker."""
        self.position = 0

    def move(self):
        """Move forward."""
        # This is a complete valid statement
        self.position += 1
