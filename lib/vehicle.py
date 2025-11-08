from __future__ import annotations
from collections import defaultdict
import itertools
import shutil
import copy
import os
import glob
from typing import Any, Literal, TypeAlias, TypedDict, Unpack
from xml.etree import ElementTree as ET
from lib.logic_type import LOGIC_TYPE_NUMBER, LogicTypeName
from lib.vehicle_component import VehicleComponent
from lib.matrix import Matrix3i, AxisName, Vector3i
from lib.escape_multiline_attributes import EscapeMultilineAttributes
from lib.script_resolver import ScriptResolver

StrPath: TypeAlias = str | os.PathLike[str]
Tuple3i: TypeAlias = tuple[int, int, int]
Box: TypeAlias = tuple[Vector3i | Tuple3i, Vector3i | Tuple3i]


class _ComponentSelector(TypedDict, total=False):
    position: Vector3i | Tuple3i | None
    box: Box | None
    custom_name: str | None
    microprocessor_name: str | None


def _remove_non_ascii(text: str) -> str:
    return ''.join(c for c in text if c.isascii())


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
    logic_type: int
    position_0: Vector3i
    position_1: Vector3i

    def __init__(self, element: ET.Element):
        vp0 = element.find('voxel_pos_0')
        vp1 = element.find('voxel_pos_1')
        self._element = element
        self.logic_type = int(element.get('type', 0))

        if vp0 is None:
            self.position_0 = Vector3i.zero()
        else:
            self.position_0 = Vector3i(
                int(vp0.get('x', '0')),
                int(vp0.get('y', '0')),
                int(vp0.get('z', '0'))
            )
        if vp1 is None:
            self.position_1 = Vector3i.zero()
        else:
            self.position_1 = Vector3i(
                int(vp1.get('x', '0')),
                int(vp1.get('y', '0')),
                int(vp1.get('z', '0'))
            )

    def set_position(self, i: Literal[0, 1], new_position: Vector3i):
        if i == 0:
            self.position_0 = new_position
        else:
            self.position_1 = new_position

        tag_name = f'voxel_pos_{i}'
        vp = self._element.find(tag_name)
        if new_position != Vector3i.zero():
            if vp is None:
                vp = ET.Element(tag_name, new_position.xml_attrib())
                self._element.append(vp)
            else:
                vp.attrib = new_position.xml_attrib()
        elif vp is not None:
            self._element.remove(vp)


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
    def from_file(path: str) -> Vehicle:
        with open(path, encoding='utf-8') as f:
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

    def _refresh_map_cache(self):
        self._position_component_map = {}
        self._body_component_map = defaultdict(set)
        self._custom_name_map = defaultdict(set)
        self._microprocessor_name_map = defaultdict(set)
        self._position_logic_map = defaultdict(set)

        for component in self._components:
            for p in component.voxels():
                if p in self._position_component_map:
                    raise ValueError(f'Multiple components at position {p}.')
                self._position_component_map[p] = component

            self._body_component_map[component.get_body()].add(component)

            custom_name = component.get_custom_name()
            if custom_name is not None:
                self._custom_name_map[custom_name].add(component)

            microprocessor_name = component.get_microprocessor_name()
            if microprocessor_name is not None:
                self._microprocessor_name_map[microprocessor_name]\
                    .add(component)

        for link in self._logic_links:
            self._position_logic_map[link.position_0].add(link)
            self._position_logic_map[link.position_1].add(link)

    def _add_vehicle(self, vehicle: ET.Element):
        bodies = self._root.find('./bodies')
        assert bodies is not None
        for body in vehicle.findall('./bodies/body'):
            if body not in bodies:
                bodies.append(body)
            self._bodies.append(body)
            for c in body.findall('./components/c'):
                self._add_component(VehicleComponent(c, body))

        logic_node_links = self._root.find('./logic_node_links')
        if logic_node_links is None:
            logic_node_links = ET.Element('logic_node_links')
            self._root.append(logic_node_links)

        for element in vehicle.findall('./logic_node_links/logic_node_link'):
            if element not in logic_node_links:
                logic_node_links.append(element)
            self._add_logic_link(LogicNodeLink(element))

    def _add_component(self, component: VehicleComponent):
        # TODO: 既にあるパーツとボクセルが重複する場合の処理

        element = component.get_element()
        body = component.get_body()
        components = body.find('./components')
        assert components is not None
        if element not in components:
            components.append(element)

        self._components.add(component)

        for p in component.voxels():
            if p in self._position_component_map:
                raise ValueError(
                    f'Multiple components at position {p}.')
            self._position_component_map[p] = component

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
        components = body.find('./components')
        assert components is not None
        components.remove(component.get_element())
        self._components.remove(component)
        for p in component.voxels():
            assert self._position_component_map.pop(p) == component
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
        self._position_logic_map[link.position_0].add(link)
        self._position_logic_map[link.position_1].add(link)

    def _remove_logic_link(self, link: LogicNodeLink):
        self._logic_links.remove(link)
        self._position_logic_map[link.position_0].remove(link)
        self._position_logic_map[link.position_1].remove(link)

    def _change_logic_link_pos(self, link: LogicNodeLink, *, new_position_0: Vector3i | None = None, new_position_1: Vector3i | None = None):
        if new_position_0 is not None:
            self._position_logic_map[link.position_0].remove(link)
            self._position_logic_map[new_position_0].add(link)
            link.position_0 = new_position_0

        if new_position_1 is not None:
            self._position_logic_map[link.position_1].remove(link)
            self._position_logic_map[new_position_1].add(link)
            link.position_1 = new_position_1

    def add_logic_link(
        self,
        logic_type: LogicTypeName,
        position_0: Vector3i | Tuple3i,
        position_1: Vector3i | Tuple3i
    ):
        element = ET.Element(
            'logic_node_link',
            {'type': str(LOGIC_TYPE_NUMBER[logic_type])}
        )
        element.append(ET.Element(
            'voxel_pos_0',
            Vector3i(position_0).xml_attrib()
        ))
        element.append(ET.Element(
            'voxel_pos_1',
            Vector3i(position_1).xml_attrib()
        ))

        logic_node_links = self._root.find('./logic_node_links')
        if logic_node_links is None:
            logic_node_links = ET.Element('logic_node_links')
            self._root.append(logic_node_links)
        logic_node_links.append(element)

        self._add_logic_link(LogicNodeLink(element))

    def translate(self, delta: Vector3i | Tuple3i):
        delta = Vector3i(delta)
        for component in self._components:
            component.set_position(component.get_position() + delta)

        self._refresh_map_cache()

    def rotate(self, axis: AxisName, count: int, center: Vector3i | Tuple3i | None = None):
        if center is None:
            center = Vector3i.zero()
        else:
            center = Vector3i(center)

        r = Matrix3i.rotation(axis, -count)
        for component in self._components:
            component.apply_transform(r)
            component.set_position(r.multiply_on_vector(
                component.get_position() - center) + center)

        for link in self._logic_links:
            link.set_position(
                0, r.multiply_on_vector(link.position_0 - center) + center)
            link.set_position(
                1, r.multiply_on_vector(link.position_1 - center) + center)

        self._refresh_map_cache()

    def copy(self) -> Vehicle:
        return copy.deepcopy(self)

    def include_vehicle(self, other: Vehicle):
        self._component_mods += other._component_mods
        self._add_vehicle(other._root)

    def save(self, path: StrPath):
        # .bin ファイルをリストアップ
        mod_components: dict[str, str] = {}
        for mods_source in self._component_mods:
            if not os.path.isdir(mods_source):
                continue
            for file in glob.glob('*.bin', root_dir=mods_source):
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
                    os.path.join(mods_source, f'{name}.bin'),
                    os.path.join(mods_dest, f'{name}.bin')
                )

        with open(path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(self._escape_multiline_attrs.restore(
                ET.tostring(self._root, encoding='unicode')
            ))

    def get_components(
        self,
        **kwargs: Unpack[_ComponentSelector]
    ) -> list[VehicleComponent]:
        result: list[VehicleComponent] | None = None

        position = kwargs.get('position')
        box = kwargs.get('box')
        custom_name = kwargs.get('custom_name')
        microprocessor_name = kwargs.get('microprocessor_name')

        if position is not None:
            position = Vector3i(position)
            if position not in self._position_component_map:
                return []
            result = [self._position_component_map[position]]

        if box is not None:
            result = []
            for p in _get_box_positions(box):
                if p in self._position_component_map:
                    result.append(self._position_component_map[p])

        if custom_name is not None:
            result = list(self._custom_name_map[custom_name])\
                if result is None else \
                [r for r in result if r in self._custom_name_map[custom_name]]

        if microprocessor_name is not None:
            result = list(self._microprocessor_name_map[microprocessor_name])\
                if result is None else \
                [r for r in result if r in self._microprocessor_name_map[microprocessor_name]]

        return result if result is not None else list(self._components)

    def get_component(
        self,
        **kwargs: Unpack[_ComponentSelector]
    ) -> VehicleComponent:
        components = self.get_components(**kwargs)
        if len(components) != 1:
            raise ValueError(
                f'get_component should find 1 components, but {len(components)} found')
        else:
            return next(iter(components))

    def remove_components(
        self,
        **kwargs: Unpack[_ComponentSelector]
    ):
        components = self.get_components(**kwargs)
        for component in components:
            self._remove_component(component)

    def remove_component(
        self,
        **kwargs: Unpack[_ComponentSelector]
    ):
        self._remove_component(self.get_component(**kwargs))

    def set_attribute(
        self,
        attr_name: str,
        value: str | int | float | bool,
        **kwargs: Unpack[_ComponentSelector]
    ):
        if attr_name == 'custom_name':
            self.set_custom_name(str(value), **kwargs)

        self.get_component(**kwargs).set_attribute(attr_name, value)

    def set_custom_name(
        self,
        new_custom_name: str,
        **kwargs: Unpack[_ComponentSelector]
    ):
        component = self.get_component(**kwargs)
        if component.custom_name is not None:
            self._custom_name_map[component.custom_name].remove(component)
        component.set_custom_name(new_custom_name)
        self._custom_name_map[new_custom_name].add(component)

    def set_microprocessor_property(
        self,
        property_name: str,
        value: str | int,
        **kwargs: Unpack[_ComponentSelector]
    ):
        self.get_component(**kwargs)\
            .set_microprocessor_property(property_name, value)

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

        bodies = self._root.find('./bodies')
        assert bodies is not None
        bodies.remove(body2)

    def resolve_lua_script(self, build_params: Any = None, resolver: ScriptResolver | None = None):
        if resolver is None:
            resolver = ScriptResolver()

        for m in itertools.chain.from_iterable(self._microprocessor_name_map.values()):
            for o in m.element.findall('./o/microprocessor_definition/group/components/c[@type="56"]/object[@script]'):
                script = o.get('script')
                assert script is not None
                script = self._escape_multiline_attrs.restore_value(script)
                resolved = resolver.resolve_script(
                    script, build_params=build_params, leave_filename=True)
                if resolved is not None:
                    identifier = self._escape_multiline_attrs.add(
                        _remove_non_ascii(resolved))
                    o.set('script', identifier)
                else:
                    o.set('script', _remove_non_ascii(script))
