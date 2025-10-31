"""
random walk example for xlogo
simple random walk using xlogo-compatible Python
"""

from xnlogo import Model, Agent, run


class Walker(Agent):
    def step(self):
        # move in a random direction
        self.move(self.random_direction(), 1)


model = Model()
for _ in range(20):
    model.add_agent(Walker())

run(model, steps=50)
