"""Test model with multiple breeds."""

from xnlogo.runtime import Model, breed, reset_ticks, tick


class EcosystemModel(Model):
    def __init__(self):
        super().__init__()
        self.sheep = breed("sheep", "sheep")
        self.wolves = breed("wolves", "wolf")

    def setup(self):
        reset_ticks()
        # Create some sheep
        for i in range(10):
            s = self.sheep.create(1)
            s.energy = 5.0
            s.wool = 0.0
        
        # Create some wolves
        for i in range(3):
            w = self.wolves.create(1)
            w.energy = 10.0
            w.hunger = 0.0

    def go(self):
        # Sheep behavior
        for s in self.sheep.all():
            self.graze(s)
            self.grow_wool(s)
        
        # Wolf behavior
        for w in self.wolves.all():
            self.hunt(w)
            self.check_hunger(w)
        
        tick()

    def graze(self, sheep):
        sheep.energy = sheep.energy + 0.5

    def grow_wool(self, sheep):
        if sheep.energy > 2:
            sheep.wool = sheep.wool + 0.1

    def hunt(self, wolf):
        wolf.hunger = wolf.hunger + 0.2

    def check_hunger(self, wolf):
        if wolf.hunger > 5:
            wolf.energy = wolf.energy - 1
