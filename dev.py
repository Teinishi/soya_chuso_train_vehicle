from pathlib import Path
import shutil
import subprocess
from detect_unused_components import detect_unused_components
from lib.load_env import load_env

TARGET_FOLDERS = ["chuso3000"]

env = load_env()
vehicles_path = Path(env["VEHICLES_PATH"])
root_path = Path.cwd()
dist_path = root_path.joinpath("dist")


def copy_if_newer(source: Path, target: Path):
    if not source.is_file():
        return
    if not target.is_file() or target.stat().st_mtime < source.stat().st_mtime:
        shutil.copy(source, target)


for folder in TARGET_FOLDERS:
    for t_file in root_path.joinpath(folder).glob("*.xml"):
        if not t_file.is_file():
            continue
        name = t_file.name
        v_file = vehicles_path.joinpath(name)
        if not v_file.is_file():
            continue

        copy_if_newer(v_file, t_file)

        t_folder = t_file.with_suffix("")
        v_folder = v_file.with_suffix("")
        if v_folder.is_dir():
            for v_component in v_folder.glob("*.bin"):
                if not v_component.is_file():
                    continue
                t_component = t_folder.joinpath(v_component.name)
                copy_if_newer(v_component, t_component)

        detect_unused_components(t_file, remove_file=True, verbose=True)

        if v_file.is_file() and v_file.stat().st_mtime > t_file.stat().st_mtime:
            print(
                f'Copying "{name}" from "{vehicles_path.name}" to "{folder}"')
            shutil.copy(v_file, t_file)

            print(v_folder, v_folder.is_dir())
            if v_folder.is_dir():
                print("copy dir")
                shutil.copytree(
                    v_folder,
                    t_file.with_suffix(""),
                    dirs_exist_ok=True
                )

shutil.rmtree(dist_path)

subprocess.run(root_path.joinpath("build.bat"), check=True)

for file in dist_path.glob("*.xml"):
    print(f'Generated vehicle "{file.name}"')
shutil.copytree(dist_path, vehicles_path, dirs_exist_ok=True)
