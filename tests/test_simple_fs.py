import pytest

from sfs.fs import SimpleFS
from sfs.inode import FileType, INode


def get_raw_disk(blocks=100, block_size=32) -> bytearray:
    b = bytearray()

    for i in range(blocks):
        b.extend(i for _ in range(block_size))

    return b


def test_open_file_at_root():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    # Create fileA
    # Several data blocks
    data_node_indices = []
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'This is part A of file A')
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'This is part B of file A')
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'This is part C of file A')

    # Write INode for fileA
    inode = INode()
    inode_index = fs.index_node_bitmap.next()
    inode.data_blocks = data_node_indices
    fs._set_inode_block(inode_index, inode.serialize())

    # Record fileA in root dir
    root_inode = INode.parse(fs._get_inode_block(0))
    inode_index_by_name = fs._parse_dir_data(fs._get_data_for_inode(root_inode))
    inode_index_by_name[b'fileA'] = inode_index
    fs._set_data_for_inode(root_inode, fs._serialize_dir_data(inode_index_by_name))
    fs._set_inode_block(0, root_inode.serialize())

    returned_inode = fs.open(b'/fileA')
    assert returned_inode.data_blocks == inode.data_blocks


def test_open():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    # Create fileA
    # Several data blocks
    data_node_indices = []
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'This is part A of file A')
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'This is part B of file A')
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'This is part C of file A')

    # Write INode for fileA
    inode = INode()
    inode_index = fs.index_node_bitmap.next()
    inode.data_blocks = data_node_indices
    fs._set_inode_block(inode_index, inode.serialize())

    # Create Dir1 contents
    inode = INode(file_type=FileType.DIR)
    inode_index = fs.index_node_bitmap.next()
    fs._set_inode_block(inode_index, fs._serialize_dir_data({b'fileA': inode_index}))
    fs._set_inode_block(0, root_inode.serialize())



    # Record fileA in root dir
    root_inode = INode.parse(fs._get_inode_block(0))
    inode_index_by_name = fs._parse_dir_data(fs._get_data_for_inode(root_inode))
    inode_index_by_name[b'fileA'] = inode_index
    fs._set_data_for_inode(root_inode, fs._serialize_dir_data(inode_index_by_name))
    fs._set_inode_block(0, root_inode.serialize())

    returned_inode = fs.open(b'/Dir1/fileA')
    assert returned_inode.data_blocks == inode.data_blocks






    # Create Dir2
    # one data block with name fileA and its inode index
    # One Inode. Safe Inode and get index.

    # Create Dir1
    # one data block with name Dir2 and its inode index
    # One Inode. Safe Inode and get index.

    # Save to root inode node
    # one data block with name Dir1 and its inode index
    # Add data block to root inode
    fs._serialize_dir_data({b'File': })

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

