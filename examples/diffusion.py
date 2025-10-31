"""
simple diffusion example for xlogo
agent-based diffusion using xlogo-compatible Python
"""

from xnlogo import Model, Agent, run


class Particle(Agent):
    def step(self):
        # move randomly to simulate diffusion
        self.move(self.random_direction(), 1)


model = Model()
for _ in range(100):
    model.add_agent(Particle())

run(model, steps=75)
