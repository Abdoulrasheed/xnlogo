"""simple counter example for xnlogo."""

from xnlogo import agent


@agent
class Counter:
    count: int = 0

    def setup(self):
        self.count = 0

    def increment(self):
        self.count = self.count + 1

    def reset(self):
        if self.count > 10:
            self.count = 0
