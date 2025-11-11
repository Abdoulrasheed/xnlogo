"""Sample model for testing."""

from xnlogo.runtime import Model, breed, reset_ticks, tick


class RabbitModel(Model):
    def __init__(self):
        super().__init__()
        self.rabbits = breed("rabbits", "rabbit")

    def setup(self):
        reset_ticks()
        for i in range(10):
            rabbit = self.rabbits.create(1)
            rabbit.energy = 10
            rabbit.position = 0

    def go(self):
        for rabbit in self.rabbits.all():
            self.move(rabbit)
        tick()

    def move(self, rabbit):
        rabbit.energy -= 1
        rabbit.position += 1
