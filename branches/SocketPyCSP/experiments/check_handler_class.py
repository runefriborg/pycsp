import SocketServer

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def setup(self):
        self.state = []

    def handle(self):
        print "Welcome"
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        self.state.append(self.data)
        print "%s wrote:" % self.client_address[0]
        print self.state
        # just send back the same data, but upper-cased
        self.request.send(self.data.upper())

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    # Create the server, binding to localhost on port 0
    server = SocketServer.TCPServer((HOST, 0), MyTCPHandler)

    print 'Server running at port:', server.server_address[1]

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


