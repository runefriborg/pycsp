"""
Configuration examples
"""

from MultipleTokenRing import *

if version[3] == 'processes':
    # Configurating PyCSP processes for minimum memory usage.
    c = Configuration()
    c.set(PROCESSES_SHARED_CONDITIONS, 1)
    c.set(PROCESSES_SHARED_LOCKS, 1)

    c.set(PROCESSES_ALLOC_MSG_BUFFER, 16384)
    c.set(PROCESSES_MSG_BUFFER_BLOCKSIZE, 16)

    c.set(PROCESSES_ALLOC_QUEUE_PER_CHANNEL, 100)
    c.set(PROCESSES_ALLOC_CHANNELS, 200)
    c.set(PROCESSES_ALLOC_CHANNELENDS, 400)

elif version[3] == 'net':
    # Configurating network server id, if several PyCSP net
    # applications are sharing the same Pyro nameserver.
    Configuration().set(NET_SERVER_ID, 101)

if __name__ == "__main__":
    ring(sys.argv[2:])





