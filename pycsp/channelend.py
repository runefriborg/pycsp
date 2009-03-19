

class ChannelEndException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class ChannelEnd:
    def __init__(self):
        self.channel = None
        self.isretired = False

    def post_write(self, req):
        if self.isretired:
            raise ChannelEndException('Not allowed to write to retired channelend!')
        self.channel.post_write(req)

    def post_read(self, req):
        if self.isretired:
            raise ChannelEndException('Not allowed to read from retired channelend!')
        self.channel.post_read(req)

    def remove_write(self, req):
        self.channel.remove_write(req)

    def remove_read(self, req):
        self.channel.remove_read(req)

    def poison(self):
        self.channel.poison()

    def __repr__(self):
        return "<ChannelEnd wrapping %s>" % self.channel
        

class ChannelEndWrite(ChannelEnd):
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False

    def __call__(self, val):
        if self.isretired:
            raise ChannelEndException('Not allowed to write to retired channelend!')
        self.channel._write(val)

    def retire(self):
        if self.isretired:
            raise ChannelEndException('Cannot retire twice!')
        self.channel.leave(False, True)
        self.isretired = True


class ChannelEndRead(ChannelEnd):
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False

    def __call__(self):
        if self.isretired:
            raise ChannelEndException('Not allowed to read from retired channelend!')
        return self.channel._read()

    def retire(self):
        if self.isretired:
            raise ChannelEndException('Cannot retire twice!')
        self.channel.leave(True, False)
        self.isretired = True


def IN(channel):
    channel.join(True, False)
    return ChannelEndRead(channel)

def OUT(channel):
    channel.join(False, True)
    return ChannelEndWrite(channel)

def retire(*list_of_channelEnds):
    for channelEnd in list_of_channelEnds:
        channelEnd.retire()

def poison(*list_of_channelEnds):
    for channelEnd in list_of_channelEnds:
        channelEnd.poison()



