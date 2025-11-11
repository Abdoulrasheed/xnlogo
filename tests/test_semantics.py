"""Semantic validation tests."""

from pathlib import Path

from xnlogo.parser.ast_parser import Parser
from xnlogo.semantics.checks import run_behavioral_checks, run_structural_checks


def test_detects_async_await(tmp_path: Path) -> None:
    source = tmp_path / "model.py"
    source.write_text(
        """
from xnlogo.runtime import Model

class Bot(Model):
    def __init__(self):
        super().__init__()
        self.speed = 1
    
    async def move(self):
        await self.step()
""",
        encoding="utf-8",
    )

    parser = Parser()
    result = parser.parse([source])
    run_structural_checks(result.model, result.diagnostics)
    run_behavioral_checks(result.model, result.diagnostics)

    warnings = [d for d in result.diagnostics if d.level == "warning"]
    assert any("async/await" in w.message for w in warnings)


def test_detects_lambda(tmp_path: Path) -> None:
    source = tmp_path / "model.py"
    source.write_text(
        """
from xnlogo.runtime import Model

class Agent(Model):
    def __init__(self):
        super().__init__()
        self.x = 0
    
    def compute(self):
        f = lambda n: n * 2
        self.x = f(5)
""",
        encoding="utf-8",
    )

    parser = Parser()
    result = parser.parse([source])
    run_behavioral_checks(result.model, result.diagnostics)

    warnings = [d for d in result.diagnostics if d.level == "warning"]
    assert any("lambda" in w.message for w in warnings)


def test_detects_try_except(tmp_path: Path) -> None:
    source = tmp_path / "model.py"
    source.write_text(
        """
from xnlogo.runtime import Model

class Agent(Model):
    def __init__(self):
        super().__init__()
        self.value = 0
    
    def safe_compute(self):
        try:
            self.value = 1 / 0
        except ZeroDivisionError:
            self.value = 0
""",
        encoding="utf-8",
    )

    parser = Parser()
    result = parser.parse([source])
    run_behavioral_checks(result.model, result.diagnostics)

    warnings = [d for d in result.diagnostics if d.level == "warning"]
    assert any("try/except" in w.message for w in warnings)


def test_allows_simple_comprehensions(tmp_path: Path) -> None:
    source = tmp_path / "model.py"
    source.write_text(
        """
from xnlogo.runtime import Model

class Agent(Model):
    def __init__(self):
        super().__init__()
        self.neighbors = []
    
    def find(self):
        close = [n for n in self.neighbors if n.distance < 5]
""",
        encoding="utf-8",
    )

    parser = Parser()
    result = parser.parse([source])
    run_behavioral_checks(result.model, result.diagnostics)

    warnings = [d for d in result.diagnostics if d.level == "warning"]
    comprehension_warnings = [w for w in warnings if "comprehension" in w.message]
    assert len(comprehension_warnings) == 0


def test_detects_no_agents(tmp_path: Path) -> None:
    source = tmp_path / "empty.py"
    source.write_text("# Empty file\n", encoding="utf-8")

    parser = Parser()
    result = parser.parse([source])
    run_structural_checks(result.model, result.diagnostics)

    assert result.diagnostics.has_errors()
    errors = [d for d in result.diagnostics if d.level == "error"]
    assert any("No agents defined" in e.message for e in errors)
