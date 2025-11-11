"""Tests for NetLogo code translator."""

from xnlogo.codegen.netlogo_translator import translate_statement


def test_translate_simple_assignment():
    """Test translating self.field = value."""
    result = translate_statement("self.count = 0", {"count"})
    assert result == "set count 0"


def test_translate_assignment_with_expression():
    """Test translating self.field = expr."""
    result = translate_statement("self.count = self.count + 1", {"count"})
    assert result == "set count (count + 1)"


def test_translate_assignment_multiple_operations():
    """Test translating complex expressions."""
    result = translate_statement("self.x = self.x * 2 + 1", {"x"})
    assert result == "set x ((x * 2) + 1)"


def test_translate_augmented_assignment():
    """Test translating self.field += value."""
    result = translate_statement("self.speed += 0.1", {"speed"})
    assert result == "set speed speed + 0.1"


def test_translate_subtraction():
    """Test subtraction operator."""
    result = translate_statement("self.energy = self.energy - 0.5", {"energy"})
    assert result == "set energy (energy - 0.5)"


def test_translate_multiplication():
    """Test multiplication operator."""
    result = translate_statement("self.size = self.size * 2", {"size"})
    assert result == "set size (size * 2)"


def test_translate_division():
    """Test division operator."""
    result = translate_statement("self.half = self.value / 2", {"half", "value"})
    assert result == "set half (value / 2)"


def test_translate_boolean_true():
    """Test boolean True -> true."""
    result = translate_statement("self.alive = True", {"alive"})
    assert result == "set alive true"


def test_translate_boolean_false():
    """Test boolean False -> false."""
    result = translate_statement("self.active = False", {"active"})
    assert result == "set active false"


def test_translate_string_constant():
    """Test string constants."""
    result = translate_statement('self.name = "agent"', {"name"})
    assert result == 'set name "agent"'


def test_translate_unparseable_falls_back():
    """Test that unparseable code gets commented."""
    result = translate_statement("this is not valid python", set())
    assert result.startswith("; UNPARSED:")


def test_translate_preserves_field_names():
    """Test that agent field names are correctly identified."""
    # Without agent_fields context, should still work
    result = translate_statement("self.custom_field = 42", {"custom_field"})
    assert result == "set custom_field 42"


# Comparison operators
def test_translate_equal():
    """Test equality comparison."""
    result = translate_statement("self.x == 5", {"x"})
    assert result == "(x = 5)"


def test_translate_not_equal():
    """Test not equal comparison."""
    result = translate_statement("self.x != 0", {"x"})
    assert result == "(x != 0)"


def test_translate_less_than():
    """Test less than comparison."""
    result = translate_statement("self.x < 10", {"x"})
    assert result == "(x < 10)"


def test_translate_less_than_or_equal():
    """Test less than or equal comparison."""
    result = translate_statement("self.x <= 10", {"x"})
    assert result == "(x <= 10)"


def test_translate_greater_than():
    """Test greater than comparison."""
    result = translate_statement("self.energy > 0", {"energy"})
    assert result == "(energy > 0)"


def test_translate_greater_than_or_equal():
    """Test greater than or equal comparison."""
    result = translate_statement("self.energy >= 0.5", {"energy"})
    assert result == "(energy >= 0.5)"


# Boolean operators
def test_translate_and():
    """Test and operator."""
    result = translate_statement("self.x > 0 and self.y > 0", {"x", "y"})
    assert result == "(x > 0) and (y > 0)"


def test_translate_or():
    """Test or operator."""
    result = translate_statement(
        "self.alive or self.respawning", {"alive", "respawning"}
    )
    assert result == "alive or respawning"


def test_translate_not():
    """Test not operator."""
    result = translate_statement("not self.active", {"active"})
    assert result == "not active"


def test_translate_complex_boolean():
    """Test complex boolean expression."""
    result = translate_statement(
        "self.x > 0 and self.y < 10 or self.z == 5", {"x", "y", "z"}
    )
    assert result == "(x > 0) and (y < 10) or (z = 5)"


# Unary operations
def test_translate_negation():
    """Test unary negation."""
    result = translate_statement("self.x = -self.y", {"x", "y"})
    assert result == "set x - y"


def test_translate_negative_constant():
    """Test negative constant."""
    result = translate_statement("self.x = -5", {"x"})
    assert result == "set x -5"


# If statements
def test_translate_simple_if():
    """Test simple if statement."""
    code = """if self.x > 0:
    self.y = 1"""
    result = translate_statement(code, {"x", "y"})
    expected = """if (x > 0) [
  set y 1
]"""
    assert result == expected


def test_translate_if_else():
    """Test if/else statement."""
    code = """if self.energy > 0:
    self.alive = True
else:
    self.alive = False"""
    result = translate_statement(code, {"energy", "alive"})
    expected = """if (energy > 0) [
  set alive true
]
[
  set alive false
]"""
    assert result == expected


def test_translate_if_multiple_statements():
    """Test if with multiple statements in body."""
    code = """if self.x > 0:
    self.y = 1
    self.z = 2"""
    result = translate_statement(code, {"x", "y", "z"})
    expected = """if (x > 0) [
  set y 1
  set z 2
]"""
    assert result == expected


# Method calls
def test_translate_method_call_no_args():
    """Test method call without arguments."""
    result = translate_statement("self.move()", set())
    assert result == "move"


def test_translate_method_call_with_args():
    """Test method call with arguments."""
    result = translate_statement("self.set_color(5)", set())
    assert result == "set_color 5"


def test_translate_builtin_abs():
    """Test abs() function."""
    result = translate_statement("self.x = abs(self.y)", {"x", "y"})
    assert result == "set x abs y"


def test_translate_builtin_round():
    """Test round() function."""
    result = translate_statement("self.x = round(self.y)", {"x", "y"})
    assert result == "set x round y"


def test_translate_builtin_max():
    """Test max() function."""
    result = translate_statement("self.x = max(self.a, self.b)", {"x", "a", "b"})
    # Note: NetLogo max takes a list, but we'll translate args directly for now
    assert "max" in result and "a" in result and "b" in result


# Power operator
def test_translate_power():
    """Test power operator."""
    result = translate_statement("self.x = self.y ** 2", {"x", "y"})
    assert result == "set x (y ^ 2)"


# Chained comparisons
def test_translate_chained_comparison():
    """Test chained comparison."""
    result = translate_statement("0 < self.x < 10", {"x"})
    assert result == "(0 < x) and (x < 10)"


# Subscript access
def test_translate_subscript_string():
    """Test dictionary-style access with string key."""
    result = translate_statement('self.data["speed"] = 1.5', {"data"})
    assert result == "set speed 1.5"


def test_translate_subscript_read():
    """Test reading from subscript."""
    result = translate_statement('self.x = self.data["speed"]', {"x", "data"})
    assert result == "set x speed"


def test_translate_subscript_augassign():
    """Test augmented assignment with subscript."""
    result = translate_statement('self.data["energy"] -= 0.1', {"data"})
    assert result == "set energy (energy - 0.1)"


# Return statements
def test_translate_return_value():
    """Test return with value."""
    result = translate_statement("return 0.0", set())
    assert result == "report 0.0"


def test_translate_return_void():
    """Test return without value."""
    result = translate_statement("return", set())
    assert result == "stop"


def test_translate_return_expression():
    """Test return with expression."""
    result = translate_statement("return self.x + 1", {"x"})
    assert result == "report (x + 1)"


# Variable assignments
def test_translate_local_variable():
    """Test local variable assignment (first use should be 'let')."""
    result = translate_statement("neighbors = 5", set())
    assert result == "let neighbors 5"


def test_translate_local_var_expression():
    """Test local variable with expression (first use should be 'let')."""
    result = translate_statement("total = self.x + self.y", {"x", "y"})
    assert result == "let total (x + y)"


# Method calls on variables
def test_translate_method_call_on_variable():
    """Test method call on a variable."""
    result = translate_statement("turtle.forward(1.5)", set())
    assert result == "forward 1.5"


def test_translate_sum_builtin():
    """Test sum() builtin."""
    result = translate_statement("total = sum(values)", set())
    assert "sum" in result


# ============================================================================
# For Loops Tests
# ============================================================================


def test_translate_for_range_simple():
    """Test for i in range(10) -> repeat 10."""
    result = translate_statement(
        "for i in range(10):\n    self.forward(1)", {"forward"}
    )
    assert "repeat 10" in result
    assert "forward 1" in result


def test_translate_for_range_with_start_stop():
    """Test for i in range(1, 5) -> while loop."""
    result = translate_statement("for i in range(1, 5):\n    print(i)")
    assert "set i 1" in result
    assert "while [i < 5]" in result
    assert "print i" in result
    assert "set i (i + 1)" in result


def test_translate_for_range_with_step():
    """Test for i in range(0, 10, 2) -> while loop with step."""
    result = translate_statement("for i in range(0, 10, 2):\n    print(i)")
    assert "set i 0" in result
    assert "while [i < 10]" in result
    assert "print i" in result
    assert "set i (i + 2)" in result


def test_translate_for_range_nested():
    """Test nested for loops."""
    code = """for i in range(3):
    for j in range(2):
        print(i)"""
    result = translate_statement(code)
    # Outer loop
    assert "repeat 3" in result
    # Inner loop
    assert "repeat 2" in result
    assert "print i" in result


# ============================================================================
# While Loops Tests
# ============================================================================


def test_translate_while_simple():
    """Test while condition -> while [condition]."""
    result = translate_statement("while self.energy > 0:\n    self.move()", {"energy"})
    assert "while [(energy > 0)]" in result
    assert "move" in result


def test_translate_while_with_complex_condition():
    """Test while with boolean operators."""
    code = "while self.x < 10 and self.y > 0:\n    self.step()"
    result = translate_statement(code, {"x", "y"})
    assert "while [(x < 10) and (y > 0)]" in result
    assert "step" in result


def test_translate_while_nested():
    """Test nested while loops."""
    code = """while self.alive:
    while self.moving:
        self.forward(1)"""
    result = translate_statement(code, {"alive", "moving"})
    assert result.count("while") == 2
    assert "forward 1" in result


# ============================================================================
# Ternary Operator Tests
# ============================================================================


def test_translate_ternary_simple():
    """Test x if cond else y -> ifelse-value cond x y."""
    result = translate_statement("result = 1 if self.alive else 0", {"alive"})
    assert "ifelse-value alive 1 0" in result


def test_translate_ternary_with_expressions():
    """Test ternary with complex expressions."""
    code = "speed = self.max_speed if self.running else self.min_speed"
    result = translate_statement(code, {"max_speed", "running", "min_speed"})
    assert "ifelse-value running max_speed min_speed" in result


def test_translate_ternary_nested():
    """Test nested ternary expressions."""
    code = "value = 1 if x > 0 else (-1 if x < 0 else 0)"
    result = translate_statement(code)
    assert "ifelse-value" in result
    assert result.count("ifelse-value") == 2


# ============================================================================
# List Operations Tests
# ============================================================================


def test_translate_list_indexing_constant():
    """Test lst[0] -> item 0 lst."""
    result = translate_statement("value = my_list[0]", set())
    assert "item 0 my_list" in result


def test_translate_list_indexing_variable():
    """Test lst[i] -> item i lst."""
    result = translate_statement("value = my_list[i]", set())
    assert "item i my_list" in result


def test_translate_list_indexing_negative():
    """Test lst[-1] -> item -1 lst."""
    result = translate_statement("value = my_list[-1]", set())
    assert "item -1 my_list" in result


def test_translate_list_slicing():
    """Test lst[1:3] -> sublist lst 1 3."""
    result = translate_statement("subset = my_list[1:3]", set())
    assert "sublist my_list 1 3" in result


def test_translate_list_slicing_open_end():
    """Test lst[1:] -> sublist lst 1 (length lst)."""
    result = translate_statement("subset = my_list[1:]", set())
    assert "sublist my_list 1 length my_list" in result


# ============================================================================
# Membership Operator Tests
# ============================================================================


def test_translate_in_operator():
    """Test x in lst -> member? x lst."""
    result = translate_statement("found = x in my_list", set())
    assert "member? x my_list" in result


def test_translate_not_in_operator():
    """Test x not in lst -> not member? x lst."""
    result = translate_statement("not_found = x not in my_list", set())
    assert "not member? x my_list" in result


def test_translate_in_with_if():
    """Test in operator in conditional."""
    code = "if x in neighbors:\n    print(x)"
    result = translate_statement(code)
    assert "if member? x neighbors" in result
    assert "print x" in result
