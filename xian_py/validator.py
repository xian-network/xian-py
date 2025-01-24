import ast

from enum import Enum, auto
from typing import List, Set, Dict


class XianStandard(Enum):
    XSC001 = auto()
    #XSC002 = auto()  # Future standards


class ValidatorBase(ast.NodeVisitor):
    def validate(self) -> tuple[bool, List[str]]:
        raise NotImplementedError


class ValidatorXSC001(ValidatorBase):
    def __init__(self):
        self.required_variables = {'balances', 'metadata'}
        self.required_functions = {
            'seed': set(),
            'change_metadata': {'key', 'value'},
            'transfer': {'amount', 'to'},
            'approve': {'amount', 'to'},
            'transfer_from': {'amount', 'to', 'main_account'},
            'balance_of': {'account'}
        }
        self.found_variables: Set[str] = set()
        self.found_functions: Dict[str, Set[str]] = {}
        self.has_constructor = False
        self.is_hash_type: Dict[str, bool] = {}
        self.metadata_fields = {
            'token_name',
            'token_symbol',
            'token_logo_url',
            'token_website',
            'operator'
        }
        self.found_metadata_fields: Set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Call):
            var_name = node.targets[0].id
            self.found_variables.add(var_name)

            if isinstance(node.value.func, ast.Name) and node.value.func.id == 'Hash':
                self.is_hash_type[var_name] = True

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        func_name = node.name
        args = {arg.arg for arg in node.args.args}
        self.found_functions[func_name] = args

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'construct':
                self.has_constructor = True

        if func_name == 'seed':
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    if isinstance(stmt.targets[0], ast.Subscript):
                        if isinstance(stmt.targets[0].value, ast.Name) and \
                                stmt.targets[0].value.id == 'metadata':
                            if isinstance(stmt.targets[0].slice, ast.Constant):
                                self.found_metadata_fields.add(stmt.targets[0].slice.value)

        self.generic_visit(node)

    def validate(self) -> tuple[bool, List[str]]:
        errors = []

        missing_vars = self.required_variables - self.found_variables
        if missing_vars:
            errors.append(f"Missing required variables: {missing_vars}")

        for var in self.required_variables:
            if var in self.found_variables and not self.is_hash_type.get(var):
                errors.append(f"Variable {var} must be of type Hash")

        for func, required_args in self.required_functions.items():
            if func not in self.found_functions:
                errors.append(f"Missing required function: {func}")
            elif self.found_functions[func] != required_args:
                errors.append(
                    f"Function {func} has incorrect arguments. "
                    f"Expected {required_args}, got {self.found_functions[func]}")

        if not self.has_constructor:
            errors.append("Missing constructor (@construct decorator)")

        missing_metadata = self.metadata_fields - self.found_metadata_fields
        if missing_metadata:
            errors.append(f"Missing required metadata fields: {missing_metadata}")

        return len(errors) == 0, errors


class ValidatorFactory:
    @staticmethod
    def get_validator(standard: XianStandard) -> ValidatorBase:
        if standard == XianStandard.XSC001:
            return ValidatorXSC001()
        raise ValueError(f"Unsupported standard: {standard}")


def validate_contract(contract_code: str, standard: XianStandard = XianStandard.XSC001) -> tuple[bool, List[str]]:
    """
    Validates if a contract follows the specified token standard
    Args:
        contract_code: String containing the contract code
        standard: TokenStandard enum specifying which standard to validate against
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    try:
        tree = ast.parse(contract_code)
        validator = ValidatorFactory.get_validator(standard)
        validator.visit(tree)
        return validator.validate()
    except SyntaxError as e:
        return False, [f"Syntax error in contract: {str(e)}"]
    except Exception as e:
        return False, [f"Error validating contract: {str(e)}"]
