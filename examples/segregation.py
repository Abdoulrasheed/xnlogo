"""schelling segregation model for xnlogo."""

from xnlogo import agent


@agent
class Person:
    group: int = 0
    happy: bool = False
    x: float = 0.0
    y: float = 0.0

    def setup(self):
        self.group = 0
        self.happy = False
        self.x = 0.0
        self.y = 0.0

    def check_happiness(self):
        if self.group == 1:
            self.happy = True

    def move_if_unhappy(self):
        if not self.happy:
            self.x = self.x + 1.0
            self.y = self.y + 1.0
