"""Example fish schooling model in xnLogo."""

from xnlogo import agent


@agent(
    patches={"food": "float"},
    turtles={"speed": "float", "energy": "float"},
    globals={"max-speed": "float", "turn-rate": "float"},
)
class SchoolingModel:
    def setup(self):
        self.globals["max-speed"] = 1.5
        self.globals["turn-rate"] = 15
        self.patches.ask("set food random-float 1.0")
        self.turtles.create(30, ["initialize-turtle"])

    def initialize_turtle(self, turtle):
        turtle.setxy(self.random_xcor(), self.random_ycor())
        turtle.set_heading(self.random_float(360))
        turtle["speed"] = 0.5 + self.random_float(0.5)
        turtle["energy"] = 1.0

    def go(self):
        self.turtles.ask(["steer", "swim", "feed"])
        self.patches.ask("set food food * 0.999")

    def steer(self, turtle):
        neighbors = turtle.in_radius(3)
        if not neighbors:
            return

        headings = sum(n.heading for n in neighbors) / len(neighbors)
        turn = (headings - turtle.heading) * 0.05
        turtle.right(
            max(-self.globals["turn-rate"], min(self.globals["turn-rate"], turn))
        )

    def swim(self, turtle):
        turtle["speed"] = min(self.globals["max-speed"], turtle["speed"] + 0.05)
        turtle.forward(turtle["speed"])
        turtle["energy"] -= 0.01 * turtle["speed"]

    def feed(self, turtle):
        patch = turtle.patch_here()
        food = patch["food"]
        if food > 0.1:
            turtle["energy"] = min(2.0, turtle["energy"] + 0.2)
            patch["food"] = food - 0.1

    # Placeholder helpers below allow CLI compilation prior to full runtime integration.
    def random_xcor(self):  # pragma: no cover - placeholder
        return 0.0

    def random_ycor(self):  # pragma: no cover - placeholder
        return 0.0

    def random_float(self, value):  # pragma: no cover - placeholder
        del value
        return 0.0
