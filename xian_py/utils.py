import base64
import json
import ast


def decode_dict(encoded_dict: str) -> dict:
    decoded_data = decode_str(encoded_dict)
    decoded_tx = bytes.fromhex(decoded_data).decode('utf-8')
    return json.loads(decoded_tx)


def decode_str(encoded_data: str) -> str:
    decoded_bytes = base64.b64decode(encoded_data)
    return decoded_bytes.decode('utf-8')

def remove_trailing_double_underscores(code_str):
    class RemoveDoubleUnderscores(ast.NodeTransformer):
        def strip_double_underscores(self, name):
            # Remove leading and trailing double underscores
            while name.startswith('__') or name.endswith('__'):
                if name.startswith('__'):
                    name = name[2:]
                if name.endswith('__'):
                    name = name[:-2]
            return name

        def visit_FunctionDef(self, node):
            # Update function name
            node.name = self.strip_double_underscores(node.name)
            # Update decorators
            node.decorator_list = [self.visit(decorator) for decorator in node.decorator_list]
            self.generic_visit(node)
            return node

        def visit_Name(self, node):
            # Update variable names
            node.id = self.strip_double_underscores(node.id)
            return node

        def visit_Attribute(self, node):
            # Update attribute names
            node.attr = self.strip_double_underscores(node.attr)
            self.generic_visit(node)
            return node

        def visit_keyword(self, node):
            # Update keyword argument names
            node.arg = self.strip_double_underscores(node.arg) if node.arg else None
            self.generic_visit(node)
            return node

        def visit_arguments(self, node):
            # Update function argument names
            for arg in node.args + node.kwonlyargs:
                arg.arg = self.strip_double_underscores(arg.arg)
            self.generic_visit(node)
            return node

        def visit_arg(self, node):
            # Update single argument
            node.arg = self.strip_double_underscores(node.arg)
            return node

    # Parse the code into an AST
    tree = ast.parse(code_str)
    # Transform the AST
    transformer = RemoveDoubleUnderscores()
    new_tree = transformer.visit(tree)
    # Convert the AST back to code using ast.unparse
    new_code = ast.unparse(new_tree)
    return new_code
