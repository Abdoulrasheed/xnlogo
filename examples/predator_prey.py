"""
predator-prey model example for xlogo
simple Lotka-Volterra predator-prey simulation using xlogo-compatible Python
"""

from xnlogo import Model, Agent, run


class Prey(Agent):
    def step(self):
        # prey reproduce with some probability
        if self.random() < 0.04:
            self.model.add_agent(Prey())
        # move randomly
        self.move(self.random_direction(), 1)


class Predator(Agent):
    def step(self):
        # predators die with some probability
        if self.random() < 0.05:
            self.model.remove_agent(self)
            return
        # move randomly
        self.move(self.random_direction(), 1)
        # eat prey if nearby
        prey = self.model.nearby_agents(self, Prey, radius=2)
        if prey:
            self.model.remove_agent(prey[0])
            # reproduce after eating
            if self.random() < 0.1:
                self.model.add_agent(Predator())


model = Model()
for _ in range(50):
    model.add_agent(Prey())
for _ in range(10):
    model.add_agent(Predator())

run(model, steps=100)
