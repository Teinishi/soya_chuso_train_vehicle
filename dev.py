from pathlib import Path
import shutil
import subprocess
from lib.load_env import load_env

TARGET_FOLDERS = ["chuso3000"]

env = load_env()
vehicles_path = Path(env["VEHICLES_PATH"])
root_path = Path.cwd()
dist_path = root_path.joinpath("dist")

for folder in TARGET_FOLDERS:
    for t_file in root_path.joinpath(folder).glob("*.xml"):
        if not t_file.is_file():
            continue
        name = t_file.name
        v_file = vehicles_path.joinpath(name)
        if v_file.is_file() and v_file.stat().st_mtime > t_file.stat().st_mtime:
            print(
                f'Copying "{name}" from "{vehicles_path.name}" to "{folder}"')
            shutil.copy(v_file, t_file)

shutil.rmtree(dist_path)

subprocess.run(root_path.joinpath("build.bat"), check=True)

for file in dist_path.glob("*.xml"):
    print(f'Generated vehicle "{file.name}"')
shutil.copytree(dist_path, vehicles_path, dirs_exist_ok=True)
