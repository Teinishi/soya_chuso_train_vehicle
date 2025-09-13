import os
import re

_MAX_LEN = 8192
_default_root_dir = os.path.join(os.path.dirname(__file__), "../lua")
_use_pattern = re.compile(r'\s*--\s*@\s*use\s+(?P<path1>\S+|"(?P<path2>\S+)"|\'(?P<path3>\S+)\')\s*')

def _join_path_safe(base_path: str, target_path: str) -> bool:
    base_path = os.path.abspath(base_path)
    target_path = os.path.abspath(os.path.join(base_path, target_path))
    if os.path.commonpath([base_path]) == os.path.commonpath([base_path, target_path]):
        return target_path
    else:
        return None

def resolve_script(text: str, root_dir: str = _default_root_dir, leave_params: bool = False):
    use_path = None
    for line in text.split("\n"):
        m = _use_pattern.fullmatch(line)
        if m is not None:
            m_path = m.group("path1") or m.group("path2") or m.group("path3")
            path = _join_path_safe(root_dir, m_path)
            if path is None:
                raise ValueError(f'Invalid path "{m_path}"')
            use_path = path

    if use_path is None:
        return None
    else:
        prefix = ""
        if leave_params:
            prefix = f"-- {os.path.relpath(use_path, root_dir)}\n"
        with open(use_path, encoding="utf-8") as f:
            file = f.read()
            if len(file) > _MAX_LEN:
                raise ValueError(f'Exceeding length limit {_MAX_LEN} "{use_path}"')
            if len(prefix) + len(file) > _MAX_LEN:
                return file
            else:
                return prefix + file
