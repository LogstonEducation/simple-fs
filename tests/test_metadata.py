import pytest

from sfs.fs import MetadataMixin


def get_raw_disk(blocks=10, block_size=32) -> bytearray:
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
