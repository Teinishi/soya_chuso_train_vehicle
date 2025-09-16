import re
from dataclasses import dataclass

_if_pattern = re.compile(r'--\s*@\s*if\s+(?P<condition>.*)')
_elif_pattern = re.compile(r'--\s*@\s*elif\s+(?P<condition>.*)')
_else_pattern = re.compile(r'--\s*@\s*else')
_end_pattern = re.compile(r'--\s*@\s*end')


@dataclass
class TemplateNode:
    pass


@dataclass
class TemplateText(TemplateNode):
    value: str


@dataclass
class TemplateIfBlock(TemplateNode):
    branches: list[tuple[str | None, list[TemplateNode]]]


def parse_template(lines: list[str], file: str) -> list[TemplateNode]:
    root: list[TemplateNode] = []
    stack: list[list[TemplateNode]] = [root]
    current_if = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        m = _if_pattern.fullmatch(stripped)
        if m is not None:
            expr = m.group("condition").strip()
            block = TemplateIfBlock(branches=[(expr, [])])
            stack[-1].append(block)
            stack.append(block.branches[-1][1])
            current_if = block
            continue

        m = _elif_pattern.fullmatch(stripped)
        if m is not None:
            expr = m.group("condition").strip()
            if not current_if:
                raise SyntaxError(
                    f'@elif has not corresponding @if: line {i + 1}, file: "{file}"')
            stack.pop()
            current_if.branches.append((expr, []))
            stack.append(current_if.branches[-1][1])
            continue

        m = _else_pattern.fullmatch(stripped)
        if m is not None:
            if not current_if:
                raise SyntaxError(
                    f'@end has not corresponding @if: line {i + 1}, file: "{file}"')
            stack.pop()
            current_if.branches.append((None, []))
            stack.append(current_if.branches[-1][1])
            continue

        m = _end_pattern.fullmatch(stripped)
        if m is not None:
            if not current_if:
                raise SyntaxError(
                    f'@end has not corresponding @if: line {i + 1}, file: "{file}"')
            stack.pop()
            current_if = None
            continue

        stack[-1].append(TemplateText(line))

    if len(stack) != 1:
        raise SyntaxError("Unmatched @if/@end")

    return root


def render_template(nodes: list[TemplateNode], context: dict, eval_expr) -> str:
    result = []
    for node in nodes:
        if isinstance(node, TemplateText):
            result.append(node.value)

        elif isinstance(node, TemplateIfBlock):
            for expr, body in node.branches:
                if expr is None or eval_expr(expr, context):
                    result.append(render_template(body, context, eval_expr))
                    break

        else:
            raise ValueError(f"Unknown node: {node}")
    return "".join(result)
