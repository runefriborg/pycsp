import ctypes


class Package(ctypes.Structure):
    """
    cmd : type of package
    id : string, uuid1 in bytes format
    payload_size : payload size following this header
    seq_number : sequence number used for ignoring channel requests, that was left behind.
    """
    _fields_ = [
        ("cmd", ctypes.c_int),
        ("id", ctypes.c_char * 10),
        ("payload_size", ctypes.c_long),
        ("seq_number", ctypes.c_long)
        ]


p = Package(1, "Fisk", 0, 1)

g = open("foo","wb")
g.write(p)
