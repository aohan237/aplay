import uuid
from collections import UserDict


class Msg(UserDict):

    """Docstring for Msg."""

    def __getattr__(self, attr):
        return super(Msg, self).__getitem__(attr)

    def __setattr__(self, attr, value):
        if "data" in self.__dict__:
            self.__dict__["data"][attr] = value
        else:
            super(Msg, self).__setattr__(attr, value)

    def __delattr__(self, attr, value):
        if "data" in self.__dict__:
            res = self.__dict__["data"].pop(attr)
        else:
            res = super(Msg, self).__delattr__(attr)
        return res

    def __init__(self, source=None, target=None, flow_id=None, flow_index=0, body=None):
        """TODO: to be defined."""
        self.data = {
            "source": source,
            "flow_id": flow_id if flow_id is not None else str(uuid.uuid4()),
            "flow_index": flow_index + 1,
            "body": body,
        }


def format_msg(source=None, target=None, flow_id=None, flow_index=0, body=None):
    msg = Msg(
        source=source, target=target, flow_id=flow_id, flow_index=flow_index, body=body
    )
    return msg
