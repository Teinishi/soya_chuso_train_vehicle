import argparse
import os
import re
from xml.etree import ElementTree as ET
from lib.escape_multiline_attributes import EscapeMultilineAttributes

invalid_path_chars = re.compile('[<>:"/\\|?*]')
use_pattern = re.compile(
    r'--\s*@\s*use\s+("(?P<path2>\S+)"|\'(?P<path3>\S+)\'|(?P<path1>\S+))(?P<param>\s+.+)?\s*$')


def main(input_path: str, output_path: str, skip_use: bool):
    with open(input_path, encoding="utf-8") as f:
        xml_text = f.read()

    escape_multiline_attrs = EscapeMultilineAttributes()
    root = ET.fromstring(escape_multiline_attrs.escape(xml_text))

    microprocessors: dict[str, list[list[str]]] = {}

    for mpdef in root.findall(".//microprocessor_definition"):
        scripts = []
        for o in mpdef.findall('group/components/c[@type="56"]/object'):
            scripts.append(
                escape_multiline_attrs.restore_value(o.get("script")))

        if skip_use:
            scripts = [
                script for script in scripts if use_pattern.search(script) is None]

        if len(scripts) == 0:
            continue

        name = mpdef.get("name")
        if name not in microprocessors:
            microprocessors[name] = [scripts]
        else:
            for s in microprocessors[name]:
                if set(s) == set(scripts):
                    break
            else:
                microprocessors[name].append(scripts)

    for name, m in microprocessors.items():
        is_single = len(m) == 1
        for i, scripts in enumerate(m):
            dirname = name if is_single else f"{name} ({i + 1})"
            dirname = invalid_path_chars.sub("", dirname)
            dirpath = os.path.join(output_path, dirname)
            os.makedirs(dirpath, exist_ok=True)
            for j, script in enumerate(scripts):
                with open(os.path.join(dirpath, f"{j}.lua"), "w", encoding="utf-8") as f:
                    f.write(script)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("vehicle", type=str)
    parser.add_argument("output", type=str)
    parser.add_argument("--skip-use", action="store_true")
    args = parser.parse_args()

    main(args.vehicle, args.output, args.skip_use)
