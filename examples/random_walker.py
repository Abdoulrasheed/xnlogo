"""random walk example for xnlogo."""

from xnlogo import agent


@agent
class Walker:
    x: float = 0.0
    y: float = 0.0
    step_size: float = 1.0

    def setup(self):
        self.x = 0.0
        self.y = 0.0
        self.step_size = 0.5

    def walk(self):
        self.x = self.x + self.step_size
        self.y = self.y - self.step_size

    def bounce(self):
        if self.x > 16:
            self.x = -16
        if self.x < -16:
            self.x = 16
        if self.y > 16:
            self.y = -16
        if self.y < -16:
            self.y = 16
