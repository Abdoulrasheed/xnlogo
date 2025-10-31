"""Translate Python statements to NetLogo code."""

from __future__ import annotations

import ast
from typing import Any


class NetLogoTranslator(ast.NodeVisitor):
    """Convert Python AST to NetLogo code strings."""

    def __init__(self) -> None:
        self.agent_fields: set[str] = set()

    def translate(self, source: str, agent_fields: set[str] | None = None) -> str:
        """Translate Python source to NetLogo code."""
        if agent_fields:
            self.agent_fields = agent_fields

        try:
            tree = ast.parse(source)
            # Handle single statement
            if len(tree.body) == 1:
                return self.visit(tree.body[0])
            # Multiple statements
            return "\n".join(self.visit(stmt) for stmt in tree.body)
        except SyntaxError:
            # If we can't parse it, return as-is with a comment
            return f"; UNPARSED: {source}"

    def visit_Assign(self, node: ast.Assign) -> str:
        """Translate assignment: self.field = expr -> set field expr"""
        # Handle single target (most common case)
        if len(node.targets) == 1:
            target = node.targets[0]

            # self.field = value -> set field value
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    field_name = target.attr
                    value_expr = self.visit(node.value)
                    return f"set {field_name} {value_expr}"

            # Subscript: var["key"] = value or self.dict["key"] = value
            if isinstance(target, ast.Subscript):
                value_expr = self.visit(node.value)
                # In NetLogo, we can't use dict syntax, so this needs special handling
                # For now, treat as property access if it's a string literal
                if isinstance(target.slice, ast.Constant) and isinstance(
                    target.slice.value, str
                ):
                    # turtle["speed"] -> set speed value (if turtle is implicit)
                    return f"set {target.slice.value} {value_expr}"
                # Fallback for non-string subscripts
                obj = self.visit(target.value)
                key = self.visit(target.slice)
                return f"; TODO: set {obj}[{key}] to {value_expr}"

            # Simple variable assignment: var = value -> set var value
            if isinstance(target, ast.Name):
                var_name = target.id
                value_expr = self.visit(node.value)
                return f"set {var_name} {value_expr}"

        # Fallback: use ast.unparse
        return ast.unparse(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> str:
        """Translate augmented assignment: self.x += 1 -> set x x + 1"""
        # self.field += value
        if isinstance(node.target, ast.Attribute):
            if (
                isinstance(node.target.value, ast.Name)
                and node.target.value.id == "self"
            ):
                field_name = node.target.attr
                current = field_name
                op = self.visit(node.op)
                value = self.visit(node.value)
                return f"set {field_name} {current} {op} {value}"

        # var["key"] -= value -> set key (key - value)
        if isinstance(node.target, ast.Subscript):
            if isinstance(node.target.slice, ast.Constant) and isinstance(
                node.target.slice.value, str
            ):
                field_name = node.target.slice.value
                current = field_name
                op = self.visit(node.op)
                value = self.visit(node.value)
                return f"set {field_name} ({current} {op} {value})"

        # Regular variable: var += value
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            current = var_name
            op = self.visit(node.op)
            value = self.visit(node.value)
            return f"set {var_name} ({current} {op} {value})"

        return ast.unparse(node)

    def visit_Attribute(self, node: ast.Attribute) -> str:
        """Translate attribute access: self.field -> field"""
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return node.attr
        # other attribute access kept as-is for now (e.g., turtle.heading)
        return ast.unparse(node)

    def visit_Subscript(self, node: ast.Subscript) -> str:
        """Translate subscript access."""
        # string literal subscript - treat as property access
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            return node.slice.value

        # numeric subscript - list indexing: lst[0] -> item 0 lst
        if isinstance(node.slice, (ast.Constant, ast.Name, ast.UnaryOp)):
            list_expr = self.visit(node.value)
            index_expr = self.visit(node.slice)
            return f"item {index_expr} {list_expr}"

        # slice - lst[1:3] -> sublist lst 1 3
        if isinstance(node.slice, ast.Slice):
            list_expr = self.visit(node.value)
            start = self.visit(node.slice.lower) if node.slice.lower else "0"
            stop = (
                self.visit(node.slice.upper)
                if node.slice.upper
                else f"length {list_expr}"
            )
            # NetLogo sublist uses inclusive start, exclusive stop
            return f"sublist {list_expr} {start} {stop}"

        return ast.unparse(node)

    def visit_Return(self, node: ast.Return) -> str:
        """Translate return statement."""
        if node.value is None:
            return "stop"  # NetLogo's return without value
        value = self.visit(node.value)
        return f"report {value}"  # NetLogo's return with value

    def visit_BinOp(self, node: ast.BinOp) -> str:
        """Translate binary operations."""
        left = self.visit(node.left)
        op = self.visit(node.op)
        right = self.visit(node.right)
        return f"({left} {op} {right})"

    def visit_Add(self, node: ast.Add) -> str:
        return "+"

    def visit_Sub(self, node: ast.Sub) -> str:
        return "-"

    def visit_Mult(self, node: ast.Mult) -> str:
        return "*"

    def visit_Div(self, node: ast.Div) -> str:
        return "/"

    def visit_Mod(self, node: ast.Mod) -> str:
        return "mod"

    def visit_Pow(self, node: ast.Pow) -> str:
        return "^"

    def visit_FloorDiv(self, node: ast.FloorDiv) -> str:
        # NetLogo doesn't have floor division, use int(a / b)
        return "/"  # Caller should wrap in floor or int

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        """Translate unary operations."""
        operand = self.visit(node.operand)
        op = self.visit(node.op)

        # Special case: negative constant should not have space
        if isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            return f"-{operand}"

        return f"{op} {operand}"

    def visit_USub(self, node: ast.USub) -> str:
        """Unary minus."""
        return "-"

    def visit_Not(self, node: ast.Not) -> str:
        """Logical not."""
        return "not"

    def visit_Compare(self, node: ast.Compare) -> str:
        """Translate comparison operations."""
        # single comparison (most common)
        if len(node.ops) == 1 and len(node.comparators) == 1:
            left = self.visit(node.left)
            op = node.ops[0]
            right = self.visit(node.comparators[0])

            # 'in' and 'not in' use reversed argument order
            if isinstance(op, (ast.In, ast.NotIn)):
                op_str = self.visit(op)
                # 'x in lst' -> 'member? x lst'
                return f"{op_str} {left} {right}"

            op_str = self.visit(op)
            return f"({left} {op_str} {right})"

        # chained comparisons: a < b < c -> (a < b) and (b < c)
        parts = []
        left = node.left
        for op, comparator in zip(node.ops, node.comparators):
            left_str = self.visit(left)
            op_str = self.visit(op)
            right_str = self.visit(comparator)

            if isinstance(op, (ast.In, ast.NotIn)):
                parts.append(f"{op_str} {left_str} {right_str}")
            else:
                parts.append(f"({left_str} {op_str} {right_str})")
            left = comparator

        return " and ".join(parts)

    def visit_Eq(self, node: ast.Eq) -> str:
        return "="

    def visit_NotEq(self, node: ast.NotEq) -> str:
        return "!="

    def visit_Lt(self, node: ast.Lt) -> str:
        return "<"

    def visit_LtE(self, node: ast.LtE) -> str:
        return "<="

    def visit_Gt(self, node: ast.Gt) -> str:
        return ">"

    def visit_GtE(self, node: ast.GtE) -> str:
        return ">="

    def visit_In(self, node: ast.In) -> str:
        return "member?"

    def visit_NotIn(self, node: ast.NotIn) -> str:
        return "not member?"

    def visit_BoolOp(self, node: ast.BoolOp) -> str:
        """Translate boolean operations (and/or)."""
        op_str = self.visit(node.op)
        values = [self.visit(v) for v in node.values]
        return f" {op_str} ".join(values)

    def visit_And(self, node: ast.And) -> str:
        return "and"

    def visit_Or(self, node: ast.Or) -> str:
        return "or"

    def visit_If(self, node: ast.If) -> str:
        """Translate if statements."""
        condition = self.visit(node.test)

        body_stmts = [self.visit(stmt) for stmt in node.body]
        body = "\n  ".join(body_stmts)

        if not node.orelse:
            return f"if {condition} [\n  {body}\n]"

        # elif: check if else clause is another if
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            else_part = self.visit(node.orelse[0])
            return f"if {condition} [\n  {body}\n]\n{else_part}"

        # else
        else_stmts = [self.visit(stmt) for stmt in node.orelse]
        else_body = "\n  ".join(else_stmts)
        return f"if {condition} [\n  {body}\n]\n[\n  {else_body}\n]"

    def visit_For(self, node: ast.For) -> str:
        """Translate for loops."""
        # for i in range(...) pattern
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range":
                body_stmts = [self.visit(stmt) for stmt in node.body]
                body = "\n  ".join(body_stmts)

                args = node.iter.args

                # range(n) - simple case
                if len(args) == 1:
                    n = self.visit(args[0])
                    return f"repeat {n} [\n  {body}\n]"

                # range(start, stop) or range(start, stop, step)
                if len(args) >= 2:
                    if isinstance(node.target, ast.Name):
                        var = node.target.id
                        start = self.visit(args[0])
                        stop = self.visit(args[1])
                        step = self.visit(args[2]) if len(args) == 3 else "1"

                        # generate: set i start, while [i < stop] [body, set i (i + step)]
                        if len(args) == 3:
                            init = f"set {var} {start}"
                            cond = (
                                f"{var} < {stop}"  # simplified - assumes positive step
                            )
                            update = f"set {var} ({var} + {step})"
                            return f"{init}\nwhile [{cond}] [\n  {body}\n  {update}\n]"
                        else:
                            init = f"set {var} {start}"
                            cond = f"{var} < {stop}"
                            update = f"set {var} ({var} + 1)"
                            return f"{init}\nwhile [{cond}] [\n  {body}\n  {update}\n]"

        # generic for-each (needs more sophisticated handling)
        return f"; TODO: for {ast.unparse(node.target)} in {ast.unparse(node.iter)}"

    def visit_While(self, node: ast.While) -> str:
        """Translate while loops."""
        condition = self.visit(node.test)
        body_stmts = [self.visit(stmt) for stmt in node.body]
        body = "\n  ".join(body_stmts)
        return f"while [{condition}] [\n  {body}\n]"

    def visit_IfExp(self, node: ast.IfExp) -> str:
        """Translate ternary/conditional expressions: x if cond else y."""
        condition = self.visit(node.test)
        true_val = self.visit(node.body)
        false_val = self.visit(node.orelse)
        return f"ifelse-value {condition} {true_val} {false_val}"

    def visit_Call(self, node: ast.Call) -> str:
        """Translate function/method calls."""
        # method call: self.method(args) or var.method(args)
        if isinstance(node.func, ast.Attribute):
            obj = node.func.value
            method_name = node.func.attr

            # self.method(args) -> method args
            if isinstance(obj, ast.Name) and obj.id == "self":
                args = [self._visit_arg(arg) for arg in node.args]

                if not args:
                    return method_name

                args_str = " ".join(args)
                return f"{method_name} {args_str}"

            # other method calls: var.method(args) -> method args (simplified)
            else:
                args = [self._visit_arg(arg) for arg in node.args]
                method_map = {
                    "ask": "ask",
                    "create": "create-turtles",
                    "setxy": "setxy",
                    "set_heading": "set heading",
                    "forward": "forward",
                    "right": "right",
                    "in_radius": "in-radius",
                    "patch_here": "patch-here",
                }

                nl_method = method_map.get(method_name, method_name)

                if not args:
                    return nl_method

                args_str = " ".join(args)
                return f"{nl_method} {args_str}"

        # built-in or standalone function call
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            args = [self._visit_arg(arg) for arg in node.args]

            builtin_map = {
                "abs": "abs",
                "round": "round",
                "int": "floor",
                "float": "",  # NetLogo doesn't need explicit float conversion
                "len": "length",
                "max": "max",
                "min": "min",
                "print": "print",
                "sum": "sum",
            }

            nl_func = builtin_map.get(func_name, func_name)

            if not args:
                return nl_func if nl_func else func_name

            args_str = " ".join(args)
            if nl_func:
                return f"{nl_func} {args_str}"
            return f"{func_name} {args_str}"

        return ast.unparse(node)

    def _visit_arg(self, arg: ast.expr) -> str:
        """Visit a function argument, with special handling for strings and lists."""
        # string literals in function calls should be without quotes for NetLogo code
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            if any(
                keyword in arg.value for keyword in ["set ", "ask", "create", "random"]
            ):
                return arg.value  # return without quotes
            return f'"{arg.value}"'  # keep quotes for regular strings

        # list literals -> space-separated items
        if isinstance(arg, ast.List):
            items = [self._visit_arg(elt) for elt in arg.elts]
            return " ".join(items)

        return self.visit(arg)

    def visit_Constant(self, node: ast.Constant) -> str:
        """Translate constants."""
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    def visit_List(self, node: ast.List) -> str:
        """Translate list literals."""
        items = [self.visit(elt) for elt in node.elts]
        items_str = " ".join(items)
        return f"[{items_str}]"

    def visit_Name(self, node: ast.Name) -> str:
        """Translate variable names."""
        return node.id

    def visit_Expr(self, node: ast.Expr) -> str:
        """Translate expression statements."""
        return self.visit(node.value)

    def generic_visit(self, node: Any) -> str:
        """Fallback for unhandled node types."""
        return ast.unparse(node)


def translate_statement(source: str, agent_fields: set[str] | None = None) -> str:
    """Translate a Python statement to NetLogo code."""
    translator = NetLogoTranslator()
    return translator.translate(source, agent_fields)
