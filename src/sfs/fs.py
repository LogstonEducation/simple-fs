"""
A very Simple File System (SFS).

Based off of the contents of Chapter 40 in OSTEP [1].


The file system is made up of a super block, several blocks of index nodes
(inodes), even more blocks of data, and bitmaps to indicate which blocks are
available.


[1]
"""
import math

from .bitmap import Bitmap
from .inode import FileType, INode


class SimpleFSError(Exception):
    """
    General error for SimpleFS class.
    """


class BaseFS:
    def __init__(self, raw_disk: bytearray, block_size: int=32) -> None:
        self._raw_disk = raw_disk
        self.block_size = block_size

        if len(self._raw_disk) % block_size != 0:
            raise SimpleFSError(
                f'Invalid disk size ({len(raw_disk)}) for given block size ({block_size})'
            )

        if len(self._raw_disk) < 5 * block_size:
            raise SimpleFSError(
                f'Disk too small ({len(raw_disk)}) for given block size ({block_size})'
            )

    def _get_block_slice_by_index(self, index: int) -> slice:
        start = index * self.block_size
        end = start + self.block_size
        return slice(start, end)

    def _set_block(self, index: int, data: bytes):
        """
        Set data at index. Pad data as required.
        """
        if index * self.block_size >= len(self._raw_disk):
            raise SimpleFSError(
                f'Index too large ({index}) for disk size in blocks'
            )

        if len(data) > self.block_size:
            raise SimpleFSError(
                f'Data length too large ({len(data)}) for given block size ({self.block_size})'
            )

        data = bytearray(data)

        padding = (self.block_size - len(data))
        for _ in range(padding):
            data.append(0)

        self._raw_disk[self._get_block_slice_by_index(index)] = data

    def _get_block(self, index: int) -> bytes:
        return self._raw_disk[self._get_block_slice_by_index(index)]

    def serialize(self) -> bytes:
        return bytes(self._raw_disk)


class MetadataMixin(BaseFS):
    SUPER_BLOCK_INDEX = 0
    # Offset from start of SUPER_BLOCK_INDEX into raw disk.
    INDEX_NODE_OFFSET = 1

    SUPER_BLOCK_INFO_MAGIC_INDEX = slice(0, 3)
    SUPER_BLOCK_INFO_MAGIC_VALUE = b'SFS'  # Magic number of SimpleFS
    SUPER_BLOCK_INFO_INODE_BLOCK_SIZE_INDEX = 4
    SUPER_BLOCK_INFO_INODE_BLOCK_COUNT_INDEX = 6
    SUPER_BLOCK_INFO_DATA_BLOCK_SIZE_INDEX = 5
    SUPER_BLOCK_INFO_DATA_BLOCK_COUNT_INDEX = 7

    @property
    def _super_block(self):
        block = self._get_block(self.SUPER_BLOCK_INDEX)
        assert block[self.SUPER_BLOCK_INFO_MAGIC_INDEX] == self.SUPER_BLOCK_INFO_MAGIC_VALUE
        return block

    def _reset_super_block(self):
        data = bytearray(0 for _ in range(self.block_size))
        data[self.SUPER_BLOCK_INFO_MAGIC_INDEX] = self.SUPER_BLOCK_INFO_MAGIC_VALUE
        data[self.SUPER_BLOCK_INFO_INODE_BLOCK_SIZE_INDEX] = 1  # Number of blocks for inode bitmap
        data[self.SUPER_BLOCK_INFO_DATA_BLOCK_SIZE_INDEX] = 1  # Number of blocks for data node bitmap
        data[self.SUPER_BLOCK_INFO_INODE_BLOCK_COUNT_INDEX] = 8  # Number of blocks for inodes
        data[self.SUPER_BLOCK_INFO_DATA_BLOCK_COUNT_INDEX] = 54  # Number of blocks for data blocks

        self._set_block(self.SUPER_BLOCK_INDEX, bytes(data))

    def _inode_bitmap_slice(self) -> slice:
        start = (self.SUPER_BLOCK_INDEX + self.INDEX_NODE_OFFSET) * self.block_size
        width = (self._super_block[self.SUPER_BLOCK_INFO_INODE_BLOCK_SIZE_INDEX] * self.block_size)

        return slice(start, start + width)

    @property
    def index_node_bitmap(self) -> Bitmap:
        return Bitmap(self._raw_disk, self._inode_bitmap_slice())

    def _data_bitmap_slice(self) -> slice:
        index_node_bitmap = self._inode_bitmap_slice()
        start = index_node_bitmap.stop

        width = (self._super_block[self.SUPER_BLOCK_INFO_DATA_BLOCK_SIZE_INDEX] * self.block_size)

        return slice(start, start + width)

    @property
    def data_node_bitmap(self) -> Bitmap:
        return Bitmap(self._raw_disk, self._data_bitmap_slice())

    def _to_raw_block_index(self, index: int, data_block=True) -> int:
        # Values are in terms of blocks, not bytes.
        inode_start = int(self._data_bitmap_slice().stop / self.block_size)
        inode_count = self._super_block[self.SUPER_BLOCK_INFO_INODE_BLOCK_COUNT_INDEX]

        data_block_start = inode_start + inode_count
        data_block_count = self._super_block[self.SUPER_BLOCK_INFO_DATA_BLOCK_COUNT_INDEX]

        if data_block:
            if index > data_block_count:
                raise SimpleFSError(f'Index {index} out of range of data nodes')

            return index + data_block_start

        # Is INode
        if index > (data_block_start - inode_start):
            raise SimpleFSError(f'Index {index} out of range of inodes')

        return index + inode_start

    def _get_inode_block(self, index: int) -> bytes:
        return self._get_block(self._to_raw_block_index(index, data_block=False))

    def _set_inode_block(self, index: int, data: bytes):
        self._set_block(self._to_raw_block_index(index, data_block=False), data)

    def _get_data_block(self, index: int) -> bytes:
        return self._get_block(self._to_raw_block_index(index, data_block=True))

    def _set_data_block(self, index: int, data: bytes):
        self._set_block(self._to_raw_block_index(index, data_block=True), data)

    def print_disk(self):
        for i in range(0, len(self._raw_disk), self.block_size):
            block_data = self._raw_disk[i:i+self.block_size]
            block = int(i / self.block_size)

            block_type = 'DN'
            if block == 0:
                block_type = 'S '
            elif block == 1:
                block_type = 'IB'
            elif block == 2:
                block_type = 'DB'
            elif block <= 10:
                block_type = 'IN'

            print(f'B {block} {block_type} >>', block_data, flush=True)

    def format(self):
        """
        Reset disk's bitmaps and super_block.
        """
        self._reset_super_block()
        self.index_node_bitmap.reset()
        self.data_node_bitmap.reset()

        # Create a root dir.
        data_block_index = self.data_node_bitmap.next()
        self._set_data_block(data_block_index, b'')

        inode = INode()
        inode.file_type = FileType.DIR
        inode.data_blocks.append(data_block_index)
        inode_block_index = self.index_node_bitmap.next()
        # Write inode to FIRST block in inodes block list.
        assert inode_block_index == 0
        self._set_inode_block(inode_block_index, inode.serialize())

    def _get_data_for_inode(self, inode: INode) -> bytes:
        data = bytearray()
        for data_block_id in inode.data_blocks:
            data.extend(self._get_data_block(data_block_id))
        return data

    def _set_data_for_inode(self, inode: INode, data: bytes):
        data_blocks_required = math.ceil(len(data) / self.block_size)
        data_blocks_to_aquire = data_blocks_required - len(inode.data_blocks)
        if data_blocks_to_aquire > 0:
            # get new blocks
            for _ in range(data_blocks_to_aquire):
                inode.data_blocks.append(self.data_node_bitmap.next())

        elif data_blocks_to_aquire < 0:
            # Release blocks
            for _ in range(-1 * data_blocks_to_aquire):
                self.data_node_bitmap.release(inode.data_blocks[-1])
                inode.data_blocks = inode.data_blocks[:-1]

        j = 0
        for i in range(0, len(data), self.block_size):
            self._set_data_block(inode.data_blocks[j], data[i:i+self.block_size])
            j += 1

    @staticmethod
    def _parse_dir_data(data: bytes) -> dict:
        inode_index_by_name = {}
        for i in range(0, len(data), 8):
            if not data[i]:
                break
            inode_index_by_name[bytes(data[i+1:i+8])] = data[i]
        return inode_index_by_name

    @staticmethod
    def _serialize_dir_data(data: dict) -> bytes:
        b = bytearray()
        for key, value in sorted(data.items()):
            if len(key) > 7:
                raise SimpleFSError(f'File name "{key}" too long {len(key)}')

            b.append(value)

            b.extend(key)
            for _ in range(7 - len(key)):
                b.append(0)

        return bytes(b)

    def _get_inode_index_for_file_from_dir_data(self, data: bytes, name: bytes) -> int:
        for file_name, inode_block_index in self._parse_dir_data(data).items():
            if name == file_name[:len(name)]:
                return inode_block_index

        raise FileNotFoundError(name)

    def _touch_in_dir(self, dir_inode_index: int, name: bytes, file_type=FileType.REG) -> int:
        # Create INode for item.
        inode = INode(file_type=file_type)
        inode_index = self.index_node_bitmap.next()
        self._set_inode_block(inode_index, inode.serialize())

        # Add item to parent dir's data.
        pinode = INode.parse(self._get_inode_block(dir_inode_index))
        inode_index_by_name = self._parse_dir_data(self._get_data_for_inode(pinode))
        inode_index_by_name[name] = inode_index
        self._set_data_for_inode(pinode, self._serialize_dir_data(inode_index_by_name))
        self._set_inode_block(dir_inode_index, pinode.serialize())

        return inode_index


class SimpleFS(MetadataMixin):

    def open(self, name: bytes, write=False) -> int:
        """
        Return an i-node (instead of a file descriptor) to the file referenced by "name".
        """
        name = name.lstrip(b'/')

        inode_block_index = 0
        while True:
            inode = INode.parse(self._get_inode_block(inode_block_index))  # Start at root node.
            if inode.file_type == FileType.REG:
                return inode_block_index

            data = self._get_data_for_inode(inode)

            name_part = name
            if name.find(b'/') > -1:
                name_part = name[:name.find(b'/')]
                name = name[name.find(b'/')+1:]

            try:
                inode_block_index = self._get_inode_index_for_file_from_dir_data(data, name_part)
            except FileNotFoundError as e:
                if not write:
                    raise e

                # If no more parts in name, consider a file to create.
                file_type = FileType.REG if name.find(b'/') == -1 else FileType.DIR
                inode_block_index = self._touch_in_dir(inode_block_index, name, file_type)

    def read(self, inode_index: int) -> bytes:
        """
        Return a series of bytes from a given i-node.
        """
        inode = INode.parse(self._get_inode_block(inode_index))
        data = self._get_data_for_inode(inode)
        i = 0
        while i < len(data):
            if data[i] == 0:
                break
            i += 1
        return bytes(data[:i])

    def write(self, inode_index: int, data: bytes):
        """
        Write a series of bytes to disk given an i-node.
        """
        inode = INode.parse(self._get_inode_block(inode_index))
        self._set_data_for_inode(inode, data)
        self._set_inode_block(inode_index, inode.serialize())
