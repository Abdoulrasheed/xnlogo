"""predator-prey dynamics model for xnlogo."""

from xnlogo import agent


@agent(breed="sheep")
class Sheep:
    energy: float = 5.0
    age: int = 0

    def setup(self):
        self.energy = 5.0
        self.age = 0

    def graze(self):
        self.energy = self.energy + 1.0

    def move(self):
        self.energy = self.energy - 0.5
        self.age = self.age + 1

    def die(self):
        if self.energy <= 0:
            self.energy = 0.0


@agent(breed="wolf")
class Wolf:
    energy: float = 10.0
    age: int = 0

    def setup(self):
        self.energy = 10.0
        self.age = 0

    def hunt(self):
        self.energy = self.energy + 5.0

    def move(self):
        self.energy = self.energy - 1.0
        self.age = self.age + 1

    def die(self):
        if self.energy <= 0:
            self.energy = 0.0
