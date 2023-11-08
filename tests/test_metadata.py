import pytest

from sfs.fs import MetadataMixin
from sfs.inode import INode


def get_raw_disk(blocks=100, block_size=32) -> bytearray:
    b = bytearray()

    for i in range(blocks):
        b.extend(i for _ in range(block_size))

    return b


def test_format():
    raw_disk = get_raw_disk()

    fs = MetadataMixin(raw_disk)
    fs.format()

    formatted_disk = fs.serialize()

    # Super node
    assert formatted_disk[0:32] == b'SFS\x00\x01\x01\x086' + b'\x00' * 24
    # Inode Bitmap
    assert formatted_disk[32:33] == b'\x01'
    assert formatted_disk[33:64] == b'\x00' * 31
    # Data node Bitmap
    assert formatted_disk[64:65] == b'\x01'
    assert formatted_disk[65:96] == b'\x00' * 31

    # Inodes
    assert formatted_disk[96:97] == b'\x01'
    assert formatted_disk[97:128] == b'\x00' * 31

    # Rest of disk should not be touched. Format only clears bitmaps and first inode.
    assert formatted_disk[128:] == raw_disk[128:]


def test_get_data_for_inode():
    raw_disk = get_raw_disk() + bytearray(0 for _ in range(32*32))
    fs = MetadataMixin(raw_disk)
    fs.format()

    fs._set_data_block(3, bytes(b'Hi'))
    fs._set_data_block(5, bytes(b'Hello'))

    inode = INode()
    inode.data_blocks = [3, 5]

    data = fs._get_data_for_inode(inode)

    assert data[0:2] == b'Hi'
    assert data[32:37] == b'Hello'


def test_parse_dir_data():
    raw_disk = get_raw_disk()
    fs = MetadataMixin(raw_disk)
    fs.format()

    data = bytearray(0 for _ in range(32))
    data[0] = 47
    data[1:8] = b'TESTFIL'
    data[8] = 48
    data[9:16] = b'ANOTHER'

    inode_index_by_name = fs._parse_dir_data(data)
    assert inode_index_by_name == {b'ANOTHER': 48, b'TESTFIL': 47}


def test_serialize_dir_data():
    raw_disk = get_raw_disk()
    fs = MetadataMixin(raw_disk)
    fs.format()

    data = fs._serialize_dir_data({b'ANOTHER': 93, b'TESTFIL': 94})
    assert data == b']ANOTHER^TESTFIL'


def test_get_inode_block_from_dir_data():
    raw_disk = get_raw_disk()
    fs = MetadataMixin(raw_disk)
    fs.format()

    data = bytearray(0 for _ in range(32))
    data[0] = 21
    data[1:8] = b'TESTFIL'
    data[8] = 93
    data[9:16] = b'ANOTH\x00\x00'

    assert fs._get_inode_index_for_file_from_dir_data(data, b'TESTFIL') == 21
    assert fs._get_inode_index_for_file_from_dir_data(data, b'ANOTH') == 93

    with pytest.raises(FileNotFoundError):
        fs._get_inode_index_for_file_from_dir_data(data, b'JAZZ')
