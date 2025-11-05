from typing import Literal


LogicTypeName = Literal["bool", "number", "electric",
                        "composite", "video", "audio", "rope"]
LogicTypeNumber = Literal[0, 1, 4, 5, 6, 7, 8]


LOGIC_TYPE_NUMBER: dict[LogicTypeName, LogicTypeNumber] = {
    "bool": 0,
    "number": 1,
    "electric": 4,
    "composite": 5,
    "video": 6,
    "audio": 7,
    "rope": 8
}

LOGIC_TYPE_NAME: dict[LogicTypeNumber, LogicTypeName] = {
    0: "bool",
    1: "number",
    4: "electric",
    5: "composite",
    6: "video",
    7: "audio",
    8: "rope"
}
