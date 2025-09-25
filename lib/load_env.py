from pathlib import Path

env_file = Path.cwd().joinpath(".env")


def load_env():
    env = {}
    with env_file.open("r", encoding="utf-8") as f:
        for line in f.readlines():
            key, value = line.split("=", maxsplit=1)
            value = value.strip()
            if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            env[key.strip()] = value

    return env
