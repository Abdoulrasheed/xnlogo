"""simple traffic flow model for xnlogo."""

from xnlogo import agent


@agent
class Car:
    speed: float = 1.0
    position: float = 0.0
    max_speed: float = 2.0

    def setup(self):
        self.speed = 0.5
        self.position = 0.0
        self.max_speed = 2.0

    def accelerate(self):
        if self.speed < self.max_speed:
            self.speed = self.speed + 0.1

    def decelerate(self):
        if self.speed > 0:
            self.speed = self.speed - 0.2

    def move_forward(self):
        self.position = self.position + self.speed

    def wrap_around(self):
        if self.position > 100:
            self.position = 0.0
