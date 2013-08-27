"""
The header specification for the message protocol

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import ctypes
from pycsp.parallel.const import *

# Bit patters for selecting types
GUARD_CMD   = 1<<13
PROCESS_CMD = 1<<12
CHANNEL_CMD = 1<<11
HAS_PAYLOAD = 1<<10
REQ_REPLY   = 1<<9
IS_REPLY    = 1<<8
NATFIX      = 1<<7
IGN_UNKNOWN = 1<<6

ERROR_CMD = 0

"""
GUARD_CMD, PROCESS_CMD and CHANNEL_CMD encodes the destination.
HAS_PAYLOAD tells the receiver, that it must read N bytes containing a payload message
REQ_REPLY informs that if the destination is not available, an error must be returned, such that the sender does not deadlock by waiting eternally for a reply
IS_REPLY informs which queue to post the incoming message to.
NATFIX informs that the receiving socket should also be used as a sending socket  
IGN_UNKNOWN informs that it is ok to drop this message, if the destination is not found
"""

#  CMDs for processes
LOCKTHREAD_ACQUIRE_LOCK   =  0 | PROCESS_CMD | REQ_REPLY
LOCKTHREAD_ACCEPT_LOCK    =  1 | CHANNEL_CMD | GUARD_CMD | IS_REPLY
LOCKTHREAD_UNAVAILABLE    =  2 | CHANNEL_CMD | GUARD_CMD | IS_REPLY 

LOCKTHREAD_NOTIFY_SUCCESS =  3 | PROCESS_CMD | IS_REPLY | HAS_PAYLOAD 
LOCKTHREAD_POISON         =  4 | PROCESS_CMD | IS_REPLY
LOCKTHREAD_RETIRE         =  5 | PROCESS_CMD | IS_REPLY
LOCKTHREAD_RELEASE_LOCK   =  6 | PROCESS_CMD | IS_REPLY | IGN_UNKNOWN
LOCKTHREAD_CHAN_MOVED     =  7 | PROCESS_CMD | IS_REPLY | HAS_PAYLOAD

LOCKTHREAD_QUIT           =  8 | PROCESS_CMD
LOCKTHREAD_ACK            =  9 | PROCESS_CMD
SOCKETTHREAD_SHUTDOWN     = 10 | PROCESS_CMD | CHANNEL_CMD
SOCKETTHREAD_PING         = 11 | PROCESS_CMD | CHANNEL_CMD

# CMDs for channels
CHANTHREAD_JOIN_READER    = 12 | CHANNEL_CMD
CHANTHREAD_JOIN_WRITER    = 13 | CHANNEL_CMD
CHANTHREAD_RETIRE_READER  = 14 | CHANNEL_CMD
CHANTHREAD_RETIRE_WRITER  = 15 | CHANNEL_CMD
CHANTHREAD_POISON_READER  = 16 | CHANNEL_CMD
CHANTHREAD_POISON_WRITER  = 17 | CHANNEL_CMD
CHANTHREAD_REGISTER       = 18 | CHANNEL_CMD
CHANTHREAD_DEREGISTER     = 19 | CHANNEL_CMD
CHANTHREAD_MOVE           = 20 | CHANNEL_CMD
CHANTHREAD_POST_READ      = 21 | CHANNEL_CMD
CHANTHREAD_POST_WRITE     = 22 | CHANNEL_CMD | HAS_PAYLOAD
CHANTHREAD_POST_ACK_READ  = 23 | CHANNEL_CMD
CHANTHREAD_POST_ACK_WRITE = 24 | CHANNEL_CMD | HAS_PAYLOAD
CHANTHREAD_ENTER          = 25 | CHANNEL_CMD | NATFIX
CHANTHREAD_LEAVE          = 26 | CHANNEL_CMD


def cmd2str(cmd):
    """
    Translate command IDs to their string representation
    
    Use for debugging and error messages
    """
    D = {
        ERROR_CMD:"ERROR_CMD",
        LOCKTHREAD_ACQUIRE_LOCK  :"LOCKTHREAD_ACQUIRE_LOCK",
        LOCKTHREAD_ACCEPT_LOCK   :"LOCKTHREAD_ACCEPT_LOCK",
        LOCKTHREAD_UNAVAILABLE   :"LOCKTHREAD_UNAVAILABLE",
        LOCKTHREAD_NOTIFY_SUCCESS:"LOCKTHREAD_NOTIFY_SUCCESS",
        LOCKTHREAD_POISON        :"LOCKTHREAD_POISON",
        LOCKTHREAD_RETIRE        :"LOCKTHREAD_RETIRE",
        LOCKTHREAD_CHAN_MOVED    :"LOCKTHREAD_CHAN_MOVED",
        LOCKTHREAD_RELEASE_LOCK  :"LOCKTHREAD_RELEASE_LOCK",
        LOCKTHREAD_QUIT          :"LOCKTHREAD_QUIT ",
        SOCKETTHREAD_SHUTDOWN    :"SOCKETTHREAD_SHUTDOWN",
        CHANTHREAD_JOIN_READER   :"CHANTHREAD_JOIN_READER",
        CHANTHREAD_JOIN_WRITER   :"CHANTHREAD_JOIN_WRITER",
        CHANTHREAD_RETIRE_READER :"CHANTHREAD_RETIRE_READER",
        CHANTHREAD_RETIRE_WRITER :"CHANTHREAD_RETIRE_WRITER",
        CHANTHREAD_POISON_READER :"CHANTHREAD_POISON_READER",
        CHANTHREAD_POISON_WRITER :"CHANTHREAD_POISON_WRITER",
        CHANTHREAD_REGISTER      :"CHANTHREAD_REGISTER",
        CHANTHREAD_DEREGISTER    :"CHANTHREAD_DEREGISTER",        
        CHANTHREAD_MOVE          :"CHANTHREAD_MOVE",
        CHANTHREAD_POST_READ     :"CHANTHREAD_POST_READ",
        CHANTHREAD_POST_WRITE    :"CHANTHREAD_POST_WRITE",
        CHANTHREAD_POST_ACK_READ :"CHANTHREAD_POST_ACK_READ",
        CHANTHREAD_POST_ACK_WRITE:"CHANTHREAD_POST_ACK_WRITE",
        CHANTHREAD_ENTER         :"CHANTHREAD_ENTER",
        CHANTHREAD_LEAVE         :"CHANTHREAD_LEAVE"
        }

    return D[cmd]


class Header(ctypes.Structure):
    """
    cmd          : type of package
    id           : string, uuid1 in bytes format
    seq_number   : sequence number used for ignoring channel requests, that was left behind.
    arg          : contains the payload size following this header
    _source_host,_source_port,_source_id enables the receiver to reply to a message
    _result_id   : updated with the chosen channel in an offer and match
    """
    _fields_ = [
        ("cmd", ctypes.c_short),
        ("id", ctypes.c_char * 64),
        ("seq_number", ctypes.c_long),
        ("arg", ctypes.c_long),
        ("_source_host", ctypes.c_char * 16),
        ("_source_port", ctypes.c_int),
        ("_source_id", ctypes.c_char * 64),
        ("_result_id", ctypes.c_char * 64)
        ]

HEADERLEN = ctypes.sizeof(Header)
