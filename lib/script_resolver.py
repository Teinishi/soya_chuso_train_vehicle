import os
import re
import subprocess
import sys
import json
from lib.lua_literal import to_lua_literal
from lib.template_parser import parse_template, render_template
from lib.safe_eval import safe_eval

_MAX_LEN = 8192
_default_root_dir = os.path.join(os.path.dirname(__file__), "../lua")
_use_pattern = re.compile(
    r'--\s*@\s*use\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))(?P<param>\s+.+)?\s*$')
_require_pattern = re.compile(
    r'--\s*@\s*require\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))(?P<param>\s+.+)?\s*$')
_require_line_pattern = re.compile(r'(?P<prefix>=\s*).*$')


def _run_python(path: str, input: str | None = None) -> str:
    if not os.path.isfile(path):
        raise ValueError(f'File not found "{path}"')

    try:
        r = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, check=True,
            input=input, cwd=os.getcwd()
        )
        return r.stdout
    except subprocess.CalledProcessError as e:
        sys.stdout.write(e.stdout or "")
        sys.stderr.write(e.stderr or "")
        sys.exit(e.returncode)


class ScriptResolver:
    _root_dir: str
    _file_cache: dict[str, str]
    _require_cache: dict[tuple[str, str], any]

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

    def _open_file(self, path: str) -> str:
        path = self._join_path_safe(path)
        if path in self._file_cache:
            return self._file_cache[path]
        else:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self._file_cache[path] = text
            return text

    def _require(self, path: str, params: dict):
        path = self._join_path_safe(path)
        params_json = json.dumps(params)
        if (path, params_json) in self._require_cache:
            o = self._require_cache[(path, params_json)]
        else:
            o = json.loads(_run_python(path, input=params_json))
            self._require_cache[(path, params_json)] = o

        return o

    def _resolve_require(self, script: str, params: dict) -> str:
        # @require を探す
        lines = script.split("\n")
        for i, line in enumerate(lines):
            m1 = _require_pattern.search(line)
            if m1 is None:
                continue
            path = m1.group("path1") or \
                m1.group("path2") or m1.group("path3")

            param = m1.group("param")
            if param is not None:
                param = param.strip()
                params = {**params, "require_param_text": param.strip()}
                try:
                    params["require_params"] = json.loads(param)
                except json.decoder.JSONDecodeError:
                    pass

            value = self._require(path, params)
            lines[i] = _require_line_pattern.sub(
                lambda m2: m2.group("prefix") + to_lua_literal(value),
                line, 1
            )

        return "\n".join(lines)

    def _render_template(self, script: str, params: dict, file: str) -> str:
        nodes = parse_template([l + "\n" for l in script.split("\n")], file)
        try:
            script = render_template(nodes, params, safe_eval)
        except Exception as e:
            raise Exception(f'Unexpected error in file "{file}":\n{e}')
        return script

    def _use_script(self, path: str, build_params: dict | None = None, use_param: str | None = None) -> str:
        params = {}
        if build_params is not None:
            params["build_params"] = build_params
        if use_param is not None:
            params["use_param_text"] = use_param
            try:
                params["use_params"] = json.loads(use_param)
            except json.decoder.JSONDecodeError:
                pass

        ext = os.path.splitext(path)[1]
        if ext == ".lua":
            return self._resolve_require(self._render_template(self._open_file(path), params, path), params)
        elif ext == ".py":
            return _run_python(path, input=json.dumps(params))
        else:
            raise ValueError(f'Unknown file type "{ext}" of file "{path}"')

    def resolve_script(self, text: str, build_params: dict | None = None, leave_params: bool = False):
        use_path_param: tuple[str, str | None] | None = None
        for line in text.split("\n"):
            # @use を探す
            m = _use_pattern.search(line)
            if m is not None:
                path = m.group("path1") or \
                    m.group("path2") or m.group("path3")
                param = m.group("param")
                if param is not None:
                    param = param.strip()
                use_path_param = (self._join_path_safe(path), param)
                break

        if use_path_param is not None:
            script = self._use_script(
                use_path_param[0], build_params, use_path_param[1])

            # 文字数チェック
            if len(script) > _MAX_LEN:
                raise ValueError(
                    f'Exceeding length limit {_MAX_LEN}, file "{use_path_param[0]}"')

            # 文字数が足りるならコメントを残す
            prefix = ""
            if leave_params:
                prefix = f"-- {os.path.relpath(use_path_param[0], self._root_dir)}"
                if use_path_param[1] is not None:
                    prefix += " "
                    prefix += use_path_param[1]
                prefix += "\n"
            if len(prefix) + len(script) > _MAX_LEN:
                return script
            else:
                return prefix + script

        else:
            return None
