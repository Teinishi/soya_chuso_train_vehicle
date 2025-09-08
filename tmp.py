from xml.etree import ElementTree as ET

tree = ET.parse("./chuso3000/CHUSO3000_base.xml")
root = tree.getroot()

d_set = set()
for c in root.findall(".//c[@d]"):
    d_set.add(c.get("d"))

for d in sorted(d_set, key=len):
    print(d)
