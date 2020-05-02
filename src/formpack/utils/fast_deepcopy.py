import msgpack


def fast_deepcopy(obj):
    """
    This only works with simple JSON-like structures.
    """

    return msgpack.unpackb(
        msgpack.packb(obj, use_bin_type=True),
        encoding='utf-8'
    )
