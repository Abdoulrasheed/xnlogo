"""simple epidemic spread model for xnlogo."""

from xnlogo import agent


@agent
class Person:
    infected: bool = False
    immune: bool = False
    infection_time: int = 0

    def setup(self):
        self.infected = False
        self.immune = False
        self.infection_time = 0

    def spread(self):
        if self.infected:
            self.infection_time = self.infection_time + 1

    def recover(self):
        if self.infection_time > 10:
            self.infected = False
            self.immune = True
            self.infection_time = 0
