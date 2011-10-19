# Echo server program
import socket

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5) # set backlog to 5.. 


while 1:
    conn, addr = s.accept()
    print 'Connected by', addr
    while 1:
    
        data = conn.recv(1024)
        if not data: break
        if data.strip() == "quit":
            break
        conn.send(data)
    conn.close()
