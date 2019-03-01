from abc import (
    ABC,
    abstractmethod,
)
import io
from typing import (
    IO,
    Any,
    Generic,
    Tuple,
    TypeVar,
)

from bimini.exceptions import (
    DecodingError,
    EncodingError,
)
from bimini.decoders import (
    decode_bool,
    decode_uint,
    decode_scalar,
    decode_bytes,
)
from bimini.parsers import (
    parse_bool,
    parse_uint,
    parse_scalar,
    parse_container,
    parse_array,
    parse_tuple,
    parse_bytes,
)
from bimini.encoders import (
    encode_bool,
    encode_bytes,
    encode_uint,
    encode_scalar,
    encode_container,
    encode_tuple,
    encode_array,
)


T = TypeVar('T')


class BaseType(ABC, Generic[T]):
    def __repr__(self) -> str:
        return f'<{str(self)}>'

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def encode(self, value: T) -> bytes:
        pass

    @abstractmethod
    def decode(self, data: bytes) -> T:
        pass

    def s_encode(self, stream: IO[bytes], value: T) -> None:
        # TODO: optimize implementation for indivual types.
        stream.write(self.encode(value))

    @abstractmethod
    def s_decode(self, stream: IO[bytes]) -> T:
        pass


class BaseBit(BaseType[bool]):
    def __eq__(self, other: Any) -> bool:
        return type(self) is type(other)

    def encode(self, value: bool) -> bytes:
        return encode_bool(value)

    def decode(self, data: bytes) -> bool:
        return decode_bool(data)

    def s_decode(self, stream: IO[bytes]) -> bool:
        return parse_bool(stream)


class BitType(BaseBit):
    def __str__(self) -> str:
        return 'bit'


class BoolType(BaseBit):
    def __str__(self) -> str:
        return 'bool'


class UnsignedIntegerType(BaseType[int]):
    def __init__(self, bit_size: int):
        self.bit_size = bit_size

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, UnsignedIntegerType) and other.bit_size == self.bit_size

    def __str__(self) -> str:
        return f'uint{self.bit_size}'

    def encode(self, value: int) -> bytes:
        return encode_uint(self.bit_size, value)

    def decode(self, data: bytes) -> int:
        return decode_uint(self.bit_size, data)

    def s_decode(self, stream: IO[bytes]) -> int:
        return parse_uint(self.bit_size, stream)


class ByteType(BaseType[bytes]):
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ByteType)

    def __str__(self) -> str:
        return f'byte'

    def encode(self, value: bytes) -> bytes:
        if len(value) > 1:
            raise EncodingError("TODO: INVALID")
        return value

    def decode(self, data: bytes) -> bytes:
        if len(data) > 1:
            raise EncodingError("TODO: INVALID")
        return data

    def s_decode(self, stream: IO[bytes]) -> bytes:
        data = stream.read(1)
        if not data:
            raise EncodingError("TODO: INVALID")
        return data


class ScalarType(BaseType[int]):
    def __init__(self, bit_size: int):
        self.bit_size = bit_size

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ScalarType) and other.bit_size == self.bit_size

    def __str__(self) -> str:
        return f'scalar{self.bit_size}'

    def encode(self, value: int) -> bytes:
        return encode_scalar(self.bit_size, value)

    def decode(self, data: bytes) -> int:
        return decode_scalar(self.bit_size, data)

    def s_decode(self, stream: IO[bytes]) -> int:
        return parse_scalar(self.bit_size, stream)


class ContainerType(BaseType[Tuple[Any, ...]]):
    def __init__(self, element_types: Tuple[BaseType[Any], ...]):
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

    def encode(self, elements: Tuple[Any, ...]) -> bytes:
        element_encoders = tuple(
            element_type.encode
            for element_type
            in self.element_types
        )
        return encode_container(element_encoders, elements)

    def decode(self, data: bytes) -> Tuple[Any, ...]:
        return self.s_decode(io.BytesIO(data))

    def s_decode(self, stream: IO[bytes]) -> Tuple[Any, ...]:
        element_decoders = tuple(
            element_type.s_decode
            for element_type
            in self.element_types
        )
        return parse_container(element_decoders, stream)


class TupleType(BaseType[Tuple[Any, ...]]):
    def __init__(self, item_type: BaseType, length: int):
        self.length = length
        self.item_type = item_type

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TupleType):
            return False
        else:
            return self.item_type == other.item_type and self.length == other.length

    def __str__(self) -> str:
        return f'{str(self.item_type)}[{self.length}]'

    def encode(self, values: Tuple[Any, ...]) -> bytes:
        return encode_tuple(self.item_type.encode, values)

    def decode(self, data: bytes) -> Tuple[Any, ...]:
        return self.s_decode(io.BytesIO(data))

    def s_decode(self, stream: IO[bytes]) -> Tuple[Any, ...]:
        return parse_tuple(self.length, self.item_type.s_decode, stream)


class ArrayType(BaseType[Tuple[Any, ...]]):
    def __init__(self, item_type: BaseType):
        self.item_type = item_type

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ArrayType):
            return False
        else:
            return self.item_type == other.item_type

    def __str__(self) -> str:
        return f'{str(self.item_type)}[]'

    def encode(self, values: Tuple[Any, ...]) -> bytes:
        return encode_array(self.item_type.encode, values)

    def decode(self, data: bytes) -> Tuple[Any, ...]:
        return self.s_decode(io.BytesIO(data))

    def s_decode(self, stream: IO[bytes]) -> Tuple[Any, ...]:
        return parse_array(self.item_type.s_decode, stream)


class BytesType(BaseType[bytes]):
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, BytesType)

    def __str__(self) -> str:
        return 'bytes'

    def encode(self, value: Tuple[Any, ...]) -> bytes:
        return encode_bytes(value)

    def decode(self, data: bytes) -> bytes:
        return decode_bytes(data)

    def s_decode(self, stream: IO[bytes]) -> bytes:
        return parse_bytes(stream)


class OptionalType(BaseType[Any]):
    def __init__(self, value_type: BaseType) -> None:
        self.value_type = value_type

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, OptionalType) and other.value_type == self.value_type

    def __str__(self) -> str:
        return f'{self.value_type}?'

    def encode(self, value: Any) -> bytes:
        if value:
            return b'\x01' + self.value_type.encode(value)
        else:
            return b'\x00'

    def decode(self, data: bytes) -> Any:
        flag = data[0]
        if flag == 0:
            return b''
        elif flag == 1:
            return self.value_type.decode(data[1:])
        else:
            raise DecodingError('TODO: INVALID')

    def s_decode(self, stream: IO[bytes]) -> bytes:
        flag = stream.read(1)
        if flag == b'':
            raise DecodingError('TODO: MISSING FLAG')
        elif flag == b'\x00':
            return b''
        elif flag == b'\x01':
            return self.value_type.s_decode(stream)
        else:
            raise DecodingError('TODO: INVALID')


class FixedBytesType(BaseType[bytes]):
    def __init__(self, length: int):
        self.length = length

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, FixedBytesType) and self.length == other.length

    def __str__(self) -> str:
        return f'bytes{self.length}'

    def encode(self, value: Tuple[Any, ...]) -> bytes:
        if len(value) != self.length:
            raise EncodingError("TODO: INVALID SIZE")
        return value

    def decode(self, data: bytes) -> bytes:
        if len(data) != self.length:
            raise DecodingError("TODO: INVALID SIZE")
        return data

    def s_decode(self, stream: IO[bytes]) -> bytes:
        value = stream.read(self.length)
        if len(value) != self.length:
            raise DecodingError("TODO: INVALID SIZE")
        return value
