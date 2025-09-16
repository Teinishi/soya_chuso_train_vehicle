import ast
import operator

# サポートする演算子
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

_BOOL_OPS = {
    ast.And: all,
    ast.Or: any,
}

_UNARY_OPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Not: operator.not_,
}


def safe_eval(expr: str, context: dict = None):
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        # 名前（変数）
        elif isinstance(node, ast.Name):
            if context is None or node.id not in context:
                raise NameError(f"Unknown variable: {node.id}")
            return context[node.id]

        # 定数
        elif isinstance(node, ast.Constant):  # Python 3.8+
            return node.value

        # 二項演算 (a + b など)
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _BIN_OPS:
                raise ValueError(f"Unsupported operator: {ast.dump(node.op)}")
            return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))

        # 比較演算 (a < b, a == b など)
        elif isinstance(node, ast.Compare):
            left = _eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in _CMP_OPS:
                    raise ValueError(f"Unsupported comparator: {ast.dump(op)}")
                right = _eval(comparator)
                if not _CMP_OPS[type(op)](left, right):
                    return False
                left = right
            return True

        # bool演算 (and / or)
        elif isinstance(node, ast.BoolOp):
            if type(node.op) not in _BOOL_OPS:
                raise ValueError(f"Unsupported bool op: {ast.dump(node.op)}")
            values = [_eval(v) for v in node.values]
            return _BOOL_OPS[type(node.op)](values)

        # 単項演算 (-a, not a)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in _UNARY_OPS:
                raise ValueError(f"Unsupported unary op: {ast.dump(node.op)}")
            return _UNARY_OPS[type(node.op)](_eval(node.operand))

        else:
            raise ValueError(f"Unsupported syntax: {ast.dump(node)}")

    return _eval(tree)
