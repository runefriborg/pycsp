import socket
import errno

print errno.ECONNREFUSED

# Create IPv4 TCP socket (TODO: add support for IPv6)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Disable Nagle's algorithem, to enable faster send
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

# Connect

try:
    sock.connect(('',998))
except socket.error, (value,message):
    print value
    print message
