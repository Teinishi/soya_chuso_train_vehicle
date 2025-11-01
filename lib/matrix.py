from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Vector3i:
    x: int
    y: int
    z: int

    def __init__(self, x: int | Vector3i | tuple[int, int, int], y: int | None = None, z: int | None = None):
        if isinstance(x, Vector3i):
            x, y, z = x.x, x.y, x.z
        elif isinstance(x, tuple):
            x, y, z = x
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)
        object.__setattr__(self, 'z', z)

    def __add__(self, other: Vector3i) -> Vector3i:
        return Vector3i(self.x + other.x, self.y + other.y, self.z + other.z)

    def __repr__(self) -> str:
        return f'[{self.x}, {self.y}, {self.z}]'

    def to_xml_dict(self) -> dict[str, str]:
        return {
            'x': str(self.x),
            'y': str(self.y),
            'z': str(self.z)
        }


@dataclass(frozen=True)
class Matrix3i:
    _mat: list[int]

    def __init__(self, text: str):
        mat = list(map(int, text.split(',')))
        if len(mat) != 9:
            raise ValueError('Matrix text does not have 9 numbers')
        object.__setattr__(self, '_mat', mat)

    @staticmethod
    def identity() -> Matrix3i:
        return Matrix3i('1,0,0,0,1,0,0,0,1')

    def multiply_on_vector(self, vec: Vector3i) -> Vector3i:
        x, y, z = vec.x, vec.y, vec.z
        return Vector3i(
            self._mat[0]*x + self._mat[1]*y + self._mat[2]*z,
            self._mat[3]*x + self._mat[4]*y + self._mat[5]*z,
            self._mat[6]*x + self._mat[7]*y + self._mat[8]*z
        )
