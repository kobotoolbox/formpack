import msgpack
import sys


def fast_deepcopy(obj):
    """
    This only works with simple JSON-like structures.
    """

    if sys.version_info[0] == 2:
        return msgpack.unpackb(
            msgpack.packb(obj, use_bin_type=True),
            encoding='utf-8'
        )

    return msgpack.unpackb(msgpack.packb(obj))
