from dataclasses import dataclass
import itertools
from typing import Literal
from xml.etree import ElementTree as ET
from lib.logic_type import LogicTypeName, LogicTypeNumber, LOGIC_TYPE_NAME
from lib.matrix import Vector3i, Matrix3i

Position = tuple[int, int, int]
Box = tuple[Vector3i, Vector3i]


@dataclass
class MicroprocessorNode:
    label: str
    mode: int
    type: LogicTypeNumber
    position2d: tuple[int, int]

    def is_output(self):
        return self.mode == 0

    def is_input(self):
        return self.mode == 1

    def type_name(self) -> LogicTypeName:
        return LOGIC_TYPE_NAME[self.type]

    def position(self) -> Vector3i:
        return Vector3i(self.position2d[0], 0, self.position2d[1])


class VehicleComponent:
    element: ET.Element
    _body: ET.Element
    _position: Vector3i
    _d: str
    _r: Matrix3i
    custom_name: str | None
    _microprocessor_name: str | None

    def __init__(self, element: ET.Element, body: ET.Element):
        self.element = element
        self._body = body

        self._d = element.get('d', '01_block')
        o = element.find('./o')
        assert o is not None
        r = o.get('r')
        self._r = Matrix3i.from_text(r) if r is not None else Matrix3i.identity()
        self.custom_name = o.get('custom_name')

        self._microprocessor_name = None
        if element.get('d') == 'microprocessor':
            mcdef = o.find('./microprocessor_definition')
            if mcdef is not None:
                self._microprocessor_name = mcdef.get('name')

        vp = o.find('./vp')
        self._position = Vector3i(0, 0, 0) if vp is None else Vector3i(
            int(vp.get('x', 0)), int(vp.get('y', 0)), int(vp.get('z', 0)))

    def get_element(self) -> ET.Element:
        return self.element

    def get_body(self) -> ET.Element:
        return self._body

    def get_definition_name(self) -> str:
        return self._d

    def get_position(self) -> Vector3i:
        return self._position

    def get_custom_name(self) -> str | None:
        return self.custom_name

    def get_microprocessor_name(self) -> str | None:
        return self._microprocessor_name

    def get_microprocessor_definition(self):
        mcdef = self.element.find('./o/microprocessor_definition')
        if self.element.get('d') != 'microprocessor' or mcdef is None:
            raise ValueError(
                'Attempt to get microprocessor definition of non-microprocessor')

        return mcdef

    def get_microprocessor_nodes(self) -> list[MicroprocessorNode]:
        mcdef = self.get_microprocessor_definition()

        nodes: list[MicroprocessorNode] = []
        for node in mcdef.findall('./nodes/n/node'):
            position_el = node.find('./position')
            if position_el is not None:
                position = (
                    int(position_el.get('x', 0)),
                    int(position_el.get('z', 0))
                )
            else:
                position = (0, 0)

            nodes.append(MicroprocessorNode(
                label=node.get('label', ''),
                mode=int(node.get('mode', 0)),
                type=int(node.get('type', 0)),  # type: ignore
                position2d=position
            ))

        return nodes

    def local_to_global_pos(self, local_pos: Vector3i):
        return self._r.multiply_on_vector(local_pos) + self._position

    def voxels(self) -> list[Vector3i]:
        # マイコンは width と length からサイズを取る
        if self.element.get('d') == 'microprocessor':
            mcdef = self.element.find('./o/microprocessor_definition')
            assert mcdef is not None
            width_s = mcdef.get('width')
            assert width_s is not None
            length_s = mcdef.get('length')
            assert length_s is not None
            width = int(width_s)
            length = int(length_s)

            result: list[Vector3i] = []
            for x, z in itertools.product(range(width), range(length)):
                result.append(
                    self._r.multiply_on_vector(Vector3i(x, 0, z))
                    + self.get_position()
                )
            return result

        # TODO: パーツ定義ファイルを見てボクセルを取得する
        # 現状は暫定的にパーツ原点のみを返す
        return [self.get_position()]
    
    def apply_transform(self, transform: Matrix3i):
        self._r = transform.multiply(self._r)
        if self._r.is_identity():
            self.remove_attribute('r')
        else:
            self.set_attribute('r', self._r.to_text())

    def rotate(self, axis: Literal['x', 'y', 'z'], count: int, pivot: Vector3i | None = None):
        # todo: pivot を考慮して位置を変更
        self.apply_transform(Matrix3i.rotation(axis, count))

    def remove_attribute(self, attr_name: str) -> str| None:
        o = self.element.find('./o')
        assert o is not None
        value = o.get(attr_name)
        del o.attrib[attr_name]
        return value

    def set_attribute(self, attr_name: str, value: str | int | float | bool):
        if value == False:
            value = 'false'
        elif value == True:
            value = 'true'
        else:
            value = str(value)
        o = self.element.find('./o')
        assert o is not None
        o.set(attr_name, value)

    def set_custom_name(self, new_custom_name: str):
        self.set_attribute('custom_name', new_custom_name)
        self.custom_name = new_custom_name

    def set_microprocessor_property(self, property_name: str, new_value: int | float | str):
        mcdef = self.get_microprocessor_definition()

        count = 0

        # Property Dropdown
        for dropdown in mcdef.findall('./group/components/c[@type="20"]/object') or []:
            name = dropdown.get('name') or 'value'
            if name != property_name:
                continue
            new_index = None
            if type(new_value) is int:
                n = len(dropdown.findall('./items/i'))
                if new_value < 0 or n <= new_value:
                    raise ValueError(
                        f'Index {new_value} is out of bounds for property dropdown "{property_name}" which has {n} options')
                new_index = new_value
            elif type(new_value) is str:
                options = [i.get('l') for i in dropdown.findall('./items/i')]
                try:
                    new_index = options.index(new_value)
                except ValueError:
                    raise ValueError(
                        f'No option named "{new_value}" found for property dropdown "{property_name}" witch only has {', '.join([f'"{l}"' for l in options])}')
            else:
                raise TypeError(
                    'Attempt to set propety dropdown with a non-str, non-int value')
            dropdown.set('i', str(new_index))
            count += 1

        # Property Number
        for prop_number in mcdef.findall('./group/components/c[@type="34"]/object') or []:
            name = prop_number.get('n') or 'number'
            if name != property_name:
                continue
            if type(new_value) is int or type(new_value) is float:
                v = prop_number.find('./v')
                assert v is not None
                v.set('text', str(new_value))
                v.set('value', str(new_value))
                count += 1
            else:
                raise TypeError(
                    'Attempt to set propety number with a non-number value')

        # Property Slider
        for prop_slider in mcdef.findall('./group/components/c[@type="19"]/object') or []:
            name = prop_slider.get('name') or 'value'
            if name != property_name:
                continue
            if type(new_value) is int or type(new_value) is float:
                val = float(new_value)
                v = prop_slider.find('./v')
                assert v is not None
                v = v.set('value', str(val))
                count += 1
            else:
                raise TypeError(
                    'Attempt to set propety slider with a non-number value')

        # Property Text
        for prop_text in mcdef.findall('./group/components/c[@type="58"]/object') or []:
            name = prop_text.get('n') or 'Label'
            if name != property_name:
                continue
            if type(new_value) is str:
                prop_text.set('v', new_value)
                count += 1
            else:
                raise TypeError(
                    'Attempt to set propety text with a non-str value')

        # Property Toggle
        for prop_toggle in mcdef.findall('./group/components/c[@type="33"]/object') or []:
            name = prop_toggle.get('n') or 'toggle'
            if name != property_name:
                continue
            new_bool = None
            if type(new_value) is bool:
                new_bool = new_value
            elif type(new_value) is str:
                on_label = prop_toggle.get('on', 'on')
                off_label = prop_toggle.get('off', 'off')
                if on_label == new_value:
                    new_bool = True
                elif off_label == new_value:
                    new_bool = False
                else:
                    raise ValueError(
                        f'Attempt to set property toggle with label "{new_value}" witch only has "{on_label}" or "{off_label}"')
            else:
                raise TypeError(
                    'Attempt to set propety toggle with a non-bool, non-str value')
            prop_toggle.set('v', 'true' if new_bool else 'false')
            count += 1

        if count == 0:
            raise ValueError(f'No property named "{property_name}" found')
