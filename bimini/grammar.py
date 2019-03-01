import functools
from typing import (
    Optional,
    Tuple,
    Union,
)

import parsimonious
from parsimonious import (
    expressions,
)

from bimini.exceptions import (
    ParseError,
)
from bimini.types import (
    ArrayType,
    BaseType,
    BitType,
    ByteType,
    BytesType,
    FixedBytesType,
    BoolType,
    ContainerType,
    OptionalType,
    ScalarType,
    TupleType,
    UnsignedIntegerType,
)


grammar = parsimonious.Grammar(r"""
type = types optional?
types = basic_type / alias_type / container_type / tuple_type / array_type

container_type = container_types optional? arrlist?
container_types = zero_container / non_zero_container
tuple_type = type const_arr optional?
array_type = type dynam_arr optional?

non_zero_container = "{" type next_type* "}"
next_type = "," type

zero_container = "{}"

optional = "?"

basic_type = basic_types optional? arrlist?
basic_types = integer_types / bit_type
bit_type = "bit"

integer_types = base_integer_type bit_size
bit_size = ~"[1-9][0-9]*"
base_integer_type = "uint" / "scalar"

alias_type = alias_types optional? arrlist?
alias_types = bool_type / bytesN_type / bytes_type / byte_type

bytesN_type = bytes_type digits

bool_type = "bool"
bytes_type = "bytes"
byte_type = "byte"

arrlist = dynam_arr / const_arr
dynam_arr = dynam_arr_comp any_arr_comp*
const_arr = const_arr_comp any_arr_comp*

any_arr_comp = (const_arr_comp / dynam_arr_comp)*

dynam_arr_comp = "[]"
const_arr_comp = "[" digits "]"

digits = ~"[1-9][0-9]*"
""")


ArrTypeMeta = Tuple[Union[ArrayType, TupleType], Optional[int]]


def _reduce_arrlist(item_type: BaseType,
                    arr_type_meta: ArrTypeMeta,
                    ) -> Union[TupleType, ArrayType]:
    arr_type, arr_size = arr_type_meta
    if arr_type is TupleType:
        return TupleType(item_type, arr_size)
    elif arr_type is ArrayType:
        if arr_size is not None:
            raise Exception("INVALID")
        else:
            return ArrayType(item_type)
    else:
        raise Exception('INVARIANT')


class NodeVisitor(parsimonious.NodeVisitor):
    """
    Parsimonious node visitor which performs both parsing of type strings and
    post-processing of parse trees.  Parsing operations are cached.
    """
    grammar = grammar

    def _maybe_reduce_arrlist(self, node, visited_children):
        base_type, optional, arr_comps = visited_children

        if optional:
            declared_type = optional(base_type)
        else:
            declared_type = base_type

        if arr_comps is None:
            value_type = declared_type
        else:
            value_type = functools.reduce(_reduce_arrlist, reversed(arr_comps), declared_type)

        return value_type

    def visit_type(self, node, visited_children):
        value_type, optional = visited_children

        if optional:
            return optional(value_type)
        else:
            return value_type

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

    def visit_optional(self, node, visited_children):
        return OptionalType

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
        bit_size = int(node.text)
        if bit_size % 8 != 0:
            raise ParseError("Invalid bit_size.  Must be multiple of 8")
        return bit_size

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
    def visit_alias_type(self, node, visited_children):
        return self._maybe_reduce_arrlist(node, visited_children)

    def visit_bool_type(self, node, visited_children):
        return BoolType()

    def visit_byte_type(self, node, visited_children):
        return ByteType()

    def visit_bytes_type(self, node, visited_children):
        return BytesType()

    def visit_bytesN_type(self, node, visited_children):
        # we discard the parsed type to replace with just a `byte` type.
        _, size = visited_children
        return FixedBytesType(size)

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
