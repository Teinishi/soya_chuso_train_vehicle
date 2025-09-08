from dataclasses import dataclass
import typing


@dataclass(frozen=True)
class Vector3i:
    x: int
    y: int
    z: int

    def __init__(self, x: int | tuple[int, int, int], y: int | None = None, z: int | None = None):
        if isinstance(x, tuple):
            x, y, z = x
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "z", z)

    def __add__(self, other: typing.Self) -> typing.Self:
        return Vector3i(self.x + other.x, self.y + other.y, self.z + other.z)

    def __repr__(self) -> str:
        return f"[{self.x}, {self.y}, {self.z}]"


@dataclass(frozen=True)
class Matrix3i:
    _mat: list[int]

    def __init__(self, text: str):
        mat = list(map(int, text.split(",")))
        if len(mat) != 9:
            raise ValueError("Matrix text does not have 9 numbers")
        object.__setattr__(self, "_mat", mat)

    @staticmethod
    def identity() -> typing.Self:
        return Matrix3i("1,0,0,0,1,0,0,0,1")

    def __repr__(self):
        return f"[[{self._m00}, {self._m01}, {self._m02}],\n [{self._m10}, {self._m11}, {self._m12}],\n [{self._m20}, {self._m21}, {self._m22}]]"

    def multiply_on_vector(self, vec: Vector3i) -> Vector3i:
        x, y, z = vec.x, vec.y, vec.z
        return Vector3i(
            self._mat[0]*x + self._mat[1]*y + self._mat[2]*z,
            self._mat[3]*x + self._mat[4]*y + self._mat[5]*z,
            self._mat[6]*x + self._mat[7]*y + self._mat[8]*z
        )
