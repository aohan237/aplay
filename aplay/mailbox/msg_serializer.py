import msgpack


class Serializer:
    def loads():
        raise ModuleNotFoundError

    def dumps():
        raise ModuleNotFoundError


class MsgPackSerializer:
    def loads(data):
        return msgpack.unpackb(data, raw=False)

    def dumps(data):
        return msgpack.packb(data, use_bin_type=True)
