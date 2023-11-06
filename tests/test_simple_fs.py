import pytest

from sfs.fs import SimpleFS
from sfs.inode import FileType, INode


def get_raw_disk(blocks=100, block_size=32) -> bytearray:
    b = bytearray()

    for i in range(blocks):
        b.extend(i for _ in range(block_size))

    return b


def test_open():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    # Create fileA
    # Several data blocks
    # One Inode. Safe Inode and get index.

    # Create Dir2
    # one data block with name fileA and its inode index
    # One Inode. Safe Inode and get index.

    # Create Dir1
    # one data block with name Dir2 and its inode index
    # One Inode. Safe Inode and get index.

    # Save to root inode node
    # one data block with name Dir1 and its inode index
    # Add data block to root inode
    fs._serialize_dir_data({b'Dir1': })

    # Dir1
    data = bytearray(0 for _ in range(32))
    data[0] =
    data[1:8] = b'Dir1'

    # Dir2
    data[8] = 93
    data[9:16] = b'ANOTH\x00\x00'

    # fileA
    # Create root inode
    inode = INode(file_type=FileType.DIR)

    inode = fs.open(b'/Dir1/Dir2/fileA')

