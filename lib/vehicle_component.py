import itertools
from xml.etree import ElementTree as ET
from lib.matrix import Vector3i, Matrix3i

Position = tuple[int, int, int]
Box = tuple[Vector3i, Vector3i]


class VehicleComponent:
    _element: ET.Element
    _body: ET.Element
    _position: Vector3i
    _d: str
    _r: Matrix3i
    _custom_name: str | None
    _microprocessor_name: str | None

    def __init__(self, element: ET.Element, body: ET.Element):
        self._element = element
        self._body = body

        self._d = element.get("d", "01_block")
        o = element.find("./o")
        r = o.get("r")
        self._r = Matrix3i(r) if r is not None else Matrix3i.identity()
        self._custom_name = o.get("custom_name")

        self._microprocessor_name = None
        if element.get("d") == "microprocessor":
            mcdef = o.find("./microprocessor_definition")
            if mcdef is not None:
                self._microprocessor_name = mcdef.get("name")

        vp = o.find("./vp")
        self._position = Vector3i(0, 0, 0) if vp is None else Vector3i(
            int(vp.get("x", 0)), int(vp.get("y", 0)), int(vp.get("z", 0)))

    def get_element(self) -> ET.Element:
        return self._element

    def get_body(self) -> ET.Element:
        return self._body

    def get_definition_name(self) -> str:
        return self._d

    def get_position(self) -> Vector3i:
        return self._position

    def get_custom_name(self) -> str | None:
        return self._custom_name

    def get_microprocessor_name(self) -> str | None:
        return self._microprocessor_name

    def voxels(self) -> list[Vector3i]:
        # マイコンは width と length からサイズを取る
        if self._element.get("d") == "microprocessor":
            mcdef = self._element.find("./o/microprocessor_definition")
            width = int(mcdef.get("width"))
            length = int(mcdef.get("length"))

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

    def _set_attribute(self, attr_name: str, value: str | int | float | bool):
        if value == False:
            value = "false"
        elif value == True:
            value = "true"
        else:
            value = str(value)
        self._element.find("./o").set(attr_name, value)

    def _set_custom_name(self, new_custom_name: str):
        self._set_attribute("custom_name", new_custom_name)
        self._custom_name = new_custom_name

    def _set_microprocessor_property(self, property_name: str, new_value: int | float | str):
        if self._element.get("d") != "microprocessor":
            raise ValueError(
                "Attempt to set microprocessor property for non-microprocessor")

        mcdef = self._element.find("./o/microprocessor_definition")
        count = 0

        # Property Dropdown
        for dropdown in mcdef.findall('./group/components/c[@type="20"]/object') or []:
            name = dropdown.get("name") or "value"
            if name != property_name:
                continue
            new_index = None
            if type(new_value) is int:
                n = len(dropdown.findall("./items/i"))
                if new_value < 0 or n <= new_value:
                    raise ValueError(
                        f'Index {new_value} is out of bounds for property dropdown "{property_name}" which has {n} options')
                new_index = new_value
            elif type(new_value) is str:
                options = [i.get("l") for i in dropdown.findall("./items/i")]
                try:
                    new_index = options.index(new_value)
                except ValueError:
                    raise ValueError(
                        f'No option named "{new_value}" found for property dropdown "{property_name}" witch only has {", ".join([f'"{l}"' for l in options])}')
            else:
                raise TypeError(
                    "Attempt to set propety dropdown with a non-str, non-int value")
            dropdown.set("i", str(new_index))
            count += 1

        # Property Number
        for prop_number in mcdef.findall('./group/components/c[@type="34"]/object') or []:
            name = prop_number.get("n") or "number"
            if name != property_name:
                continue
            if type(new_value) is int or type(new_value) is float:
                prop_number.find("./v").set("value", str(float(new_value)))
                count += 1
            else:
                raise TypeError(
                    "Attempt to set propety number with a non-number value")

        # Property Slider
        for prop_slider in mcdef.findall('./group/components/c[@type="19"]/object') or []:
            name = prop_slider.get("name") or "value"
            if name != property_name:
                continue
            if type(new_value) is int or type(new_value) is float:
                val = float(new_value)
                prop_slider.find("./v").set("value", str(val))
                count += 1
            else:
                raise TypeError(
                    "Attempt to set propety slider with a non-number value")

        # Property Text
        for prop_text in mcdef.findall('./group/components/c[@type="58"]/object') or []:
            name = prop_text.get("n") or "Label"
            if name != property_name:
                continue
            if type(new_value) is str:
                prop_text.set("v", new_value)
                count += 1
            else:
                raise TypeError(
                    "Attempt to set propety text with a non-str value")

        # Property Toggle
        for prop_toggle in mcdef.findall('./group/components/c[@type="33"]/object') or []:
            name = prop_toggle.get("n") or "toggle"
            if name != property_name:
                continue
            new_bool = None
            if type(new_value) is bool:
                new_bool = new_value
            elif type(new_value) is str:
                on_label = prop_toggle.get("on", "on")
                off_label = prop_toggle.get("off", "off")
                if on_label == new_value:
                    new_bool = True
                elif off_label == new_value:
                    new_bool = False
                else:
                    raise ValueError(
                        f'Attempt to set property toggle with label "{new_value}" witch only has "{on_label}" or "{off_label}"')
            else:
                raise TypeError(
                    "Attempt to set propety toggle with a non-bool, non-str value")
            prop_toggle.set("v", "true" if new_bool else "false")
            count += 1

        if count == 0:
            raise ValueError(f'No property named "{property_name}" found')
