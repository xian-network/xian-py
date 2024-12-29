import ast
import astor


class CustomSourceGenerator(astor.SourceGenerator):
    """Custom source generator that handles formatting better"""

    def __init__(self, *args, **kwargs):
        kwargs['indent_with'] = '    '  # Use 4 spaces for indentation
        super().__init__(*args, **kwargs)

    def write(self, *params):
        """Track line length when writing"""
        for item in params:
            self.current_line_length += len(str(item))
        super().write(*params)

    def newline(self, node=None, extra=0):
        """Reset line length counter on newline"""
        self.current_line_length = 0
        super().newline(node, extra)

    def visit_Str(self, node):
        """Use double quotes for strings"""
        val = str(node.s)
        if '"' in val and "'" not in val:
            self.write("'" + val + "'")
        else:
            self.write('"' + val.replace('"', '\\"') + '"')

    def visit_JoinedStr(self, node):
        """Handle f-strings with double quotes"""
        self.write('f"')
        for value in node.values:
            if isinstance(value, ast.Str):
                self.write(value.s)
            elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                self.write(value.value)
            elif isinstance(value, ast.FormattedValue):
                self.write('{')
                self.visit(value.value)
                if value.conversion != -1:
                    self.write('!' + chr(value.conversion))
                if value.format_spec is not None:
                    self.write(':')
                    self.visit(value.format_spec)
                self.write('}')
            else:
                self.write('{')
                self.visit(value)
                self.write('}')
        self.write('"')

    def visit_Num(self, node):
        """Format numbers without scientific notation"""
        if isinstance(node.n, float):
            self.write(f"{node.n:.10f}".rstrip('0').rstrip('.'))
        else:
            self.write(str(node.n))


class ContractDecompiler(ast.NodeTransformer):
    def __init__(self):
        self.contract_name = None
        self.orm_vars = set()
        self.comments = {}

    def decompile(self, source: str) -> str:
        """Decompile source code and return as a string"""
        tree = ast.parse(source)
        # First pass to collect ORM variables and comments
        self.collect_orm_vars(tree)
        # Second pass to transform the code
        transformed = self.visit(tree)
        # Generate source code using the custom generator
        generator = CustomSourceGenerator()
        generator.visit(transformed)
        return ''.join(generator.result)

    def collect_orm_vars(self, node):
        """First pass to collect all ORM variable names"""
        for node in ast.walk(node):
            if isinstance(node, ast.Assign):
                if (isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Name) and
                        any(kw.arg == 'contract' for kw in node.value.keywords)):

                    # Get the original name from the 'name' keyword argument
                    name_kw = next(kw for kw in node.value.keywords if kw.arg == 'name')
                    if isinstance(name_kw.value, ast.Str):
                        self.orm_vars.add(name_kw.value.s)

    def visit_Name(self, node):
        """Remove __ prefix from variable and function names"""
        if isinstance(node.id, str):
            if node.id.startswith('__') and node.id[2:] in self.orm_vars:
                node.id = node.id[2:]
            elif node.id.startswith('__'):
                node.id = node.id[2:]
        return node

    def visit_FunctionDef(self, node):
        """Transform function definitions back to original form"""
        self.generic_visit(node)

        # Handle seed/init function
        if node.name == '____':
            node.name = 'seed'
            node.decorator_list = [ast.Name(id='construct', ctx=ast.Load())]
            return node

        # Handle exported functions
        if node.decorator_list:
            decorator = node.decorator_list[0]
            if isinstance(decorator, ast.Call):
                # Specifically for export calls, replace with simple @export
                if (isinstance(decorator.func, ast.Name) and
                        decorator.func.id == 'export' and
                        len(decorator.args) == 1 and
                        isinstance(decorator.args[0], ast.Constant)):
                    node.decorator_list = [ast.Name(id='export', ctx=ast.Load())]
            elif isinstance(decorator, ast.Name) and decorator.id.startswith('__'):
                decorator.id = decorator.id[2:]

        # Remove __ prefix from function name if it exists
        if node.name.startswith('__'):
            node.name = node.name[2:]

        return node

    def visit_Call(self, node):
        """Handle function calls, including decimal removal"""
        self.generic_visit(node)

        if (isinstance(node.func, ast.Name) and
                node.func.id == 'decimal' and
                len(node.args) == 1 and
                isinstance(node.args[0], (ast.Str, ast.Constant))):

            value = node.args[0].s if isinstance(node.args[0], ast.Str) else node.args[0].value
            try:
                float_val = float(value)
                return ast.Num(n=float_val)
            except ValueError:
                return node

        return node

    def visit_Assign(self, node):
        """Transform ORM variable assignments"""
        self.generic_visit(node)

        if (isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Name)):

            # Remove contract and name keywords
            if any(kw.arg == 'contract' for kw in node.value.keywords):
                node.value.keywords = [kw for kw in node.value.keywords
                                       if kw.arg == 'default_value']
        return node