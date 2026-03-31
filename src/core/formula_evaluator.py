
import ast
import operator as op

# Supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.Gt: op.gt,
    ast.Lt: op.lt,
    ast.GtE: op.ge,
    ast.LtE: op.le,
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
    ast.Not: op.not_,
}

def safe_eval(expr, variables):
    """
    Safely evaluate a boolean or arithmetic expression with variables.
    """
    try:
        # Pre-process expression to handle 'AND', 'OR', 'NOT' which are not standard in Python eval body if not properly parsed
        # Case insensitive replacement for common logical operators
        import re
        expr = re.sub(r'\bAND\b', 'and', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bOR\b', 'or', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.IGNORECASE)

        tree = ast.parse(expr, mode='eval')
        return _eval(tree.body, variables)
    except Exception:
        # In production, we might want to log this
        return False

def _eval(node, variables):
    # Use ast.Constant for Python 3.8+; fallback to ast.Num/ast.Str for older versions
    if isinstance(node, ast.Constant):
        return node.value
    elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
        return node.n
    elif hasattr(ast, 'Str') and isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.BinOp):
        return operators[type(node.op)](_eval(node.left, variables), _eval(node.right, variables))
    elif isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](_eval(node.operand, variables))
    elif isinstance(node, ast.Compare):
        left = _eval(node.left, variables)
        for operation, right_node in zip(node.ops, node.comparators):
            right = _eval(right_node, variables)
            if not operators[type(operation)](left, right):
                return False
            left = right
        return True
    elif isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_eval(value, variables) for value in node.values)
        elif isinstance(node.op, ast.Or):
            return any(_eval(value, variables) for value in node.values)
    elif isinstance(node, ast.Name):
        # Case-insensitive variable lookup
        var_name = node.id.upper()
        if var_name in variables:
            return variables[var_name]
        raise NameError(f"Variable {node.id} not found")
    else:
        raise TypeError(f"Unsupported node type: {type(node)}")

if __name__ == "__main__":
    # Test cases
    vars = {'CLOSE': 51000, 'RSI': 25, 'VOLUME': 1000, 'SMA20': 50000}
    assert safe_eval('CLOSE > 50000 AND RSI < 30', vars)
    assert not safe_eval('CLOSE < 50000', vars)
    assert safe_eval('CLOSE > 50000 and (RSI < 20 OR volume > 500)', vars)
    assert safe_eval('NOT (CLOSE < 50000)', vars)
    assert not safe_eval('__import__("os").system("ls")', vars)
    print("All tests passed!")
