from collections import defaultdict
import itertools
import shutil
import typing
import copy
import os
import glob
from xml.etree import ElementTree as ET
from lib.vehicle_component import VehicleComponent
from lib.matrix import Vector3i
from lib.escape_multiline_attributes import EscapeMultilineAttributes

Tuple3i = tuple[int, int, int]
Box = tuple[Vector3i | Tuple3i, Vector3i | Tuple3i]


def _normalize_box(box: Box) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    a = box[0]
    if isinstance(a, tuple):
        a = Vector3i(a)
    b = box[1]
    if isinstance(b, tuple):
        b = Vector3i(b)
    xmin, xmax = min(a.x, b.x), max(a.x, b.x)
    ymin, ymax = min(a.y, b.y), max(a.y, b.y)
    zmin, zmax = min(a.z, b.z), max(a.z, b.z)
    return (xmin, xmax), (ymin, ymax), (zmin, zmax)


def _get_box_positions(box: Box):
    (xmin, xmax), (ymin, ymax), (zmin, zmax) = _normalize_box(box)
    return map(Vector3i, itertools.product(range(xmin, xmax + 1), range(ymin, ymax + 1), range(zmin, zmax + 1)))


class LogicNodeLink:
    _element: ET.Element
    _logic_type: int
    _position_0: Vector3i
    _position_1: Vector3i

    def __init__(self, element: ET.Element):
        vp0 = element.find("voxel_pos_0")
        vp1 = element.find("voxel_pos_1")
        self._element = element
        self._logic_type = int(element.get("type", 0))
        self._position_0 = Vector3i(0, 0, 0) if vp0 is None else Vector3i(
            int(vp0.get("x", 0)), int(vp0.get("y", 0)), int(vp0.get("z", 0)))
        self._position_1 = Vector3i(0, 0, 0) if vp1 is None else Vector3i(
            int(vp1.get("x", 0)), int(vp1.get("y", 0)), int(vp1.get("z", 0)))

    def get_logic_type(self) -> int:
        return self._logic_type

    def get_position_0(self) -> Vector3i:
        return self._position_0

    def get_position_1(self) -> Vector3i:
        return self._position_1


class Vehicle:
    _component_mods: list[str]
    _escape_multiline_attrs: EscapeMultilineAttributes
    _root: ET.Element
    _bodies: list[ET.Element]
    _components: set[VehicleComponent]
    _position_component_map: dict[Vector3i, VehicleComponent]
    _body_component_map: defaultdict[ET.Element, set[VehicleComponent]]
    _custom_name_map: defaultdict[str, set[VehicleComponent]]
    _microprocessor_name_map: defaultdict[str, set[VehicleComponent]]
    _logic_links: set[LogicNodeLink]
    _position_logic_map: defaultdict[Vector3i, set[LogicNodeLink]]

    @staticmethod
    def from_file(path: str) -> typing.Self:
        with open(path, encoding="utf-8") as f:
            xml_text = f.read()
        v = Vehicle(xml_text)
        v._component_mods.append(os.path.splitext(path)[0])
        return v

    def __init__(self, xml_text: str):
        self._component_mods = []
        self._escape_multiline_attrs = EscapeMultilineAttributes()
        self._root = ET.fromstring(
            self._escape_multiline_attrs.escape(xml_text))
        self._bodies = []
        self._components = set()
        self._position_component_map = {}
        self._body_component_map = defaultdict(set)
        self._custom_name_map = defaultdict(set)
        self._microprocessor_name_map = defaultdict(set)
        self._logic_links = set()
        self._position_logic_map = defaultdict(set)

        self._add_vehicle(self._root)

    def _add_vehicle(self, vehicle: ET.Element):
        bodies = self._root.find("./bodies")
        for body in vehicle.findall("./bodies/body"):
            if body not in bodies:
                bodies.append(body)
            self._bodies.append(body)
            for c in body.findall("./components/c"):
                self._add_component(VehicleComponent(c, body))

        logic_node_links = self._root.find("./logic_node_links")
        for element in vehicle.findall("./logic_node_links/logic_node_link"):
            if element not in logic_node_links:
                logic_node_links.append(element)
            self._add_logic_link(LogicNodeLink(element))

    def _add_component(self, component: VehicleComponent):
        # TODO: 既にあるパーツとボクセルが重複する場合の処理

        element = component.get_element()
        body = component.get_body()
        components = body.find("./components")
        if element not in components:
            components.append(element)

        self._components.add(component)

        position = component.get_position()
        if position in self._position_component_map:
            raise ValueError(f"Multiple components at position {position}.")
        self._position_component_map[position] = component

        self._body_component_map[body].add(component)

        custom_name = component.get_custom_name()
        if custom_name is not None:
            self._custom_name_map[custom_name].add(component)

        microprocessor_name = component.get_microprocessor_name()
        if microprocessor_name is not None:
            self._microprocessor_name_map[microprocessor_name]\
                .add(component)

    def _remove_component(self, component: VehicleComponent):
        for p in component.voxels():
            for link in list(self._position_logic_map[p]):
                self._remove_logic_link(link)

        body = component.get_body()
        body.find("./components").remove(component.get_element())
        self._components.remove(component)
        del self._position_component_map[component.get_position()]
        self._body_component_map[body].remove(component)

        custom_name = component.get_custom_name()
        if custom_name is not None:
            self._custom_name_map[custom_name].remove(component)

        microprocessor_name = component.get_microprocessor_name()
        if microprocessor_name is not None:
            self._microprocessor_name_map[microprocessor_name]\
                .remove(component)

    def _add_logic_link(self, link: LogicNodeLink):
        self._logic_links.add(link)
        self._position_logic_map[link.get_position_0()].add(link)
        self._position_logic_map[link.get_position_1()].add(link)

    def _remove_logic_link(self, link: LogicNodeLink):
        self._logic_links.remove(link)
        self._position_logic_map[link.get_position_0()].remove(link)
        self._position_logic_map[link.get_position_1()].remove(link)

    def copy(self) -> typing.Self:
        return copy.deepcopy(self)

    def include_vehicle(self, other: typing.Self):
        self._component_mods += other._component_mods
        self._add_vehicle(other._root)

    def save(self, path):
        # .bin ファイルをリストアップ
        mod_components: dict[str, str] = {}
        for mods_source in self._component_mods:
            if not os.path.isdir(mods_source):
                continue
            for file in glob.glob("*.bin", root_dir=mods_source):
                mod_components[os.path.splitext(file)[0]] = mods_source

        # 使用中の .bin を調べる
        active_mod_components: set[tuple[str, str]] = set()
        for component in self._components:
            d = component.get_definition_name()
            if d in mod_components:
                active_mod_components.add((mod_components[d], d))

        # .bin をコピー
        if len(active_mod_components) > 0:
            mods_dest = os.path.splitext(path)[0]
            os.makedirs(mods_dest, exist_ok=True)
            for (mods_source, name) in active_mod_components:
                shutil.copy(
                    os.path.join(mods_source, f"{name}.bin"),
                    os.path.join(mods_dest, f"{name}.bin")
                )


        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(self._escape_multiline_attrs.restore(
                ET.tostring(self._root, encoding="unicode")
            ))

    def get_components(
        self,
        position: Vector3i | Tuple3i | None = None,
        box: Box | None = None,
        custom_name: str | None = None,
        microprocessor_name: str | None = None
    ) -> list[VehicleComponent]:
        if isinstance(position, tuple):
            position = Vector3i(*position)

        result: list[VehicleComponent] | None = None
        if position is not None:
            if position not in self._position_component_map:
                return []
            result = [self._position_component_map[position]]

        if box is not None:
            result = []
            for p in _get_box_positions(box):
                if p in self._position_component_map:
                    result.append(self._position_component_map[p])

        if custom_name is not None:
            result = copy.copy(self._custom_name_map[custom_name])\
                if result is None else \
                [r for r in result if r in self._custom_name_map[custom_name]]

        if microprocessor_name is not None:
            result = copy.copy(self._microprocessor_name_map[microprocessor_name])\
                if result is None else \
                [r for r in result if r in self._microprocessor_name_map[microprocessor_name]]

        return result if result is not None else list(self._components)

    def get_component(self, **args) -> VehicleComponent:
        components = self.get_components(**args)
        if len(components) != 1:
            raise ValueError(
                f"get_component should find 1 components, but {len(components)} found")
        else:
            return next(iter(components))

    def remove_components(self, **args):
        components = self.get_components(**args)
        for component in components:
            self._remove_component(component)

    def remove_component(self, **args):
        self._remove_component(self.get_component(**args))

    def set_attribute(self, attr_name: str, value: str | int | float | bool, **args):
        if attr_name == "custom_name":
            self.set_custom_name(value, **args)

        self.get_component(**args)._set_attribute(attr_name, value)

    def set_custom_name(self, new_custom_name: str, **args):
        component = self.get_component(**args)
        if component._custom_name is not None:
            self._custom_name_map[component._custom_name].remove(component)
        component._set_custom_name(new_custom_name)
        self._custom_name_map[new_custom_name].add(component)

    def set_microprocessor_property(self, property_name: str, value: str | int, **args):
        self.get_component(**args)\
            ._set_microprocessor_property(property_name, value)

    def merge_bodies(self, component1: VehicleComponent, component2: VehicleComponent):
        i1 = self._bodies.index(component1.get_body())
        i2 = self._bodies.index(component2.get_body())
        i1, i2 = min(i1, i2), max(i1, i2)
        body1 = self._bodies[i1]
        body2 = self._bodies[i2]

        count1 = 0
        for component in list(self._body_component_map[body2]):
            count1 += 1
            self._remove_component(component)
            self._add_component(
                VehicleComponent(component.get_element(), body1))
        del self._body_component_map[body2]

        bodies = self._root.find("./bodies")
        bodies.remove(body2)
