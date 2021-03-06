import functools
import itertools
import math
import operator
from typing import (
    Any,
    IO,
    Iterable,
    Callable,
    Tuple,
)
from cytoolz import curry

from bimini._utils.decorators import (
    to_tuple,
)
from bimini.decoders import (
    decode_bool,
)
from bimini.exceptions import (
    ParseError,
)


# TODO: combine with decoders


LOW_MASK = 2**7 - 1
HIGH_MASK = 2**7


def _read_exact(num_bytes: int, stream: IO[bytes]) -> bytes:
    data = stream.read(num_bytes)
    if len(data) != num_bytes:
        raise ParseError(f"Insufficient bytes in stream: needed {num_bytes},  got {len(data)}")
    return data


def _validate_bit_size(bit_size: int) -> None:
    # TODO: extract
    assert bit_size % 8 == 0
    assert 8 <= bit_size


@to_tuple
def _parse_unsigned_leb128(bit_size: int, stream: IO[bytes]) -> Iterable[int]:
    max_shift = int(math.ceil(bit_size / 7))
    for shift in itertools.count(0, 7):
        if shift > max_shift:
            raise ParseError("Parsed integer exceeds maximum bit size")

        byte = stream.read(1)

        try:
            value = byte[0]
        except IndexError:
            raise ParseError(
                "Unexpected end of stream while parsing LEB128 encoded integer"
            )

        yield (value & LOW_MASK) << shift

        if not value & HIGH_MASK:
            break


def parse_bool(stream: IO[bytes]) -> bool:
    byte = _read_exact(1, stream)
    return decode_bool(byte)


@curry
def parse_scalar(bit_size: int, stream: IO[bytes]) -> int:
    """
    https://en.wikipedia.org/wiki/LEB128
    """
    _validate_bit_size(bit_size)
    return functools.reduce(
        operator.or_,
        _parse_unsigned_leb128(bit_size, stream),
        0,
    )


@curry
def parse_uint(bit_size: int, stream: IO[bytes]) -> int:
    _validate_bit_size(bit_size)
    data = _read_exact(bit_size // 8, stream)
    return int.from_bytes(data, 'little')


@curry
def parse_fixed_bytes(num_bytes: int, stream: IO[bytes]) -> bytes:
    return _read_exact(num_bytes, stream)


@curry
def parse_bytes(stream: IO[bytes]) -> bytes:
    length = parse_scalar(32, stream)
    return parse_fixed_bytes(length, stream)


# TODO: use TypeVar to retain type data
ParseFn = Callable[[IO[bytes]], Any]


@curry
def parse_container(element_parsers: Tuple[ParseFn, ...], stream: IO[bytes]) -> Tuple[Any, ...]:
    return _parse_container(element_parsers, stream)


@to_tuple
def _parse_container(element_parsers: Tuple[ParseFn, ...], stream: IO[bytes]) -> Tuple[Any, ...]:
    for parser in element_parsers:
        yield parser(stream)


@curry
def parse_tuple(length: int, item_parser: ParseFn, stream: IO[bytes]) -> Tuple[Any, ...]:
    return _parse_tuple(length, item_parser, stream)


@to_tuple
def _parse_tuple(length: int, item_parser: ParseFn, stream: IO[bytes]) -> Iterable[Any]:
    for _ in range(length):
        yield item_parser(stream)


@curry
def parse_array(item_parser: ParseFn, stream: IO[bytes]) -> Tuple[Any, ...]:
    length = parse_scalar(32, stream)
    return _parse_tuple(length, item_parser, stream)
