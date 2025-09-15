def _dict_to_list(data: dict[int, any]):
    r = []
    for i in range(1, max(data.keys()) + 1):
        r.append(data.get(i, None))
    return r


def _is_number(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True


def _is_natural_number(s: str) -> bool:
    if not _is_number(s):
        return False
    f = float(s)
    return f.is_integer() and f >= 1


def _lua_table_key(key: int | float | str) -> str:
    if _is_number(key):
        return f"[{key}]"
    else:
        return key


def _list_to_lua(data: list) -> str:
    r = data.copy()
    while len(r) > 0 and r[-1] is None:
        r.pop()
    return "{" + ",".join(map(to_lua_literal, r)) + "}"


def _dict_to_lua(data: dict) -> str:
    def _dict_to_lua(data: dict) -> str:
        lua: str = "{"
        if len(data) > 0:
            for k, v in data.items():
                if v is not None:
                    lua += f"{_lua_table_key(k)}={to_lua_literal(v)},"
            lua = lua[:-1]
        lua += "}"
        return lua

    lua1: str = _dict_to_lua(data)

    natural_number_keys = {}
    other_keys = {}

    for k, v in data.items():
        if _is_natural_number(k):
            natural_number_keys[int(k)] = v
        else:
            other_keys[k] = v

    if len(natural_number_keys) > 0:
        lua2: str = _list_to_lua(_dict_to_list(natural_number_keys))
        if len(other_keys) > 0:
            lua2 = lua2[:-1] + "," + _dict_to_lua(other_keys)[1:]
        return lua1 if len(lua1) < len(lua2) else lua2

    return lua1


def to_lua_literal(data: dict | list | int | float | str | None) -> str:
    if data is None:
        return "nil"
    elif isinstance(data, int) or isinstance(data, float):
        return str(data)
    elif isinstance(data, str):
        return f"'{data}'"
    elif isinstance(data, list):
        return _list_to_lua(data)
    elif isinstance(data, dict):
        return _dict_to_lua(data)
