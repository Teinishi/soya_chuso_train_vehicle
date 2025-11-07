from __future__ import annotations
from dataclasses import dataclass
import itertools
from typing import Literal


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

    @staticmethod
    def from_text(text: str):
        mat = list(map(int, text.split(',')))
        if len(mat) != 9:
            raise ValueError('Matrix text does not have 9 numbers')
        return Matrix3i(mat)

    @staticmethod
    def identity() -> Matrix3i:
        return Matrix3i([1, 0, 0, 0, 1, 0, 0, 0, 1])
    
    @staticmethod
    def rotation(axis: Literal['x', 'y', 'z'], count: int) -> Matrix3i:
        axis_n = 'xyz'.index(axis)
        axis_n1 = (axis_n + 1) % 3
        axis_n2 = (axis_n + 2) % 3
        c = [1, 0, -1, 0][count % 4] # cos(count * 90deg)
        s = [0, 1, 0, -1][count % 4] # sin(count * 90deg)

        m = Matrix3i.identity()
        m._mat[3 * axis_n1 + axis_n1] = c
        m._mat[3 * axis_n1 + axis_n2] = -s
        m._mat[3 * axis_n2 + axis_n1] = s
        m._mat[3 * axis_n2 + axis_n2] = c
        return m
    
    def is_identity(self) -> bool:
        return self == Matrix3i.identity()
    
    def multiply(self, other: Matrix3i) -> Matrix3i:
        new_mat = [0] * 9
        for i, j, k in itertools.product(range(3), repeat=3):
            new_mat[3 * i + j] += self._mat[3 * i + k] * other._mat[3 * k + j]
        return Matrix3i(new_mat)

    def multiply_on_vector(self, vec: Vector3i) -> Vector3i:
        x, y, z = vec.x, vec.y, vec.z
        return Vector3i(
            self._mat[0]*x + self._mat[1]*y + self._mat[2]*z,
            self._mat[3]*x + self._mat[4]*y + self._mat[5]*z,
            self._mat[6]*x + self._mat[7]*y + self._mat[8]*z
        )

    def to_text(self) -> str:
        return ','.join(map(str, self._mat))
