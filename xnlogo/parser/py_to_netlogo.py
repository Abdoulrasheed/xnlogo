"""Convert Python AST to NetLogo code."""

from __future__ import annotations

import ast


class PythonToNetLogoConverter(ast.NodeVisitor):
    """Convert Python AST nodes to NetLogo code."""

    def __init__(self, context_params: set[str] | None = None):
        self.netlogo_code = []
        self.indent_level = 0
        self.loop_vars = set()  # Track loop variables like 'turtle', 'patch'
        # Track parameters that represent the implicit agent context
        self.context_params = context_params or set()
        # Track variables created by create() calls (for sprout context)
        self.created_turtles = set()
        # Track if we're inside a guard clause pattern
        self.pending_statements = []
        # Track local variables (for 'let' vs 'set')
        self.local_vars: set[str] = set()
        self.declared_vars: set[str] = set()

    def convert(self, node: ast.AST) -> str:
        """Convert a Python AST node to NetLogo code."""
        self.netlogo_code = []

        # Pre-analyze to identify local variables
        self._analyze_local_variables(node)

        self.visit(node)
        return "\n".join(self.netlogo_code)

    def _analyze_local_variables(self, node: ast.AST) -> None:
        """Identify local variables (simple assignments, not self.attr)."""
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    # Simple variable assignment: x = value (not self.x or turtle.x)
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Exclude loop variables and context parameters
                        if (
                            var_name not in self.loop_vars
                            and var_name not in self.context_params
                        ):
                            self.local_vars.add(var_name)

    def _indent(self) -> str:
        """Get current indentation."""
        return "  " * self.indent_level

    def visit_For(self, node: ast.For) -> None:
        """Convert for loop to ask block or detect sprout pattern."""
        # Track the loop variable (e.g., 'turtle', 'patch')
        if isinstance(node.target, ast.Name):
            loop_var = node.target.id
            self.loop_vars.add(loop_var)

        # Detect sprout pattern: for patch in patches: turtle = create(1); turtle.attr = val
        is_sprout_pattern = False
        if isinstance(node.target, ast.Name) and node.target.id in ("patch", "p"):
            # Check if first statement creates a turtle
            if node.body and isinstance(node.body[0], ast.Assign):
                first_assign = node.body[0]
                if (
                    isinstance(first_assign.value, ast.Call)
                    and isinstance(first_assign.value.func, ast.Attribute)
                    and first_assign.value.func.attr == "create"
                ):
                    is_sprout_pattern = True

        if is_sprout_pattern:
            # Convert to sprout pattern
            iter_expr = self._convert_expr(node.iter)
            self.netlogo_code.append(f"{self._indent()}ask {iter_expr} [")
            self.indent_level += 1

            # Get the turtle variable name from first assignment
            turtle_var = None
            if isinstance(node.body[0].targets[0], ast.Name):
                turtle_var = node.body[0].targets[0].id
                self.created_turtles.add(turtle_var)

            # Generate sprout command
            if isinstance(node.body[0].value, ast.Call):
                args = node.body[0].value.args
                count = self._convert_expr(args[0]) if args else "1"
                self.netlogo_code.append(f"{self._indent()}sprout {count} [")
                self.indent_level += 1

                # Process remaining statements (turtle.attr = value)
                for stmt in node.body[1:]:
                    self.visit(stmt)

                self.indent_level -= 1
                self.netlogo_code.append(f"{self._indent()}]")

            self.indent_level -= 1
            self.netlogo_code.append(f"{self._indent()}]")

            # Clean up created turtle tracking
            if turtle_var:
                self.created_turtles.discard(turtle_var)

        # Regular for loop handling
        elif isinstance(node.iter, ast.Call):
            # for turtle in self.turtles.all(): -> ask turtles [
            # Handle .all() calls
            if isinstance(node.iter.func, ast.Attribute):
                if node.iter.func.attr == "all":
                    agentset = self._convert_expr(node.iter.func.value)
                    agentset = agentset.replace("self.", "")
                    self.netlogo_code.append(f"{self._indent()}ask {agentset} [")
                else:
                    # Other method calls (filter, sample, etc.)
                    agentset = self._convert_expr(node.iter)
                    self.netlogo_code.append(f"{self._indent()}ask {agentset} [")
            else:
                # Direct function call like patches(), turtles()
                agentset = self._convert_expr(node.iter)
                self.netlogo_code.append(f"{self._indent()}ask {agentset} [")

            self.indent_level += 1
            for stmt in node.body:
                self.visit(stmt)
            self.indent_level -= 1
            self.netlogo_code.append(f"{self._indent()}]")
        else:
            # Regular iteration over a variable
            iter_expr = self._convert_expr(node.iter)
            # Check if it looks like an agentset variable
            # Common patterns: all_patches, selected_patches, turtles, etc.
            if isinstance(node.target, ast.Name):
                loop_var_name = node.target.id
                # If loop variable suggests agent iteration (patch, turtle, agent), use ask
                if loop_var_name in ("patch", "turtle", "agent", "p", "t"):
                    self.netlogo_code.append(f"{self._indent()}ask {iter_expr} [")
                else:
                    # Otherwise use foreach
                    self.netlogo_code.append(f"{self._indent()}foreach {iter_expr} [")
            else:
                self.netlogo_code.append(f"{self._indent()}foreach {iter_expr} [")

            self.indent_level += 1
            for stmt in node.body:
                self.visit(stmt)
            self.indent_level -= 1
            self.netlogo_code.append(f"{self._indent()}]")

        # Remove loop variable from tracking
        if isinstance(node.target, ast.Name):
            self.loop_vars.discard(node.target.id)

    def _is_object_used_in_body(self, var_name: str, body: list) -> bool:
        """Check if a variable is used as an object (not just boolean) in the body."""
        for stmt in body:
            # Check if variable is passed as argument to a function
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    # Check if variable is used as an argument
                    for arg in node.args:
                        if isinstance(arg, ast.Name) and arg.id == var_name:
                            return True
                    # Check if it's a method call on the variable
                    if isinstance(node.func, ast.Attribute):
                        if (
                            isinstance(node.func.value, ast.Name)
                            and node.func.value.id == var_name
                        ):
                            return True
        return False

    def visit_If(self, node: ast.If) -> None:
        """Convert if statement to NetLogo if or ifelse."""
        test = self._convert_expr(node.test)

        # Special case: if test is a simple variable name (truthiness check),
        # check if it's used as an object in the body. If so, convert to "!= nobody"
        # This handles cases like "if nearest:" where nearest might be None
        if isinstance(node.test, ast.Name):
            var_name = node.test.id
            # Check if the variable is used as an object (passed to functions, has methods called on it)
            if self._is_object_used_in_body(var_name, node.body):
                test = f"{test} != nobody"

        # Check if we have an else clause (not elif)
        has_else = node.orelse and not (
            len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
        )

        # Use 'ifelse' if there's a true else clause, 'if' otherwise
        keyword = "ifelse" if has_else else "if"
        self.netlogo_code.append(f"{self._indent()}{keyword} {test} [")

        self.indent_level += 1
        # Save declared vars state to allow separate declarations in branches
        saved_declared_vars = self.declared_vars.copy()

        for stmt in node.body:
            self.visit(stmt)

        self.indent_level -= 1

        if node.orelse:
            # Check if orelse is a single If node (which represents elif in Python)
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # This is an elif - close the current if and start a new if
                self.netlogo_code.append(f"{self._indent()}]")
                # Restore declared vars so the elif branch can declare its own variables
                self.declared_vars = saved_declared_vars.copy()
                # Visit the elif as a new if statement
                self.visit(node.orelse[0])
            else:
                # This is a true else clause - use ifelse syntax
                self.netlogo_code.append(f"{self._indent()}] [")
                self.indent_level += 1
                # Restore declared vars for else branch
                self.declared_vars = saved_declared_vars.copy()
                for stmt in node.orelse:
                    self.visit(stmt)
                self.indent_level -= 1
                self.netlogo_code.append(f"{self._indent()}]")
        else:
            # No else clause - this is a standalone if
            # Remove variables that were only declared in this block
            # so subsequent if blocks can declare them independently
            self.netlogo_code.append(f"{self._indent()}]")
            # Restore to before this if block to allow subsequent blocks
            # to independently declare the same variables
            self.declared_vars = saved_declared_vars.copy()

    def visit_While(self, node: ast.While) -> None:
        """Convert while loop."""
        test = self._convert_expr(node.test)
        self.netlogo_code.append(f"{self._indent()}while [ {test} ] [")

        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

        self.netlogo_code.append(f"{self._indent()}]")

    def visit_Assign(self, node: ast.Assign) -> None:
        """Convert assignment."""
        for target in node.targets:
            value_str = self._convert_expr(node.value)

            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "create"
                and isinstance(target, ast.Name)
            ):
                self.created_turtles.add(target.id)
                self.netlogo_code.append(f"{self._indent()}set {target.id} {value_str}")

            elif isinstance(target, ast.Attribute):
                obj = self._convert_expr(target.value)
                attr = target.attr

                if obj in self.created_turtles:
                    self.netlogo_code.append(f"{self._indent()}set {attr} {value_str}")
                elif (
                    obj == "self" or obj in self.loop_vars or obj in self.context_params
                ):
                    self.netlogo_code.append(f"{self._indent()}set {attr} {value_str}")
                else:
                    self.netlogo_code.append(
                        f"{self._indent()}; TODO: set [{attr}] of {obj} to {value_str}"
                    )
            else:
                target_str = self._convert_expr(target)
                target_str = target_str.replace("self.", "")

                if isinstance(target, ast.Name) and target.id in self.local_vars:
                    if target.id not in self.declared_vars:
                        self.declared_vars.add(target.id)
                        self.netlogo_code.append(
                            f"{self._indent()}let {target_str} {value_str}"
                        )
                    else:
                        self.netlogo_code.append(
                            f"{self._indent()}set {target_str} {value_str}"
                        )
                else:
                    self.netlogo_code.append(
                        f"{self._indent()}set {target_str} {value_str}"
                    )

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Convert augmented assignment (+=, -=, etc.)."""
        target = self._convert_expr(node.target)
        target = target.replace("self.", "")
        value = self._convert_expr(node.value)

        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
        }

        op = op_map.get(type(node.op), "+")
        self.netlogo_code.append(
            f"{self._indent()}set {target} ({target} {op} {value})"
        )

    def visit_Expr(self, node: ast.Expr) -> None:
        """Convert expression statement."""
        expr_str = self._convert_expr(node.value)
        if expr_str and not isinstance(node.value, ast.Constant):
            self.netlogo_code.append(f"{self._indent()}{expr_str}")

    def visit_Return(self, node: ast.Return) -> None:
        if node.value:
            value = self._convert_expr(node.value)
            self.netlogo_code.append(f"{self._indent()}report {value}")
        else:
            self.netlogo_code.append(f"{self._indent()}stop")

    def visit_Break(self, node: ast.Break) -> None:
        """Convert break statement.

        In NetLogo, break from while loop can be done by setting condition to false,
        but simpler to use stop to exit the current ask/while block.
        """
        self.netlogo_code.append(f"{self._indent()}stop")

    def visit_Continue(self, node: ast.Continue) -> None:
        """Convert continue statement.

        NetLogo doesn't have continue, so we comment it out.
        """
        self.netlogo_code.append(
            f"{self._indent()}; continue (not directly supported in NetLogo)"
        )

    def _convert_expr(self, node: ast.AST) -> str:
        """Convert an expression node to NetLogo code."""
        if isinstance(node, ast.Constant):
            return self._convert_constant(node.value)

        elif isinstance(node, ast.Name):
            return node.id

        elif isinstance(node, ast.Attribute):
            value = self._convert_expr(node.value)
            attr = node.attr

            if value == "self":
                return attr
            elif value in self.loop_vars or value in self.context_params:
                return attr
            elif value.startswith("self."):
                return attr
            else:
                if value in ("patch", "p"):
                    return attr
                return f"[{attr}] of {value}"

        elif isinstance(node, ast.Call):
            return self._convert_call(node)

        elif isinstance(node, ast.BinOp):
            return self._convert_binop(node)

        elif isinstance(node, ast.Compare):
            return self._convert_compare(node)

        elif isinstance(node, ast.BoolOp):
            return self._convert_boolop(node)

        elif isinstance(node, ast.UnaryOp):
            return self._convert_unaryop(node)

        elif isinstance(node, ast.List):
            elements = [self._convert_expr(elt) for elt in node.elts]
            return f"[ {' '.join(elements)} ]"

        elif isinstance(node, ast.Lambda):
            # Convert lambda to NetLogo block
            body = self._convert_expr(node.body)
            return f"[ {body} ]"

        elif isinstance(node, ast.IfExp):
            test = self._convert_expr(node.test)
            body = self._convert_expr(node.body)
            orelse = self._convert_expr(node.orelse)

            if isinstance(node.test, ast.Name):
                is_none_check = (
                    isinstance(node.orelse, ast.Constant) and node.orelse.value is None
                ) or (isinstance(node.body, ast.Constant) and node.body.value is None)
                if is_none_check:
                    test = f"{test} != nobody"

            return f"ifelse-value ({test}) [ {body} ] [ {orelse} ]"

        elif isinstance(node, ast.ListComp):
            if len(node.generators) == 1:
                gen = node.generators[0]
                iter_expr = self._convert_expr(gen.iter)

                if isinstance(gen.target, ast.Name):
                    comp_var = gen.target.id
                    self.loop_vars.add(comp_var)

                conditions = []
                for if_clause in gen.ifs:
                    cond = self._convert_expr(if_clause)
                    if isinstance(gen.target, ast.Name):
                        comp_var = gen.target.id
                        cond = cond.replace(f"{comp_var}.", "")
                        for ctx_param in self.context_params:
                            cond = cond.replace(
                                f" {comp_var} != {ctx_param}", " self != myself"
                            )
                            cond = cond.replace(
                                f" {comp_var} = {ctx_param}", " self = myself"
                            )
                        cond = cond.replace(f"{comp_var} !=", "self !=")
                        cond = cond.replace(f"{comp_var} =", "self =")
                    conditions.append(cond)

                # Remove from loop vars
                if isinstance(gen.target, ast.Name):
                    self.loop_vars.discard(gen.target.id)

                if conditions:
                    condition_str = " and ".join(f"({c})" for c in conditions)
                    return f"{iter_expr} with [ {condition_str} ]"
                else:
                    return iter_expr
            # Fallback for complex comprehensions
            return "[ ]"

        elif isinstance(node, ast.JoinedStr):
            # Handle f-strings: f"text {expr}" -> (word "text " expr)
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    # String literal part - escape special characters and keep on one line
                    string_val = value.value
                    # Escape backslashes first, then newlines, tabs, quotes
                    string_val = string_val.replace("\\", "\\\\")
                    string_val = string_val.replace("\n", "\\n")
                    string_val = string_val.replace("\t", "\\t")
                    string_val = string_val.replace('"', '\\"')
                    parts.append(f'"{string_val}"')
                elif isinstance(value, ast.FormattedValue):
                    # Expression part - convert and format
                    expr_str = self._convert_expr(value.value)
                    parts.append(expr_str)

            if len(parts) == 1:
                return parts[0]
            else:
                return f"(word {' '.join(parts)})"

        else:
            # Fallback: try to unparse and normalize quotes
            try:
                result = ast.unparse(node)
                # Normalize fancy Unicode quotes to standard ASCII quotes
                result = result.replace("'", "'").replace("'", "'")
                result = result.replace(""", '"').replace(""", '"')
                return result
            except Exception:
                return str(node)

    def _convert_constant(self, value) -> str:
        """Convert Python constant to NetLogo."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # NetLogo color names don't need quotes
            netlogo_colors = {
                "black",
                "gray",
                "white",
                "red",
                "orange",
                "brown",
                "yellow",
                "green",
                "lime",
                "turquoise",
                "cyan",
                "sky",
                "blue",
                "violet",
                "magenta",
                "pink",
            }
            if value.lower() in netlogo_colors:
                return value.lower()
            else:
                # Escape special characters in strings
                escaped_value = value.replace("\\", "\\\\")  # Escape backslashes first
                escaped_value = escaped_value.replace("\n", "\\n")  # Escape newlines
                escaped_value = escaped_value.replace("\t", "\\t")  # Escape tabs
                escaped_value = escaped_value.replace('"', '\\"')  # Escape quotes
                return f'"{escaped_value}"'
        elif value is None:
            return "nobody"
        else:
            return str(value)

    def _convert_call(self, node: ast.Call) -> str:
        """Convert function/method call to NetLogo."""
        func_name = ""

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            obj = self._convert_expr(node.func.value)
            method = node.func.attr

            # Handle agentset methods
            if method == "all":
                return obj.replace("self.", "")
            elif method == "filter":
                # Convert Django-style filter to NetLogo with
                if node.keywords:
                    conditions = []
                    for kw in node.keywords:
                        if kw.arg and "__" in kw.arg:
                            # field__op=value -> field op value
                            parts = kw.arg.split("__")
                            field = parts[0]
                            op = parts[1] if len(parts) > 1 else "eq"
                            value = self._convert_expr(kw.value)

                            op_map = {
                                "gt": ">",
                                "lt": "<",
                                "gte": ">=",
                                "lte": "<=",
                                "eq": "=",
                            }
                            nl_op = op_map.get(op, "=")
                            conditions.append(f"{field} {nl_op} {value}")
                        elif kw.arg:
                            # Simple field=value
                            field = kw.arg
                            value = self._convert_expr(kw.value)
                            conditions.append(f"{field} = {value}")

                    condition_str = " and ".join(conditions)
                    obj = obj.replace("self.", "")
                    return f"{obj} with [ {condition_str} ]"
                elif node.args:
                    # filter(lambda t: t.infected_time > 0)
                    if isinstance(node.args[0], ast.Lambda):
                        lambda_node = node.args[0]
                        # Track lambda parameter temporarily
                        if lambda_node.args.args:
                            lambda_param = lambda_node.args.args[0].arg
                            self.loop_vars.add(lambda_param)

                        condition = self._convert_expr(lambda_node.body)

                        # Remove lambda parameter from tracking
                        if lambda_node.args.args:
                            self.loop_vars.discard(lambda_node.args.args[0].arg)

                        obj = obj.replace("self.", "")
                        return f"{obj} with [ {condition} ]"

            elif method == "count":
                obj = obj.replace("self.", "")
                return f"count {obj}"

            elif method == "sample":
                if node.args:
                    n = self._convert_expr(node.args[0])
                    obj = obj.replace("self.", "")
                    return f"n-of {n} {obj}"

            elif method == "one":
                obj = obj.replace("self.", "")
                return f"one-of {obj}"

            elif method == "min_by" or method == "max_by":
                if node.args:
                    # Assume it's a lambda
                    obj = obj.replace("self.", "")
                    prefix = "min-one-of" if method == "min_by" else "max-one-of"
                    if isinstance(node.args[0], ast.Lambda):
                        lambda_node = node.args[0]
                        # Track lambda parameter temporarily
                        if lambda_node.args.args:
                            lambda_param = lambda_node.args.args[0].arg
                            self.loop_vars.add(lambda_param)

                        reporter = self._convert_expr(lambda_node.body)

                        # Remove lambda parameter from tracking
                        if lambda_node.args.args:
                            self.loop_vars.discard(lambda_node.args.args[0].arg)

                        return f"{prefix} {obj} [ {reporter} ]"

            elif method in (
                "forward",
                "back",
                "right",
                "left",
                "face",
                "move_to",
                "die",
            ):
                # Turtle commands
                args_list = []
                for arg in node.args:
                    arg_str = self._convert_expr(arg)
                    # Special case: move_to with loop variable (e.g., patch) should use patch-here
                    if method == "move_to" and arg_str in self.loop_vars:
                        if arg_str in ("patch", "p"):
                            args_list.append("patch-here")
                        else:
                            # For other loop vars (like turtle), skip the argument
                            continue
                    else:
                        args_list.append(arg_str)

                nl_method = method.replace("_", "-")
                args_str = " ".join(args_list)
                if args_str:
                    return f"{nl_method} {args_str}"
                else:
                    return nl_method

            elif method == "distance_to":
                if node.args:
                    target = self._convert_expr(node.args[0])
                    # In min-one-of/max-one-of context with lambda parameter,
                    # convert turtle.distance_to(p) -> distance myself
                    # where p is the implicit patch/agent in the block
                    if target in self.loop_vars:
                        # The target is the lambda parameter (implicit in NetLogo block)
                        # The object doing the distance check becomes 'myself'
                        return "distance myself"
                    return f"distance {target}"

            elif method == "turtles_in_radius":
                if node.args:
                    radius = self._convert_expr(node.args[0])
                    return f"other turtles in-radius {radius}"

            elif method == "turtles_in_cone":
                if len(node.args) >= 2:
                    distance = self._convert_expr(node.args[0])
                    angle = self._convert_expr(node.args[1])
                    return f"other turtles in-cone {distance} {angle}"

            elif method == "neighbors_within":
                if node.args:
                    distance = self._convert_expr(node.args[0])
                    return f"other turtles in-radius {distance}"

            elif method == "create":
                if node.args:
                    n = self._convert_expr(node.args[0])
                    obj = obj.replace("self.", "")
                    return f"create-{obj} {n}"

            elif method == "patch":
                return "patch-here"

            else:
                # Generic method call
                obj = obj.replace("self.", "")

                # Special case: self.method() -> just call method as a procedure
                if obj == "self":
                    # Convert positional and keyword arguments
                    args_list = []
                    # Add positional arguments, but skip loop variables (they're implicit in ask context)
                    for arg in node.args:
                        arg_str = self._convert_expr(arg)
                        # Skip if this argument is a loop variable (e.g., 'turtle' in ask turtles)
                        if arg_str not in self.loop_vars:
                            args_list.append(arg_str)
                    # Add keyword arguments (just the values, NetLogo uses positional)
                    for kw in node.keywords:
                        args_list.append(self._convert_expr(kw.value))

                    args_str = " ".join(args_list)
                    if args_str:
                        return f"{method} {args_str}"
                    else:
                        return method

                # Other object method calls
                args_str = " ".join(self._convert_expr(arg) for arg in node.args)
                if args_str:
                    return f"{obj} {method} {args_str}"
                else:
                    return f"{obj} {method}"

        # Handle standalone functions
        if func_name == "patches":
            return "patches"
        elif func_name == "turtles":
            return "turtles"
        elif func_name == "print":
            # Convert Python print() to NetLogo print
            if node.args:
                arg = self._convert_expr(node.args[0])
                return f"print {arg}"
            return "print"
        elif func_name == "reset_ticks":
            return "reset-ticks"
        elif func_name == "tick":
            return "tick"
        elif func_name == "clear_all":
            return "clear-all"
        elif func_name == "random_float":
            if node.args:
                arg = self._convert_expr(node.args[0])
                return f"random-float {arg}"
            return "random-float 100"
        elif func_name == "random":
            if node.args:
                arg = self._convert_expr(node.args[0])
                return f"random {arg}"
            return "random 100"
        elif func_name == "min":
            args_str = " ".join(self._convert_expr(arg) for arg in node.args)
            return f"min (list {args_str})"
        elif func_name == "max":
            args_str = " ".join(self._convert_expr(arg) for arg in node.args)
            return f"max (list {args_str})"
        elif func_name == "len":
            if node.args:
                arg = self._convert_expr(node.args[0])
                # In NetLogo: 'count' for agentsets, 'length' for strings/lists
                # Heuristic: if the argument is a simple variable name (likely an agentset),
                # use 'count'. If it's a literal list/string, use 'length'.
                # This handles the common case where list comprehensions become agentset filters
                arg_node = node.args[0]
                if isinstance(arg_node, ast.Name):
                    # Variable reference - likely an agentset, use count
                    return f"count {arg}"
                else:
                    # Literal or expression - use length
                    return f"length {arg}"
        elif func_name == "mean":
            if node.args:
                arg = self._convert_expr(node.args[0])
                return f"mean {arg}"
        elif func_name == "setattr":
            # setattr(obj, 'attr', value) -> set [attr] of obj value
            if len(node.args) >= 3:
                obj = self._convert_expr(node.args[0])
                attr = self._convert_expr(node.args[1]).strip('"')
                value = self._convert_expr(node.args[2])
                obj = obj.replace("self.", "")
                return f"set {attr} {value}"
        else:
            # Generic function call
            args_str = " ".join(self._convert_expr(arg) for arg in node.args)
            return f"{func_name} {args_str}" if args_str else func_name

        return ""

    def _convert_binop(self, node: ast.BinOp) -> str:
        """Convert binary operation."""
        # Special case: random_float() * 100 -> random-float 100
        if (
            isinstance(node.op, ast.Mult)
            and isinstance(node.left, ast.Call)
            and isinstance(node.left.func, ast.Name)
            and node.left.func.id == "random_float"
            and not node.left.args
            and isinstance(node.right, ast.Constant)
        ):
            # random_float() * N -> random-float N
            return f"random-float {node.right.value}"

        left = self._convert_expr(node.left)
        right = self._convert_expr(node.right)

        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "mod",
            ast.Pow: "^",
        }

        op = op_map.get(type(node.op), "+")
        return f"({left} {op} {right})"

    def _convert_compare(self, node: ast.Compare) -> str:
        """Convert comparison."""
        left = self._convert_expr(node.left)

        op_map = {
            ast.Eq: "=",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }

        parts = [left]
        for op, comparator in zip(node.ops, node.comparators):
            nl_op = op_map.get(type(op), "=")
            comp = self._convert_expr(comparator)

            # Special case: comparing loop var to context param
            # t != turtle -> self != myself
            if isinstance(node.left, ast.Name) and isinstance(comparator, ast.Name):
                left_name = node.left.id
                right_name = comparator.id
                if left_name in self.loop_vars and right_name in self.context_params:
                    parts = ["self"]
                    comp = "myself"

            parts.append(nl_op)
            parts.append(comp)

        return " ".join(parts)

    def _convert_boolop(self, node: ast.BoolOp) -> str:
        """Convert boolean operation."""
        op = "and" if isinstance(node.op, ast.And) else "or"
        values = [self._convert_expr(v) for v in node.values]
        return f" {op} ".join(f"({v})" for v in values)

    def _convert_unaryop(self, node: ast.UnaryOp) -> str:
        """Convert unary operation."""
        operand = self._convert_expr(node.operand)

        if isinstance(node.op, ast.Not):
            return f"not ({operand})"
        elif isinstance(node.op, ast.USub):
            return f"(- {operand})"
        else:
            return operand
