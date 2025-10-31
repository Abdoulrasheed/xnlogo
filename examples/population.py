"""simple population dynamics model for xnlogo."""

from xnlogo import agent


@agent
class Organism:
    energy: float = 10.0
    age: int = 0
    alive: bool = True

    def setup(self):
        self.energy = 10.0
        self.age = 0
        self.alive = True

    def live(self):
        self.energy = self.energy - 0.1
        self.age = self.age + 1

    def check_death(self):
        if self.energy <= 0:
            self.alive = False
        if self.age > 100:
            self.alive = False

    def reproduce(self):
        if self.energy > 20:
            self.energy = self.energy - 10
