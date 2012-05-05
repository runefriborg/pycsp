
import ctypes

# Bit patters for selecting types
PROCESS_CMD = 1<<9
CHANNEL_CMD = 1<<8
HAS_PAYLOAD = 1<<7
IS_REPLY    = 1<<6

ERROR_CMD = 0

#  CMDs for processes
LOCKTHREAD_ACQUIRE_LOCK   = PROCESS_CMD | 0
LOCKTHREAD_ACCEPT_LOCK    = CHANNEL_CMD | 1 | IS_REPLY
LOCKTHREAD_NOTIFY_SUCCESS = PROCESS_CMD | 2 | IS_REPLY | HAS_PAYLOAD 
LOCKTHREAD_POISON         = PROCESS_CMD | 3 | IS_REPLY
LOCKTHREAD_RETIRE         = PROCESS_CMD | 4 | IS_REPLY
LOCKTHREAD_RELEASE_LOCK   = PROCESS_CMD | 5 | IS_REPLY
LOCKTHREAD_SHUTDOWN       = PROCESS_CMD | 6

# CMDs for channels
CHANTHREAD_JOIN_READER    = CHANNEL_CMD | 0
CHANTHREAD_JOIN_WRITER    = CHANNEL_CMD | 1
CHANTHREAD_LEAVE_READER   = CHANNEL_CMD | 2
CHANTHREAD_LEAVE_WRITER   = CHANNEL_CMD | 3
CHANTHREAD_RETIRE_READER  = CHANNEL_CMD | 4
CHANTHREAD_RETIRE_WRITER  = CHANNEL_CMD | 5
CHANTHREAD_POISON_READER  = CHANNEL_CMD | 6
CHANTHREAD_POISON_WRITER  = CHANNEL_CMD | 7
CHANTHREAD_REGISTER       = CHANNEL_CMD | 8
CHANTHREAD_DEREGISTER     = CHANNEL_CMD | 9
CHANTHREAD_POST_READ      = CHANNEL_CMD | 10 | HAS_PAYLOAD
CHANTHREAD_POST_WRITE     = CHANNEL_CMD | 11 | HAS_PAYLOAD


class Header(ctypes.Structure):
    """
    cmd : type of package
    id : string, uuid1 in bytes format
    seq_number : sequence number used for ignoring channel requests, that was left behind.
    payload_size : payload size following this header
    """
    _fields_ = [
        ("cmd", ctypes.c_short),
        ("id", ctypes.c_char * 16),
        ("seq_number", ctypes.c_long),
        ("arg", ctypes.c_long),
        ("_source_host", ctypes.c_char * 16),
        ("_source_port", ctypes.c_int),
        ("_source_id", ctypes.c_char * 16)
        ]


