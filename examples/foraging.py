"""ant foraging model for xnlogo."""

from xnlogo import agent


@agent
class Ant:
    has_food: bool = False
    energy: float = 10.0
    x: float = 0.0
    y: float = 0.0

    def setup(self):
        self.has_food = False
        self.energy = 10.0
        self.x = 0.0
        self.y = 0.0

    def search(self):
        if not self.has_food:
            self.x = self.x + 0.5
            self.y = self.y + 0.5
            self.energy = self.energy - 0.1

    def return_home(self):
        if self.has_food:
            self.x = self.x - 0.5
            self.y = self.y - 0.5

    def drop_food(self):
        if self.has_food:
            if self.x < 1 and self.y < 1:
                self.has_food = False
                self.energy = 10.0
