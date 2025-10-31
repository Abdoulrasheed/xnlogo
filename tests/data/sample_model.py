"""Sample model for testing."""


def agent(*args, **kwargs):  # pragma: no cover - decorator stub for parsing only
    def wrapper(cls):
        return cls

    return wrapper


@agent
class Rabbit:
    energy: int = 10

    def move(self):
        self.energy -= 1
        self.position += 1
