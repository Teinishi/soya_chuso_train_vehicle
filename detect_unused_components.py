import argparse
from pathlib import Path
import os
from xml.etree import ElementTree as ET


def detect_unused_components(target: Path, remove_file: bool = False, verbose: bool = False) -> set[str]:
    tree = ET.parse(target)
    root = tree.getroot()

    used_components: set[str] = set()
    unused_components: set[str] = set()

    for c in root.findall("./bodies/body/components/c"):
        used_components.add(c.get("d"))

    for file in target.with_suffix("").glob("*.bin"):
        if not file.is_file():
            continue
        name = file.with_suffix("").name
        if name not in used_components:
            if remove_file:
                if verbose:
                    print(f"{name}.bin is not used, removing file")
                os.remove(file)
            else:
                if verbose:
                    print(f"{name}.bin is not used")
                unused_components.add(name)

    return unused_components


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=str)
    parser.add_argument("-r", "--remove-file", action="store_true")
    args = parser.parse_args()

    detect_unused_components(Path(args.target), remove_file=True, verbose=True)
