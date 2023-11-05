from enum import Enum


class INodeError:
    """
    General error for the INode class.
    """


class FileType(Enum):
    DIR = 1
    REG = 2


class INode:

    def __init__(self, file_type: FileType=FileType.REG):
        self.file_type: FileType = file_type
        self.data_blocks: list = []

    def serialize(self):
        b = bytearray()

        b.append(self.file_type.value)
        b.extend(self.data_blocks)

        return b

    @classmethod
    def parse(cls, data: bytes) -> 'INode':
        inode = cls()

        inode.file_type = FileType(data[0])

        inode.data_blocks = []
        for data_block_id in data[1:]:
            # Only consider data up to first null.
            if not data_block_id:
                break
            inode.data_blocks.append(data_block_id)

        return inode
