"""Test model with complex expressions and multiple behaviors."""

from xnlogo import agent


@agent
class ComplexAgent:
    x: float = 0.0
    y: float = 0.0
    energy: float = 100.0
    speed: float = 1.0
    alive: bool = True

    def setup(self):
        self.x = 0.0
        self.y = 0.0
        self.energy = 100.0
        self.alive = True

    def move(self):
        self.x = self.x + self.speed
        self.y = self.y + self.speed * 0.5

    def update_energy(self):
        self.energy = self.energy - self.speed * 0.1

    def check_status(self):
        if self.energy <= 0:
            self.alive = False
        else:
            if self.energy < 20:
                self.speed = 0.5
            else:
                self.speed = 1.0

    def complex_math(self):
        # Test various operators
        self.x = self.x**2
        self.y = self.y - self.x / 2

        # Test comparisons and boolean logic
        if self.x > 100 and self.y < 50:
            self.x = 0.0

        if self.x < 0 or self.y < 0:
            self.x = abs(self.x)
            self.y = abs(self.y)

    def boundary_check(self):
        if self.x > 100:
            self.x = 100

        if self.x < -100:
            self.x = -100

        if self.y > 100:
            self.y = 100

        if self.y < -100:
            self.y = -100
