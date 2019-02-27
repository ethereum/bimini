import functools
from typing import (
    Any,
    Tuple,
)

import parsimonious
from parsimonious import (
    expressions,
)

from bimini.exceptions import (
    ParseError,
)


grammar = parsimonious.Grammar(r"""
type = basic_type / container_type / tuple_type / array_type / alias_type

container_type = container_types arrlist?
container_types = zero_container / non_zero_container
tuple_type = type const_arr
array_type = type dynam_arr

non_zero_container = "{" type next_type* "}"
next_type = "," type

zero_container = "{}"

basic_type = basic_types arrlist?
basic_types = integer_types / bit_type
bit_type = "bit"

integer_types = base_integer_type bit_size
bit_size = "8" / "16" / "24" / "32" / "40" / "48" / "56" / "64" / "72" / "80" / "88" / "96" /
           "104" / "112" / "120" / "128" / "136" / "144" / "152" / "160" / "168" / "176" /
           "184" / "192" / "200" / "208" / "216" / "224" / "232" / "240" / "248" / "256"
base_integer_type = "uint" / "scalar"

alias_type = alias_types arrlist?
alias_types = "bool" / bytes_type / byte_type / bytesN_type

bool_type = "bool"
bytes_type = "bytes"
byte_type = "byte"
bytesN_type = "bytes" digits

arrlist = dynam_arr / const_arr
dynam_arr = dynam_arr_comp any_arr_comp*
const_arr = const_arr_comp any_arr_comp*

any_arr_comp = (const_arr_comp / dynam_arr_comp)*

dynam_arr_comp = "[]"
const_arr_comp = "[" digits "]"

digits = ~"[1-9][0-9]*"
""")


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


def _reduce_arrlist(item_type, arr_type_meta):
    arr_type, arr_size = arr_type_meta
    if arr_type is TupleType:
        return TupleType(item_type, arr_size)
    elif arr_type is ArrayType:
        if arr_size is not None:
            raise Exception("INVALID")
        return ArrayType(item_type)
    else:
        raise Exception('INVARIANT')


class NodeVisitor(parsimonious.NodeVisitor):
    """
    Parsimonious node visitor which performs both parsing of type strings and
    post-processing of parse trees.  Parsing operations are cached.

    - container_type
    - tuple_type
    - array_type
    - non_zero_container
    - zero_container
    - basic_type
    - basic_types
    - bit_size
    - base_integer_type
    - integer_types
    - alias_type
    - alias_types
    - arrlist
    - dynam_arr
    - const_arr
    - any_arr_comp
    - dynam_arr_comp
    - const_arr_comp
    - digits
    """
    grammar = grammar

    def _maybe_reduce_arrlist(self, node, visited_children):
        base_type, arr_comps = visited_children
        if arr_comps is None:
            return base_type
        else:
            return functools.reduce(_reduce_arrlist, reversed(arr_comps), base_type)

    def visit_container_type(self, node, visited_children):
        return self._maybe_reduce_arrlist(node, visited_children)

    def visit_next_type(self, node, visited_children):
        # Ignore comma
        _, element_type = visited_children

        return element_type

    def visit_zero_container(self, node, visited_children):
        return ContainerType((), 0)

    def visit_non_zero_container(self, node, visited_children):
        # Ignore left and right braces
        _, first, rest, _ = visited_children

        return ContainerType((first,) + rest)

    ############
    def _visit_any_arr(self, node, visited_children):
        base_arr, tail_arrs = visited_children
        if tail_arrs:
            return (base_arr,) + tail_arrs[0]
        else:
            return (base_arr,)

    def visit_dynam_arr(self, node, visited_children):
        return self._visit_any_arr(node, visited_children)

    def visit_const_arr(self, node, visited_children):
        return self._visit_any_arr(node, visited_children)

    def visit_dynam_arr_comp(self, node, visited_children):
        return (ArrayType, None)

    def visit_const_arr_comp(self, node, visited_children):
        _, size, _ = visited_children
        return (TupleType, int(size))

    ############
    def visit_basic_type(self, node, visited_children):
        return self._maybe_reduce_arrlist(node, visited_children)

    def visit_bit_size(self, node, visited_children):
        return int(node.text)

    def visit_base_integer_type(self, node, visited_children):
        if node.text == 'uint':
            return UnsignedIntegerType
        elif node.text == 'scalar':
            return ScalarType
        else:
            raise Exception("Unreachable")

    def visit_integer_types(self, node, visited_children):
        base, bit_size = visited_children
        return base(bit_size)

    def visit_bit_type(self, node, visited_children):
        return BitType()
    ############
    """
    alias_type = alias_types arrlist?
    alias_types = bool_type / bytes_type / byte_type / bytesN_type

    bool_type = "bool"
    bytes_type = "bytes"
    byte_type = "byte"
    bytesN_type = "bytes" digits
    """
    def visit_bool_type(self, node, visited_children):
        return BitType(is_bool=True)

    def visit_bytes_type(self, node, visited_children):
        return ArrayType(UnsignedIntegerType(bit_size=8))

    def visit_byte_type(self, node, visited_children):
        return UnsignedIntegerType(bit_size=8)

    def visit_bytesN_type(self, node, visited_children):
        assert False

    ############

    def visit_digits(self, node, visited_children):
        return int(node.text)

    def generic_visit(self, node, visited_children):
        if isinstance(node.expr, expressions.OneOf):
            # Unwrap value chosen from alternatives
            return visited_children[0]

        if isinstance(node.expr, expressions.Optional):
            # Unwrap optional value or return `None`
            if len(visited_children) != 0:
                return visited_children[0]

            return None

        return tuple(visited_children)

    @functools.lru_cache(maxsize=None)
    def parse(self, type_str):
        """
        Parses a type string into an appropriate instance of
        :class:`~eth_abi.grammar.ABIType`.  If a type string cannot be parsed,
        throws :class:`~eth_abi.exceptions.ParseError`.

        :param type_str: The type string to be parsed.
        :returns: An instance of :class:`~eth_abi.grammar.ABIType` containing
            information about the parsed type string.
        """
        if not isinstance(type_str, str):
            raise TypeError('Can only parse string values: got {}'.format(type(type_str)))

        try:
            return super().parse(type_str)
        except parsimonious.ParseError as e:
            raise ParseError(e.text, e.pos, e.expr)


visitor = NodeVisitor()


TYPE_ALIASES = {
    'byte': 'uint8',
    'bytes': 'uint8[]',
    'bytesN': 'uint8[N]',
    'bool': 'bit'
}


def normalize(type_str):
    """
    TODO
    """
    assert False


parse = visitor.parse
