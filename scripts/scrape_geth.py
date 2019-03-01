import argparse
import itertools
import plyvel
import struct
import sys
import time
import typing

import rlp

from eth_utils import toolz

from eth.rlp.accounts import Account
from eth.rlp.headers import BlockHeader
from trie.constants import (
    NODE_TYPE_BLANK,
    NODE_TYPE_BRANCH,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_LEAF,
    BLANK_NODE_HASH,
)
from trie.utils.nodes import (
    decode_node,
    get_node_type,
    extract_key,
    consume_common_prefix,
)
from trie.utils.nibbles import (
    bytes_to_nibbles,
    nibbles_to_bytes,
    add_nibbles_terminator,
    encode_nibbles,
)


class Node(typing.NamedTuple):
    kind: str
    rlp: bytes
    path: tuple


# from https://github.com/ethereum/go-ethereum/blob/master/core/rawdb/schema.go
LAST_BLOCK = b'LastBlock'
HEADER_PREFIX = b'h'
NUM_SUFFIX = b'n'
HEADER_NUMBER_PREFIX=b'H'


def int_to_prefix(num: int):
    # big-endian 8-byte unsigned int
    return struct.pack('>Q', num)


def get_node(db, nodehash):
    if len(nodehash) < 32:
        # non-root nodes smaller than 32 bytes are in-lined
        node_rlp = nodehash
    else:
        node_rlp = db.get(nodehash)
    if not node_rlp:
        raise Exception(f'was unable to fetch node {nodehash.hex()}')
    node = decode_node(node_rlp)
    return node_rlp, node


def traverse_branch(db, path, branch, start):
    if branch[16] != b'':
        print(f'weird branch: {path} {branch}')
        raise Exception('weird branch')

    try:
        start_index = start[0]
    except IndexError:
        # if we've gone deeper than start return everything
        start_index = 0

    for i in range(start_index, 16):
        if branch[i] != b'':
            yield from traverse_node(db, path + (i,), branch[i], start[1:])


def format_path(path) -> str:
    return ''.join(
        hex(item)[2:]
        for item in path
    )


def traverse_node(db, path, nodehash, start: int):
    node_rlp, node = get_node(db, nodehash)
    node_type = get_node_type(node)
    if node_type == NODE_TYPE_BRANCH:
        yield Node('branch', node_rlp, path)
        yield from traverse_branch(db, path, node, start)
    elif node_type == NODE_TYPE_LEAF:
        rest = extract_key(node)
        # TODO: also traverse the state root?
        yield Node('leaf', node_rlp, path + rest)
    elif node_type == NODE_TYPE_EXTENSION:
        # TODO: decide whether to yield this node, does it still match {start}
        # TODO: test that we're building this path correctly
        rest = extract_key(node)
        full_path = path + rest
        yield Node('extension', node_rlp, full_path)
        yield from traverse_node(db, full_path, node[1], start[1:])
    else:
        raise Exception(f"don't know how to handle type {node_type}")


def traverse_until_count(db, root, start, count):
    seen_leaves = 0
    for node in traverse_node(db, tuple(), root, start):
        if node.kind == 'leaf':
            seen_leaves += 1
        yield node
        if seen_leaves >= count:
            return


def should_continue(node_path, end_path):
    common, node_rest, end_rest = consume_common_prefix(node_path, end_path)
    if len(node_rest) == 0:
        # e.g. node_path, end_path = ffa, ffaf
        # everything from ffa{0-f} is yet to be explored
        return True
    if len(node_rest) and len(end_rest):
        # e.g. node_path, end_path = 0, 11
        # everything is left to be explored!
        return node_rest[0] < end_rest[0]
    if len(end_rest) == 0:
        # e.g. node_path, end_path = 110, 11
        # everything which remains will lie after {end_path}
        return False

    print(node_path, end_path, common, node_rest, end_rest)
    raise Exception('oh no')


def traverse_until_end(db, root, start, end):
    for node in traverse_node(db, tuple(), root, start):
        if not should_continue(node.path, end):
            return
        yield node


def open_db(path):
    return plyvel.DB(
        path,
        create_if_missing=False,
        error_if_exists=False,
        max_open_files=64
    )


def state_root_for(args, db):
    if not args.block:
        lastBlockHash = db.get(LAST_BLOCK)
        blockNum = db.get(HEADER_NUMBER_PREFIX + lastBlockHash)
        blockPrefix = HEADER_PREFIX + blockNum
    else:
        blockPrefix = HEADER_PREFIX + int_to_prefix(args.block)

    blockHashKey = blockPrefix + NUM_SUFFIX
    blockHash = db.get(blockHashKey)

    if not blockHash:
        raise Exception(f'could not find hash for block {args.block}')

    headerRlp = db.get(blockPrefix + blockHash)

    header = rlp.decode(headerRlp, sedes=BlockHeader)
    root = header.state_root
    print(f"retrieved header: {header} with stateroot: {root.hex()}")
    return root


def iterator_for(args, db, root):
    start = bytes.fromhex(args.start)
    start_nibbles = bytes_to_nibbles(start)
    if args.count:
        iterator = traverse_until_count(db, root, start_nibbles, args.count)
    else:
        end = bytes.fromhex(args.end)
        end_nibbles = bytes_to_nibbles(end)
        iterator = traverse_until_end(db, root, start_nibbles, end_nibbles)
    return iterator


def overhead(args):
    db = open_db(args.db)
    root = state_root_for(args, db)
    iterator = iterator_for(args, db, root)

    start = time.monotonic()

    overhead = 0
    leaf_weight = 0
    leaf_count = 0
    branch_count = 0
    extension_count = 0
    last_path = None

    for node in iterator:
        if node.kind == 'branch':
            branch_count += 1
            overhead += len(node.rlp)
            last_path = node.path
#            print(f'branch:   {format_path(node.path)}')
        elif node.kind == 'leaf':
            leaf_count += 1
            leaf_weight += len(node.rlp)
            last_path = node.path
#            print(f'leaf:     {format_path(node.path)}')
        elif node.kind == 'extension':
            extension_count += 1
            overhead += len(node.rlp)
            last_path = node.path
#            print(f'extension {format_path(node.path)}')
        else:
            print(f'unknown result {node.kind}')

    end = time.monotonic()
    print(f'ran in {end - start} seconds')
    print(f'found everything between {args.start} and {args.end}')
    print(f'last: {format_path(last_path)}')
    print(f'(bytes) overhead: {overhead} leaf: {leaf_weight}')
    print(f'overhead is {int((overhead/(overhead+leaf_weight))*100)}%')
    print(f'leaves: {leaf_count} branches: {branch_count} extensions: {extension_count}')


def traverse_prefix(db, root, prefix):
    """
    Return all nodes with the given prefix
    """
    for node in traverse_node(db, tuple(), root, prefix):
        common, node_rest, prefix_rest = consume_common_prefix(node.path, prefix)
        if len(node_rest) == 0 and len(prefix_rest) != 0:
            # we haven't reached the starting node yet
            continue
        if len(node_rest) == 0 and len(prefix_rest) == 0:
            # this is the starting node!
            yield node
            continue
        if len(prefix_rest) == 0 and len(node_rest):
            # this node is part of our prefix!
            yield node
            continue
        if len(prefix_rest) and len(node_rest):
            # this node is past our prefix
            break


def bins(args):
    """
    Build chunks and print summaries for each of them.

    If {depth} is 1, returns chunks with the prefixes: range(16)
    If {depth} is 2, returns chunks with the prefixes: itertools.product(range(16), range(16))
    and et cetera

    It will also print the size of the proof-chunk (0 if the depth is 1)
    """
    prefixes = itertools.product(*(range(16) for _ in range(args.depth)))
    prefixes = itertools.islice(prefixes, args.count)
    prefixes = list(prefixes)

    db = open_db(args.db)
    root = state_root_for(args, db)

    for prefix in prefixes:
        leaves, branches, extensions = 0, 0, 0
        leaf_weight, other_weight = 0, 0

        start = time.monotonic()

        for node in traverse_prefix(db, root, prefix):
            if node.kind == 'branch':
                branches += 1
                other_weight += len(node.rlp)
            elif node.kind == 'leaf':
                leaves += 1
                leaf_weight += len(node.rlp)
            elif node.kind == 'extension':
                extensions += 1
                other_weight += len(node.rlp)

        end = time.monotonic()

        print(f'{format_path(prefix)} leaves={leaves} other={branches+extensions} leaf_bytes={leaf_weight} other_bytes={other_weight} secs={end-start}')  # noqa: E501


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-db', type=str, required=True)
    parser.add_argument('-block', type=int, required=False)

    subparsers = parser.add_subparsers()

    # iterate over all the leaves in a given range and emit some statistics
    parser_overhead = subparsers.add_parser('overhead')
    parser_overhead.set_defaults(func=overhead)
    parser_overhead.add_argument('-start', type=str, required=True)

    end_type = parser_overhead.add_mutually_exclusive_group(required=True)
    end_type.add_argument('-end', type=str)
    end_type.add_argument('-count', type=int)

    # compare chunks to each other
    parser_bins = subparsers.add_parser('bins')
    parser_bins.set_defaults(func=bins)
    parser_bins.add_argument('-depth', type=int, required=True)
    parser_bins.add_argument('-count', type=int, required=False)
    parser_bins.add_argument('-prefix', type=str, required=False)

    args = parser.parse_args()
    args.func(args)
