import codecs
from pathlib import Path

import numpy
import ssz
import rlp
import tabulate

from cytoolz import (
    concat,
    curry,
    groupby,
    valmap,
)

from bimini.grammar import parse


def mk_rlp():
    from rlp.sedes import (
        BigEndianInt,
        Binary,
        big_endian_int,
        binary,
        CountableList,
    )
    #
    # RLP
    #
    address = Binary.fixed_length(20, allow_empty=True)
    hash32 = Binary.fixed_length(32)
    uint32 = BigEndianInt(32)
    uint256 = BigEndianInt(256)
    trie_root = Binary.fixed_length(32, allow_empty=True)

    class BlockHeader(rlp.Serializable):
        fields = [
            ('parent_hash', hash32),
            ('uncles_hash', hash32),
            ('coinbase', address),
            ('state_root', trie_root),
            ('transaction_root', trie_root),
            ('receipt_root', trie_root),
            ('bloom', uint256),
            ('difficulty', big_endian_int),
            ('block_number', big_endian_int),
            ('gas_limit', big_endian_int),
            ('gas_used', big_endian_int),
            ('timestamp', big_endian_int),
            ('extra_data', binary),
            ('mix_hash', binary),
            ('nonce', Binary(8, allow_empty=True))
        ]

    class Transaction(rlp.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('gas_price', big_endian_int),
            ('gas', big_endian_int),
            ('to', address),
            ('value', big_endian_int),
            ('data', binary),
            ('v', big_endian_int),
            ('r', big_endian_int),
            ('s', big_endian_int),
        ]

    class Block(rlp.Serializable):
        fields = [
            ('header', BlockHeader),
            ('transactions', CountableList(Transaction)),
            ('uncles', CountableList(BlockHeader))
        ]

    class Log(rlp.Serializable):
        fields = [
            ('address', address),
            ('topics', CountableList(uint32)),
            ('data', binary)
        ]

    class Receipt(rlp.Serializable):
        fields = [
            ('state_root', binary),
            ('gas_used', big_endian_int),
            ('bloom', uint256),
            ('logs', CountableList(Log))
        ]

    class Account(rlp.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('balance', big_endian_int),
            ('storage_root', trie_root),
            ('code_hash', hash32)
        ]

    class MiniAccount(rlp.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('balance', big_endian_int),
            ('storage_root', trie_root),
            ('code_hash', trie_root)
        ]

    class Address(rlp.Serializable):
        fields = [
            ('sender_ip', binary),
            ('sender_udp_port', big_endian_int),
            ('sender_tcp_port', big_endian_int),
        ]

    class Ping(rlp.Serializable):
        fields = [
            ('version', big_endian_int),
            ('from', Address),
            ('to', Address),
            ('expiration', big_endian_int),
        ]

    class Pong(rlp.Serializable):
        fields = [
            ('to', Address),
            ('ping_hash', binary),
            ('expiration', big_endian_int),
        ]

    class FindNode(rlp.Serializable):
        fields = [
            ('target', binary),
            ('expiration', big_endian_int),
        ]

    class Neighbour(rlp.Serializable):
        fields = [
            ('ip', binary),
            ('udp_port', big_endian_int),
            ('tcp_port', big_endian_int),
            ('node_id', binary),
        ]

    class Neighbours(rlp.Serializable):
        fields = [
            ('nodes', CountableList(Neighbour)),
            ('expiration', big_endian_int),
        ]

    return BlockHeader, Block, Receipt, CountableList(Receipt), Account, MiniAccount, Ping, Pong, FindNode, Neighbours  # noqa: E501


(
    RLPBlockHeader,
    RLPBlock,
    RLPReceipt,
    RLPReceipts,
    RLPAccount,
    RLPMiniAccount,
    RLPPing,
    RLPPong,
    RLPFindNode,
    RLPNeighbours,
) = mk_rlp()


def mk_ssz():
    #
    # SSZ
    #
    from ssz.sedes import (
        bytes32,
        UInt,
        bytes_sedes,
        List,
    )

    address = bytes_sedes
    uint256 = UInt(2048)
    uint32 = UInt(256)
    big_endian_int = uint32
    trie_root = bytes32
    hash32 = bytes32

    class BlockHeader(ssz.Serializable):
        fields = [
            ('parent_hash', hash32),
            ('uncles_hash', hash32),
            ('coinbase', address),
            ('state_root', trie_root),
            ('transaction_root', trie_root),
            ('receipt_root', trie_root),
            ('bloom', uint256),
            ('difficulty', big_endian_int),
            ('block_number', big_endian_int),
            ('gas_limit', big_endian_int),
            ('gas_used', big_endian_int),
            ('timestamp', big_endian_int),
            ('extra_data', bytes_sedes),
            ('mix_hash', bytes_sedes),
            ('nonce', bytes_sedes),
        ]

    class Transaction(ssz.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('gas_price', big_endian_int),
            ('gas', big_endian_int),
            ('to', address),
            ('value', big_endian_int),
            ('data', bytes_sedes),
            ('v', big_endian_int),
            ('r', big_endian_int),
            ('s', big_endian_int),
        ]

    class Block(ssz.Serializable):
        fields = [
            ('header', BlockHeader),
            ('transactions', List(Transaction)),
            ('uncles', List(BlockHeader))
        ]

    class Log(ssz.Serializable):
        fields = [
            ('address', address),
            ('topics', List(uint32)),
            ('data', bytes_sedes)
        ]

    class Receipt(ssz.Serializable):
        fields = [
            ('state_root', bytes_sedes),
            ('gas_used', big_endian_int),
            ('bloom', uint256),
            ('logs', List(Log))
        ]

    class Account(ssz.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('balance', big_endian_int),
            ('storage_root', trie_root),
            ('code_hash', hash32)
        ]

    class MiniAccount(ssz.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('balance', big_endian_int),
            ('storage_root', bytes_sedes),
            ('code_hash', bytes_sedes)
        ]

    class Address(ssz.Serializable):
        fields = [
            ('sender_ip', bytes_sedes),
            ('sender_udp_port', big_endian_int),
            ('sender_tcp_port', big_endian_int),
        ]

    class Ping(ssz.Serializable):
        fields = [
            ('version', big_endian_int),
            ('from', Address),
            ('to', Address),
            ('expiration', big_endian_int),
        ]

    class Pong(ssz.Serializable):
        fields = [
            ('to', Address),
            ('ping_hash', bytes_sedes),
            ('expiration', big_endian_int),
        ]

    class FindNode(ssz.Serializable):
        fields = [
            ('target', bytes_sedes),
            ('expiration', big_endian_int),
        ]

    class Neighbour(ssz.Serializable):
        fields = [
            ('ip', bytes_sedes),
            ('udp_port', big_endian_int),
            ('tcp_port', big_endian_int),
            ('node_id', bytes_sedes),
        ]

    class Neighbours(ssz.Serializable):
        fields = [
            ('nodes', List(Neighbour)),
            ('expiration', big_endian_int),
        ]

    return BlockHeader, Block, Transaction, Receipt, List(Receipt), Log, Account, MiniAccount, Ping, Pong, FindNode, Neighbours, List(bytes_sedes)  # noqa: E501


(
    SSZBlockHeader,
    SSZBlock,
    SSZTransaction,
    SSZReceipt,
    SSZReceipts,
    SSZLog,
    SSZAccount,
    SSZMiniAccount,
    SSZPing,
    SSZPong,
    SSZFindNode,
    SSZNeighbours,
    SSZTrieNode,
) = mk_ssz()


def decode_discovery_message(data):
    try:
        return rlp.decode(data, sedes=RLPPing)
    except rlp.exceptions.RLPException:
        pass

    try:
        return rlp.decode(data, sedes=RLPPong)
    except rlp.exceptions.RLPException:
        pass

    try:
        return rlp.decode(data, sedes=RLPFindNode)
    except rlp.exceptions.RLPException:
        pass

    try:
        return rlp.decode(data, sedes=RLPNeighbours)
    except rlp.exceptions.RLPException:
        pass

    raise Exception("Couldn't decode message")


def collate_discovery_messages(encoded_blobs):
    all_messages = tuple(map(decode_discovery_message, encoded_blobs))
    messages_by_type = groupby(type, all_messages)

    ping_blobs = tuple(rlp.encode(msg) for msg in messages_by_type[RLPPing])
    pong_blobs = tuple(rlp.encode(msg) for msg in messages_by_type[RLPPong])
    find_node_blobs = tuple(rlp.encode(msg) for msg in messages_by_type[RLPFindNode])
    neighbours_blobs = tuple(rlp.encode(msg) for msg in messages_by_type[RLPNeighbours])

    return ping_blobs, pong_blobs, find_node_blobs, neighbours_blobs


def collate_trie_nodes_by_depth(lines):
    trie_nodes_by_depth = valmap(lambda all_nodes: tuple(map(lambda node_hex: codecs.decode(node_hex, 'hex'), all_nodes)), {  # noqa: E501
        int(depth): tuple(zip(*depths_and_nodes))[1]
        for depth, depths_and_nodes
        in groupby(
            lambda depth_and_node: depth_and_node[0],
            tuple(
                tuple(line.split(' '))
                for line
                in lines
                if line
            )
        ).items()
    })
    return (
        trie_nodes_by_depth[0],
        trie_nodes_by_depth[1],
        trie_nodes_by_depth[2],
        trie_nodes_by_depth[3],
        trie_nodes_by_depth[4],
        trie_nodes_by_depth[5],
        trie_nodes_by_depth[6],
        trie_nodes_by_depth[7],
        trie_nodes_by_depth[8],
        trie_nodes_by_depth[9],
    )


BASE_PATH = Path(__file__).parent


HEADERS_PATH = BASE_PATH / 'headers.rlp'
BLOCKS_PATH = BASE_PATH / 'blocks.rlp'
RECEIPTS_PATH = BASE_PATH / 'receipts.rlp'
ACCOUNTS_PATH = BASE_PATH / 'accounts.rlp'
DISC_V4_MESSAGES_PATH = BASE_PATH / 'discv4.rlp'
TRIE_NODES_PATH = BASE_PATH / 'trie_nodes.rlp'


def unhex(hex_data):
    return codecs.decode(hex_data, 'hex')


RLP_RAW_HEADERS = tuple(filter(bool, map(unhex, HEADERS_PATH.read_bytes().splitlines())))
RLP_RAW_BLOCKS = tuple(filter(bool, map(unhex, BLOCKS_PATH.read_bytes().splitlines())))
RLP_RAW_RECEIPTS = tuple(
    rlp.encode(receipt)
    for receipt
    in concat(tuple(
        rlp.decode(data, sedes=RLPReceipts)
        for idx, data
        in enumerate(map(unhex, RECEIPTS_PATH.read_bytes().splitlines()))
        if data
    ))
)
RLP_RAW_ACCOUNTS = tuple(filter(bool, map(unhex, ACCOUNTS_PATH.read_bytes().splitlines())))

(
    RLP_RAW_TRIE_NODES_0,
    RLP_RAW_TRIE_NODES_1,
    RLP_RAW_TRIE_NODES_2,
    RLP_RAW_TRIE_NODES_3,
    RLP_RAW_TRIE_NODES_4,
    RLP_RAW_TRIE_NODES_5,
    RLP_RAW_TRIE_NODES_6,
    RLP_RAW_TRIE_NODES_7,
    RLP_RAW_TRIE_NODES_8,
    RLP_RAW_TRIE_NODES_9,
) = collate_trie_nodes_by_depth(tuple(filter(bool, TRIE_NODES_PATH.read_text().splitlines())))  # noqa: E501

(
    RLP_RAW_PINGS,
    RLP_RAW_PONGS,
    RLP_RAW_FIND_NODES,
    RLP_RAW_NEIGHBORS,
) = collate_discovery_messages(filter(bool, map(unhex, DISC_V4_MESSAGES_PATH.read_text().splitlines())))  # noqa: E501


RLP_HEADERS = tuple(rlp.decode(data, sedes=RLPBlockHeader) for data in RLP_RAW_HEADERS if data)
RLP_BLOCKS = tuple(rlp.decode(data, sedes=RLPBlock) for data in RLP_RAW_BLOCKS if data)
RLP_RECEIPTS = tuple(rlp.decode(data, sedes=RLPReceipt) for data in RLP_RAW_RECEIPTS if data)

RLP_TRANSACTIONS = tuple(concat(block.transactions for block in RLP_BLOCKS))
RLP_RAW_TRANSACTIONS = tuple(rlp.encode(txn) for txn in RLP_TRANSACTIONS)

RLP_LOGS = tuple(concat(receipt.logs for receipt in RLP_RECEIPTS))
RLP_RAW_LOGS = tuple(rlp.encode(log) for log in RLP_LOGS)

RLP_ACCOUNTS = tuple(rlp.decode(rlp.decode(data)[1], sedes=RLPAccount) for data in RLP_RAW_ACCOUNTS if data)  # noqa: E501

RLP_TRIE_NODES_0 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_0 if data)
RLP_TRIE_NODES_1 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_1 if data)
RLP_TRIE_NODES_2 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_2 if data)
RLP_TRIE_NODES_3 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_3 if data)
RLP_TRIE_NODES_4 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_4 if data)
RLP_TRIE_NODES_5 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_5 if data)
RLP_TRIE_NODES_6 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_6 if data)
RLP_TRIE_NODES_7 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_7 if data)
RLP_TRIE_NODES_8 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_8 if data)
RLP_TRIE_NODES_9 = tuple(rlp.decode(data) for data in RLP_RAW_TRIE_NODES_9 if data)

RLP_PINGS = tuple(rlp.decode(data, sedes=RLPPing) for data in RLP_RAW_PINGS if data)
RLP_PONGS = tuple(rlp.decode(data, sedes=RLPPong) for data in RLP_RAW_PONGS if data)
RLP_FIND_NODES = tuple(rlp.decode(data, sedes=RLPFindNode) for data in RLP_RAW_FIND_NODES if data)
RLP_NEIGHBORS = tuple(rlp.decode(data, sedes=RLPNeighbours) for data in RLP_RAW_NEIGHBORS if data)


sss_header_type_str = '{bytes32,bytes32,bytes20,bytes32,bytes32,bytes32,uint2048,scalar256,scalar256,scalar256,scalar256,scalar256,bytes,bytes,bytes8?}'  # noqa: E501
sss_header_type = parse(sss_header_type_str)
sss_txn_type_str = '{scalar256,scalar256,scalar256,bytes20?,scalar256,bytes,uint8,uint256,uint256}'  # noqa: E501
sss_txn_type = parse(sss_txn_type_str)
sss_block_type_str = '{%s,%s[],%s[]}' % (sss_header_type_str, sss_txn_type, sss_header_type_str)
sss_block_type = parse(sss_block_type_str)
sss_log_type_str = '{bytes20,uint256[],bytes}'
sss_log_type = parse(sss_log_type_str)
sss_receipt_type_str = '{bytes,scalar256,uint2048,%s[]}' % sss_log_type_str
sss_receipt_type = parse(sss_receipt_type_str)
sss_receipts_type = parse('%s[]' % sss_receipt_type_str)

sss_account_type = parse('{scalar256,scalar256,bytes32,bytes32}')
sss_mini_account_type = parse('{scalar256,scalar256,bytes32?,bytes32?}')

sss_trie_node_type = parse('bytes[]')

sss_address_type_str = '{bytes,scalar16,scalar16}'
sss_ping_type_str = '{scalar8,%s,%s,scalar32}' % (sss_address_type_str, sss_address_type_str)
sss_ping_type = parse(sss_ping_type_str)
sss_pong_type_str = '{%s,bytes,scalar32}' % sss_address_type_str
sss_pong_type = parse(sss_pong_type_str)
sss_find_node = parse('{bytes,scalar32}')
sss_neighbor_type_str = '{bytes,scalar16,scalar16,bytes}'
sss_neighbors_type_str = '{%s[],scalar32}' % sss_neighbor_type_str
sss_neighbors_type = parse(sss_neighbors_type_str)

# eth2.0

INFO_PERCENTILES = [99, 95, 90, 75, 50]
CMP_PERCENTILES = [1, 5, 10, 25, 50]


@curry
def dump_rlp_info(obj_name, encoded_blobs):
    sizes = tuple(len(data) for data in encoded_blobs)
    avg_size = sum(sizes) // len(encoded_blobs)

    (
        size_99th,
        size_95th,
        size_90th,
        size_75th,
        size_50th,
    ) = map(int, numpy.percentile(sizes, INFO_PERCENTILES))

    print(f"RLP-{obj_name}:")
    print("==========")
    print(f"average size     : {avg_size}")
    print("size-percentiles :")
    print(f" - 99th={size_99th}")
    print(f" - 95th={size_95th}")
    print(f" - 90th={size_90th}")
    print(f" - 75th={size_75th}")
    print(f" - 50th={size_50th}")
    return (obj_name, 'rlp', avg_size, size_99th, size_95th, size_90th, size_75th, size_50th)


@curry
def dump_sss_info(obj_name, sss_type, canonical_objs):
    encoded_blobs = tuple(sss_type.encode(obj) for obj in canonical_objs)
    sizes = tuple(len(data) for data in encoded_blobs)
    avg_size = sum(sizes) // len(encoded_blobs)

    (
        size_99th,
        size_95th,
        size_90th,
        size_75th,
        size_50th,
    ) = map(int, numpy.percentile(sizes, INFO_PERCENTILES))

    print(f"SSS-{obj_name}:")
    print("==========")
    print(f"average size     : {avg_size}")
    print("size-percentiles :")
    print(f" - 99th={size_99th}")
    print(f" - 95th={size_95th}")
    print(f" - 90th={size_90th}")
    print(f" - 75th={size_75th}")
    print(f" - 50th={size_50th}")
    return (obj_name, 'sss', avg_size, size_99th, size_95th, size_90th, size_75th, size_50th)


@curry
def dump_ssz_info(obj_name, ssz_sedes, canonical_objs):
    encoded_blobs = tuple(ssz.encode(obj, sedes=ssz_sedes) for obj in canonical_objs)
    sizes = tuple(len(data) for data in encoded_blobs)
    avg_size = sum(sizes) // len(encoded_blobs)

    (
        size_99th,
        size_95th,
        size_90th,
        size_75th,
        size_50th,
    ) = map(int, numpy.percentile(sizes, INFO_PERCENTILES))

    print(f"SSZ-{obj_name}:")
    print("==========")
    print(f"average size     : {avg_size}")
    print(f"size-percentiles :")
    print(f" - 99th={size_99th}")
    print(f" - 95th={size_95th}")
    print(f" - 90th={size_90th}")
    print(f" - 75th={size_75th}")
    print(f" - 50th={size_50th}")
    return (obj_name, 'ssz', avg_size, size_99th, size_95th, size_90th, size_75th, size_50th)


def pct(a, b):
    return 100 * (1 - a / b)


def pct_fmt(v):
    return f"{v:.2f}%"


@curry
def compare_rlp(obj_name, sss_type, canonical_objs):
    sss_blobs = tuple(sss_type.encode(obj) for obj in canonical_objs)
    sss_sizes = tuple(len(data) for data in sss_blobs)

    rlp_blobs = tuple(rlp.encode(obj) for obj in canonical_objs)
    rlp_sizes = tuple(len(data) for data in rlp_blobs)

    delta_pcts = tuple(pct(sss_size, rlp_size) for sss_size, rlp_size in zip(sss_sizes, rlp_sizes))
    avg_delta = sum(delta_pcts) / len(delta_pcts)

    (
        delta_99th,
        delta_95th,
        delta_90th,
        delta_75th,
        delta_50th,
    ) = numpy.percentile(delta_pcts, CMP_PERCENTILES)

    print(f"SSS vs RLP: {obj_name}")
    print("=======================")
    print(f"average savings     : {avg_delta:.2f}%")
    print("savings percentiles :")
    print(f" - 99th: {delta_99th:.2f}%")
    print(f" - 95th: {delta_95th:.2f}%")
    print(f" - 95th: {delta_95th:.2f}%")
    print(f" - 90th: {delta_90th:.2f}%")
    print(f" - 75th: {delta_75th:.2f}%")
    print(f" - 50th: {delta_50th:.2f}%")
    return (
        'rlp',
        obj_name,
        pct_fmt(avg_delta),
        pct_fmt(delta_99th),
        pct_fmt(delta_95th),
        pct_fmt(delta_90th),
        pct_fmt(delta_75th),
        pct_fmt(delta_50th),
    )


@curry
def compare_ssz(obj_name, ssz_sedes, sss_type, canonical_objs):
    sss_blobs = tuple(sss_type.encode(obj) for obj in canonical_objs)
    sss_sizes = tuple(len(data) for data in sss_blobs)

    ssz_blobs = tuple(ssz.encode(obj, sedes=ssz_sedes) for obj in canonical_objs)
    ssz_sizes = tuple(len(data) for data in ssz_blobs)

    delta_pcts = tuple(pct(sss_size, ssz_size) for sss_size, ssz_size in zip(sss_sizes, ssz_sizes))
    avg_delta = sum(delta_pcts) / len(delta_pcts)

    (
        delta_99th,
        delta_95th,
        delta_90th,
        delta_75th,
        delta_50th,
    ) = numpy.percentile(delta_pcts, CMP_PERCENTILES)

    print(f"SSS vs SSZ: {obj_name}")
    print("=======================")
    print(f"average savings     : {avg_delta:.2f}%")
    print("savings percentiles :")
    print(f" - 99th: {delta_99th:.2f}%")
    print(f" - 95th: {delta_95th:.2f}%")
    print(f" - 95th: {delta_95th:.2f}%")
    print(f" - 90th: {delta_90th:.2f}%")
    print(f" - 75th: {delta_75th:.2f}%")
    print(f" - 50th: {delta_50th:.2f}%")
    return (
        'ssz',
        obj_name,
        pct_fmt(avg_delta),
        pct_fmt(delta_99th),
        pct_fmt(delta_95th),
        pct_fmt(delta_90th),
        pct_fmt(delta_75th),
        pct_fmt(delta_50th),
    )


def rlp_meta():
    total_txns = sum(len(block.transactions) for block in RLP_BLOCKS)
    total_uncles = sum(len(block.uncles) for block in RLP_BLOCKS)
    total_logs = sum(len(receipt.logs) for receipt in RLP_RECEIPTS)

    print("RLP meta:")
    print("==========")
    print(f"num-headers      : {len(RLP_HEADERS)}")
    print(f"num-blocks       : {len(RLP_BLOCKS)}")
    print(f"num-receipts     : {len(RLP_RECEIPTS)}")
    print(f"num-txns         : {total_txns}")
    print(f"num-uncles       : {total_uncles}")
    print(f"num-logs         : {total_logs}")
    print(f"num-accounts     : {len(RLP_ACCOUNTS)}")
    print(f"num-trie-depth-0 : {len(RLP_TRIE_NODES_0)}")
    print(f"num-trie-depth-1 : {len(RLP_TRIE_NODES_1)}")
    print(f"num-trie-depth-2 : {len(RLP_TRIE_NODES_2)}")
    print(f"num-trie-depth-3 : {len(RLP_TRIE_NODES_3)}")
    print(f"num-trie-depth-4 : {len(RLP_TRIE_NODES_4)}")
    print(f"num-trie-depth-5 : {len(RLP_TRIE_NODES_5)}")
    print(f"num-trie-depth-6 : {len(RLP_TRIE_NODES_6)}")
    print(f"num-trie-depth-7 : {len(RLP_TRIE_NODES_7)}")
    print(f"num-trie-depth-8 : {len(RLP_TRIE_NODES_8)}")
    print(f"num-trie-depth-9 : {len(RLP_TRIE_NODES_9)}")
    print(f"num-ping         : {len(RLP_PINGS)}")
    print(f"num-pong         : {len(RLP_PONGS)}")
    print(f"num-find-node    : {len(RLP_FIND_NODES)}")
    print(f"num-neighbors    : {len(RLP_NEIGHBORS)}")


EMPTY_SHA3 = b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';\x7b\xfa\xd8\x04]\x85\xa4p"  # noqa: E501
BLANK_ROOT_HASH = b'V\xe8\x1f\x17\x1b\xccU\xa6\xff\x83E\xe6\x92\xc0\xf8n\x5bH\xe0\x1b\x99l\xad\xc0\x01b/\xb5\xe3c\xb4!'  # noqa: E501


def minify_account(account):
    if account.storage_root == BLANK_ROOT_HASH:
        storage_root = b''
    else:
        storage_root = account.storage_root

    if account.code_hash == EMPTY_SHA3:
        code_hash = b''
    else:
        code_hash = account.code_hash

    return RLPMiniAccount(
        account.nonce,
        account.balance,
        storage_root,
        code_hash,
    )


RLP_MINI_ACCOUNTS = tuple(minify_account(acct) for acct in RLP_ACCOUNTS)
RLP_RAW_MINI_ACCOUNTS = tuple(rlp.encode(acct) for acct in RLP_MINI_ACCOUNTS)


TRIPLETS = (
    ('block', RLP_BLOCKS, RLP_RAW_BLOCKS, sss_block_type, SSZBlock),
    ('header', RLP_HEADERS, RLP_RAW_HEADERS, sss_header_type, SSZBlockHeader),
    ('receipt', RLP_RECEIPTS, RLP_RAW_RECEIPTS, sss_receipt_type, SSZReceipt),
    ('log', RLP_LOGS, RLP_RAW_LOGS, sss_log_type, SSZLog),
    ('txn', RLP_TRANSACTIONS, RLP_RAW_TRANSACTIONS, sss_txn_type, SSZTransaction),
    ('acct', RLP_ACCOUNTS, RLP_RAW_ACCOUNTS, sss_account_type, SSZAccount),
    ('mini-acct', RLP_MINI_ACCOUNTS, RLP_RAW_MINI_ACCOUNTS, sss_mini_account_type, SSZMiniAccount),  # noqa: E501
    ('trie-depth-0', RLP_TRIE_NODES_0, RLP_RAW_TRIE_NODES_0, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-1', RLP_TRIE_NODES_1, RLP_RAW_TRIE_NODES_1, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-2', RLP_TRIE_NODES_2, RLP_RAW_TRIE_NODES_2, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-3', RLP_TRIE_NODES_3, RLP_RAW_TRIE_NODES_3, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-4', RLP_TRIE_NODES_4, RLP_RAW_TRIE_NODES_4, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-5', RLP_TRIE_NODES_5, RLP_RAW_TRIE_NODES_5, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-6', RLP_TRIE_NODES_6, RLP_RAW_TRIE_NODES_6, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-7', RLP_TRIE_NODES_7, RLP_RAW_TRIE_NODES_7, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-8', RLP_TRIE_NODES_8, RLP_RAW_TRIE_NODES_8, sss_trie_node_type, SSZTrieNode),
    ('trie-depth-9', RLP_TRIE_NODES_9, RLP_RAW_TRIE_NODES_9, sss_trie_node_type, SSZTrieNode),
    ('ping', RLP_PINGS, RLP_RAW_PINGS, sss_ping_type, SSZPing),
    ('pong', RLP_PONGS, RLP_RAW_PONGS, sss_pong_type, SSZPong),
    ('find-node', RLP_FIND_NODES, RLP_RAW_FIND_NODES, sss_find_node, SSZFindNode),
    ('neighbors', RLP_NEIGHBORS, RLP_RAW_NEIGHBORS, sss_neighbors_type, SSZNeighbours),
)


RLP_PINGS = tuple(rlp.decode(data, sedes=RLPPing) for data in RLP_RAW_PINGS if data)
RLP_PONGS = tuple(rlp.decode(data, sedes=RLPPong) for data in RLP_RAW_PONGS if data)
RLP_FIND_NODES = tuple(rlp.decode(data, sedes=RLPFindNode) for data in RLP_RAW_FIND_NODES if data)
RLP_NEIGHBORS = tuple(rlp.decode(data, sedes=RLPNeighbours) for data in RLP_RAW_NEIGHBORS if data)


INFOS_HEADER = ('TYPE', 'OBJ', 'AVG SIZE', 'SIZE-99th', 'SIZE-95th', 'SIZE-90th', 'SIZE-75th', 'SIZE-50th')  # noqa: E501
COMPARISONS_HEADER = ('TYPE', 'OBJ', 'AVG DELTA', 'DELTA-99th', 'DELTA-95th', 'DELTA-90th', 'DELTA-75th', 'DELTA-50th')  # noqa: E501


def main():
    rlp_meta()
    print('\n')

    comparisons = []
    infos = []

    for obj_name, canonical_objs, encoded_blobs, sss_type, ssz_sedes in TRIPLETS:
        infos.append(dump_rlp_info(obj_name, encoded_blobs))
        print('\n')
        infos.append(dump_sss_info(obj_name, sss_type, canonical_objs))
        print('\n')
        infos.append(dump_ssz_info(obj_name, ssz_sedes, canonical_objs))
        print('\n')
        comparisons.append(compare_rlp(obj_name, sss_type, canonical_objs))
        print('\n')
        comparisons.append(compare_ssz(obj_name, ssz_sedes, sss_type, canonical_objs))
        print('\n')

    print('\n')
    print('=========================================')
    print('          RAW INFO')
    print('=========================================')
    print(tabulate.tabulate(sorted(infos, key=lambda v: v[0]), headers=INFOS_HEADER, tablefmt="github"))  # noqa: E501

    print('\n')
    print('=========================================')
    print('          COMPARISONS')
    print('=========================================')
    print(tabulate.tabulate(sorted(comparisons, key=lambda v: v[0]), headers=COMPARISONS_HEADER, tablefmt="github"))  # noqa: E501


if __name__ == '__main__':
    main()
    import pdb
    pdb.set_trace()
