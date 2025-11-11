"""Simple model for golden tests."""

from xnlogo.runtime import Model, reset_ticks, tick


class CounterModel(Model):
    def __init__(self):
        super().__init__()
        self.count = 0

    def setup(self):
        reset_ticks()
        self.count = 0

    def increment(self):
        self.count = self.count + 1

    def reset(self):
        self.count = 0
    
    def go(self):
        self.increment()
        tick()
