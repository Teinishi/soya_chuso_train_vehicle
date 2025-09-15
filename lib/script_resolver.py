import os
import re
import subprocess
import sys
import json
from lib.lua_literal import to_lua_literal

_MAX_LEN = 8192
_default_root_dir = os.path.join(os.path.dirname(__file__), "../lua")
_use_pattern = re.compile(
    r'--\s*@\s*use\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))\s*$')
_require_pattern = re.compile(
    r'--\s*@\s*require\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))(\s+(?P<key>[^\.\s]+(\s*\.\s*[^\.\s]+)*))?\s*$')
_require_line_pattern = re.compile(r'(?P<prefix>=\s*).*$')


class ScriptResolver:
    _root_dir: str
    _file_cache: dict[str, str]
    _require_cache: dict[str, any]

    def __init__(self, root_dir: str = _default_root_dir):
        self._root_dir = root_dir
        self._file_cache = {}
        self._require_cache = {}

    def _join_path_safe(self, target_path: str) -> str:
        base_path = os.path.abspath(self._root_dir)
        target_path = os.path.abspath(os.path.join(base_path, target_path))
        if os.path.commonpath([base_path]) == os.path.commonpath([base_path, target_path]):
            return target_path
        else:
            raise ValueError(f'Invalid path ("{target_path}")')

    def _require(self, path: str, key: str):
        abs_path = self._join_path_safe(path)
        if abs_path in self._require_cache:
            o = self._require_cache[abs_path]
        else:
            if not os.path.isfile(abs_path):
                raise ValueError(f'File not found ("{path}")')

            try:
                r = subprocess.run(
                    [sys.executable, abs_path],
                    capture_output=True, text=True, check=True,
                    cwd=os.getcwd()
                )
            except subprocess.CalledProcessError as e:
                sys.stdout.write(e.stdout or "")
                sys.stderr.write(e.stderr or "")
                sys.exit(e.returncode)

            o = json.loads(r.stdout)
            self._require_cache[abs_path] = o

        for k in key.split("."):
            k = k.strip()
            if isinstance(o, dict):
                o = o.get(k)
            elif isinstance(o, list) and k.isdecimal():
                o = o[int(k)]
            else:
                raise TypeError(
                    f'Cannot get property "{k}" of value {repr(k)}')

        return o

    def _resolve_require(self, script: str) -> str:
        # @require を探す
        lines = script.split("\n")
        for i, line in enumerate(lines):
            m1 = _require_pattern.search(line)
            if m1 is None:
                continue
            path = m1.group("path1") or \
                m1.group("path2") or m1.group("path3")
            key = m1.group("key")
            value = self._require(path, key)
            lines[i] = _require_line_pattern.sub(
                lambda m2: m2.group("prefix") + to_lua_literal(value),
                line, 1
            )

        return "\n".join(lines)

    def _open_file(self, path: str) -> str:
        path = self._join_path_safe(path)
        if path in self._file_cache:
            return self._file_cache[path]
        else:
            with open(path, encoding="utf-8") as f:
                script = self._resolve_require(f.read())
                self._file_cache[path] = script
                return script

    def resolve_script(self, text: str, root_dir: str = _default_root_dir, leave_params: bool = False):
        use_path = None
        for line in text.split("\n"):
            # @use を探す
            m = _use_pattern.search(line)
            if m is not None:
                use_path = m.group("path1") or \
                    m.group("path2") or m.group("path3")
                break

        if use_path is not None:
            script = self._open_file(use_path)

            # 文字数チェック
            if len(script) > _MAX_LEN:
                raise ValueError(
                    f'Exceeding length limit {_MAX_LEN} ("{use_path}")')

            # 文字数が足りるならコメントを残す
            prefix = ""
            if leave_params:
                prefix = f"-- {os.path.relpath(use_path, root_dir)}\n"
            if len(prefix) + len(script) > _MAX_LEN:
                return script
            else:
                return prefix + script

        else:
            return None
