"""
boids flocking example for xlogo
basic boids flocking simulation using xlogo-compatible Python
"""

from xnlogo import Model, Agent, run


class Boid(Agent):
    def step(self):
        # simple flocking: move towards average position of nearby boids
        neighbors = self.model.nearby_agents(self, Boid, radius=5)
        if neighbors:
            avg_x = sum(n.x for n in neighbors) / len(neighbors)
            avg_y = sum(n.y for n in neighbors) / len(neighbors)
            dx = avg_x - self.x
            dy = avg_y - self.y
            self.move_towards(dx, dy, distance=1)
        else:
            self.move(self.random_direction(), 1)


model = Model()
for _ in range(30):
    model.add_agent(Boid())

run(model, steps=60)
