import ast
import astor
from typing import Optional


class CustomSourceGenerator(astor.SourceGenerator):
    """Custom source generator with predictable formatting."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("indent_with", "    ")
        super().__init__(*args, **kwargs)
        self.current_line_length = 0

    def write(self, *params):
        for item in params:
            self.current_line_length += len(str(item))
        super().write(*params)

    def newline(self, node=None, extra=0):
        self.current_line_length = 0
        super().newline(node=node, extra=extra)

    def visit_Str(self, node):
        """Emit string literals with consistent quoting."""
        value = str(node.s)
        if '"' in value and "'" not in value:
            self.write("'" + value + "'")
        else:
            escaped = value.replace('"', '\\"')
            self.write('"' + escaped + '"')

    def visit_JoinedStr(self, node):
        """Handle f-strings using double quotes."""
        self.write('f"')
        for value in node.values:
            if isinstance(value, ast.Str):
                self.write(value.s)
            elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                self.write(value.value)
            elif isinstance(value, ast.FormattedValue):
                self.write("{")
                self.visit(value.value)
                if value.conversion != -1:
                    self.write("!" + chr(value.conversion))
                if value.format_spec is not None:
                    self.write(":")
                    self.visit(value.format_spec)
                self.write("}")
            else:
                self.write("{")
                self.visit(value)
                self.write("}")
        self.write('"')

    def visit_Num(self, node):
        """Avoid scientific notation when possible."""
        if isinstance(node.n, float):
            self.write(f"{node.n:.10f}".rstrip("0").rstrip("."))
        else:
            self.write(str(node.n))


class ContractDecompiler(ast.NodeTransformer):
    """Reconstruct readable contract source from compiled form."""

    def __init__(self):
        super().__init__()
        self.orm_vars: set[str] = set()

    def decompile(self, source: str) -> str:
        """Return best-effort decompiled source, falling back gracefully."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._normalize_output(source)

        self.orm_vars.clear()
        self._collect_orm_vars(tree)

        transformed = self.visit(tree)
        ast.fix_missing_locations(transformed)

        generator = CustomSourceGenerator()
        generator.visit(transformed)
        rendered = "".join(generator.result)
        return self._normalize_output(rendered)

    def _collect_orm_vars(self, node: ast.AST) -> None:
        """Record underlying names for ORM variables to strip prefixes safely."""
        for child in ast.walk(node):
            if isinstance(child, ast.Assign) and isinstance(child.value, ast.Call):
                if not isinstance(child.value.func, ast.Name):
                    continue
                for kw in child.value.keywords or []:
                    if kw.arg == "name" and isinstance(
                            getattr(kw, "value", None), ast.Str
                    ):
                        self.orm_vars.add(kw.value.s)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        ident = node.id
        if ident.startswith("__"):
            candidate = ident[2:]
            node.id = candidate if candidate in self.orm_vars else candidate
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)

        if node.name == "____":
            node.name = "seed"
            node.decorator_list = [ast.Name(id="construct", ctx=ast.Load())]
            return node

        if node.decorator_list:
            first = node.decorator_list[0]
            if isinstance(first, ast.Call):
                if (
                        isinstance(first.func, ast.Name)
                        and first.func.id in {"export", "__export"}
                        and first.args
                        and isinstance(first.args[0], ast.Constant)
                ):
                    node.decorator_list = [ast.Name(id="export", ctx=ast.Load())]
            elif isinstance(first, ast.Name) and first.id.startswith("__"):
                first.id = first.id[2:]

        if node.name.startswith("__"):
            node.name = node.name[2:]

        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)

        func = node.func
        if isinstance(func, ast.Name) and func.id == "decimal" and node.args:
            arg = node.args[0]
            value: Optional[str] = None
            if isinstance(arg, ast.Str):
                value = arg.s
            elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                value = arg.value
            if value is not None:
                try:
                    return ast.Num(n=float(value))
                except ValueError:
                    pass
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        self.generic_visit(node)

        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if any(kw.arg == "contract" for kw in value.keywords or []):
                value.keywords = [
                    kw for kw in value.keywords if kw.arg == "default_value"
                ]
        return node

    @staticmethod
    def _normalize_output(text: str) -> str:
        """Collapse repeated blank lines and ensure a trailing newline."""
        lines = text.splitlines()
        normalized: list[str] = []
        blank = False
        for raw in lines:
            line = raw.rstrip()
            if line:
                normalized.append(line)
                blank = False
            else:
                if not blank:
                    normalized.append("")
                blank = True

        collapsed = "\n".join(normalized).strip("\n")
        return collapsed + "\n" if collapsed else ""
