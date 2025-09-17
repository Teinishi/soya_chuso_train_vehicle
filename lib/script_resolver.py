import re
import json
import importlib.util
from pathlib import Path
from types import ModuleType
from dataclasses import dataclass
from lib.template_parser import parse_template, render_template
from lib.safe_eval import safe_eval

_MAX_LEN = 8192
_use_pattern = re.compile(
    r'--\s*@\s*use\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))(?P<param>\s+.+)?\s*$')
_require_pattern = re.compile(
    r'--\s*@\s*require\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))(?P<param>\s+.+)?\s*$')
_require_line_pattern = re.compile(r'(?P<prefix>=\s*).*$')


@dataclass
class UseParams:
    build_params: dict | None
    use_param_text: str | None
    use_params: dict | None

    @staticmethod
    def _from_text(build_params: dict | None, use_param_text: str | None):
        use_params = None
        if use_param_text is not None:
            use_param_text = use_param_text.strip()
            try:
                use_params = json.loads(use_param_text)
            except json.decoder.JSONDecodeError:
                pass
        return UseParams(build_params, use_param_text, use_params)

    def _to_dict(self) -> dict:
        return {
            "build_params": self.build_params,
            "use_param_text": self.use_param_text,
            "use_params": self.use_params
        }


@dataclass
class RequireParams:
    build_params: dict | None
    use_param_text: str | None
    use_params: dict | None
    require_param_text: str | None
    require_params: dict | None

    @staticmethod
    def _from_text(use_params: UseParams, require_param_text: str | None):
        require_params = None
        if require_param_text is not None:
            require_param_text = require_param_text.strip()
            try:
                require_params = json.loads(require_param_text)
            except json.decoder.JSONDecodeError:
                pass
        return RequireParams(
            use_params.build_params,
            use_params.use_param_text,
            use_params.use_params,
            require_param_text,
            require_params
        )

    def _to_dict(self) -> dict:
        return {
            "build_params": self.build_params,
            "use_param_text": self.use_param_text,
            "use_params": self.use_params,
            "require_param_text": self.require_param_text,
            "require_params": self.require_params
        }


class ScriptResolver:
    _root_path: Path
    _file_cache: dict[Path, str]
    _module_cache: dict[str, ModuleType]

    def __init__(self, root_dir: str | None = None):
        self._root_path = Path(
            root_dir) if root_dir is not None else Path.cwd()
        self._file_cache = {}
        self._module_cache = {}

    def _join_path_safe(self, target_path: str | Path, check_file_exists: bool = False) -> Path:
        abs_path = self._root_path.joinpath(target_path).resolve()
        try:
            abs_path.relative_to(self._root_path)
        except ValueError:
            raise ValueError(f'Invalid path: "{target_path}"')
        if check_file_exists and not abs_path.is_file():
            raise FileNotFoundError(
                f'File does not exist: "{target_path}"')
        return abs_path

    def _open_file(self, path: str | Path) -> str:
        path = self._join_path_safe(path, check_file_exists=True)
        if path in self._file_cache:
            return self._file_cache[path]
        else:
            with path.open(encoding="utf-8") as f:
                text = f.read()
            self._file_cache[path] = text
            return text

    def _import_python(self, path: Path, check_callable_exists: str | None = None) -> ModuleType:
        path = self._join_path_safe(path, check_file_exists=True)

        module_name = ".".join(
            path.relative_to(self._root_path)
            .with_suffix("").parts
        )
        if module_name in self._module_cache:
            module = self._module_cache[module_name]
        else:
            spec = importlib.util.spec_from_file_location(
                module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._module_cache[module_name] = module

        if check_callable_exists is None:
            return module

        if not hasattr(module, check_callable_exists):
            raise AttributeError(
                f'Function "{check_callable_exists}" does not exist in module: "{path}"')
        if not callable(getattr(module, check_callable_exists)):
            raise TypeError(
                f'Attribute "{check_callable_exists}" is not callable in module: "{path}"')

        return module

    def _require(self, path: str, params: RequireParams) -> str:
        module = self._import_python(path, check_callable_exists="require")
        return module.require(params)

    def _resolve_require(self, script: str, params: UseParams) -> str:
        # @require を探す
        lines = script.split("\n")
        for i, line in enumerate(lines):
            m = _require_pattern.search(line)
            if m is None:
                continue
            path = m.group("path1") or \
                m.group("path2") or m.group("path3")
            params = RequireParams._from_text(params, m.group("param"))
            value = self._require(path, params)
            lines[i] = _require_line_pattern.sub(
                lambda m2: m2.group("prefix") + value,
                line, 1
            )

        return "\n".join(lines)

    def _render_template(self, script: str, params: UseParams, file: str) -> str:
        nodes = parse_template([l + "\n" for l in script.split("\n")], file)
        try:
            script = render_template(nodes, params._to_dict(), safe_eval)
        except Exception as e:
            raise Exception(f'Unexpected error in file "{file}":\n{e}')
        return script

    def _use_script(self, path: Path, build_params: dict | None = None, use_param_text: str | None = None) -> str:
        params = UseParams._from_text(build_params, use_param_text)

        ext = path.suffix
        if ext == ".lua":
            script = self._render_template(self._open_file(path), params, path)
            return self._resolve_require(script, params)
        elif ext == ".py":
            module = self._import_python(path, check_callable_exists="use")
            return module.use(params)
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
                prefix = f"-- {Path(use_path_param[0]).relative_to(self._root_path)}"
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
