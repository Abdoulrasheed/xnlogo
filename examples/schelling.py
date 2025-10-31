"""
Schelling segregation model example for xlogo
simple Schelling segregation simulation using xlogo-compatible Python
"""

from xnlogo import Model, Agent, run


class Person(Agent):
    def __init__(self, group):
        super().__init__()
        self.group = group

    def step(self):
        # check neighbors
        neighbors = self.model.nearby_agents(self, Person, radius=2)
        same_group = [n for n in neighbors if n.group == self.group]
        if len(same_group) < 3:
            # move to random location if unhappy
            self.move_to(self.random_location())


model = Model()
for _ in range(25):
    model.add_agent(Person(group=0))
for _ in range(25):
    model.add_agent(Person(group=1))

run(model, steps=50)
