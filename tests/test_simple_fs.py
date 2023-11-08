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

    inode_index = fs.open(b'/fileA')
    assert INode.parse(fs._get_inode_block(inode_index)).data_blocks == inode.data_blocks


def test_open():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    # Create fileA
    # Several data blocks
    file_data_node_indices = data_node_indices = []
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
    data_node_indices = []
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], fs._serialize_dir_data({b'fileA': inode_index}))

    inode = INode(file_type=FileType.DIR)
    inode_index = fs.index_node_bitmap.next()
    inode.data_blocks = data_node_indices
    fs._set_inode_block(inode_index, inode.serialize())

    # Create Dir2 contents
    data_node_indices = []
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], fs._serialize_dir_data({b'Dir1': inode_index}))

    inode = INode(file_type=FileType.DIR)
    inode_index = fs.index_node_bitmap.next()
    inode.data_blocks = data_node_indices
    fs._set_inode_block(inode_index, inode.serialize())

    # Record Dir2 in root dir
    root_inode = INode.parse(fs._get_inode_block(0))
    inode_index_by_name = fs._parse_dir_data(fs._get_data_for_inode(root_inode))
    inode_index_by_name[b'Dir2'] = inode_index
    fs._set_data_for_inode(root_inode, fs._serialize_dir_data(inode_index_by_name))
    fs._set_inode_block(0, root_inode.serialize())

    inode_index = fs.open(b'/Dir2/Dir1/fileA')
    assert INode.parse(fs._get_inode_block(inode_index)).data_blocks == file_data_node_indices


def test_open_none_existent():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    with pytest.raises(FileNotFoundError):
        fs.open(b'/Dir2/Dir1/fileA')


def test_read_file():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    # Create fileA
    # Several data blocks
    data_node_indices = []
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'A' * 32)
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'B' * 32)
    data_node_indices.append(fs.data_node_bitmap.next())
    fs._set_data_block(data_node_indices[-1], b'C' * 32)

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

    assert fs.read(fs.open(b'/fileA')) == b''.join((
        (b'A' * 32),
        (b'B' * 32),
        (b'C' * 32),
    ))


def test_write_file():
    raw_disk = get_raw_disk()
    fs = SimpleFS(raw_disk)
    fs.format()

    fs.write(fs.open(b'/fileA', write=True),
        b'This is part D of file A'
        b'This is part E of file A'
        b'This is part F of file A'
    )

    assert fs.read(fs.open(b'/fileA')) == (
        b'This is part D of file A'
        b'This is part E of file A'
        b'This is part F of file A'
    )
