from typing import (
    Any,
    Tuple,
)


class BaseType:
    def __repr__(self) -> str:
        return f'<{str(self)}>'


class BitType(BaseType):
    def __init__(self, is_bool=False):
        self.is_bool = is_bool

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, BitType) and self.is_bool is other.is_bool

    def __str__(self) -> str:
        if self.is_bool:
            return 'bool'
        else:
            return 'bit'


class UnsignedIntegerType(BaseType):
    def __init__(self, bit_size: int):
        self.bit_size = bit_size

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, UnsignedIntegerType) and other.bit_size == self.bit_size

    def __str__(self) -> str:
        return f'uint{self.bit_size}'


class ByteType(UnsignedIntegerType):
    def __init__(self):
        super().__init__(bit_size=8)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ByteType) and other.bit_size == self.bit_size

    def __str__(self) -> str:
        return f'byte'


class ScalarType(BaseType):
    def __init__(self, bit_size: int):
        self.bit_size = bit_size

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ScalarType) and other.bit_size == self.bit_size

    def __str__(self) -> str:
        return f'scalar{self.bit_size}'


class ContainerType(BaseType):
    def __init__(self, element_types: Tuple[BaseType, ...]):
        self.element_types = element_types

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ContainerType):
            return False
        elif len(self.element_types) != len(other.element_types):
            return False
        else:
            return all(
                mine == theirs
                for mine, theirs
                in zip(self.element_types, other.element_types)
            )

    def __str__(self) -> str:
        return f'{"{"}{",".join((str(element_type) for element_type in self.element_types))}{"}"}'


class TupleType(BaseType):
    def __init__(self, item_type: BaseType, size: int):
        self.size = size
        self.item_type = item_type

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TupleType):
            return False
        else:
            return self.item_type == other.item_type and self.size == other.size

    def __str__(self) -> str:
        return f'{str(self.item_type)}[{self.size}]'


class ArrayType(BaseType):
    def __init__(self, item_type: BaseType):
        self.item_type = item_type

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ArrayType):
            return False
        else:
            return self.item_type == other.item_type

    def __str__(self) -> str:
        return f'{str(self.item_type)}[]'


class BytesType(ArrayType):
    def __init__(self):
        super().__init__(ByteType())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BytesType):
            return False
        else:
            return self.item_type == other.item_type

    def __str__(self) -> str:
        return 'bytes'


class FixedBytesType(TupleType):
    def __init__(self, size: int):
        super().__init__(ByteType(), size)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FixedBytesType):
            return False
        else:
            return self.item_type == other.item_type and self.size == other.size

    def __str__(self) -> str:
        return 'bytes{self.size}'
