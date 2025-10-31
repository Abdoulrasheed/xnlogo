"""Simple agent for golden tests."""

from xnlogo import agent


@agent
class Counter:
    count: int = 0

    def increment(self):
        self.count = self.count + 1

    def reset(self):
        self.count = 0
