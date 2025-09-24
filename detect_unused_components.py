import argparse
from pathlib import Path
import os
from xml.etree import ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("target", type=str)
parser.add_argument("-r", "--remove-file", action="store_true")
args = parser.parse_args()

target = Path(args.target)
tree = ET.parse(target)
root = tree.getroot()

used_components = set()

for c in root.findall("./bodies/body/components/c"):
    used_components.add(c.get("d"))

for file in target.with_suffix("").glob("*.bin"):
    if not file.is_file():
        continue
    name = file.with_suffix("").name
    if name not in used_components:
        if args.remove_file:
            print(f"{name}.bin is not used, removing file")
            os.remove(file)
        else:
            print(f"{name}.bin is not used")
