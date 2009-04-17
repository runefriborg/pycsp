class ChannelEndException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class ChannelEndWrite():
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False

        self.__call__ = self.channel._write
        self.post_write = self.channel.post_write

        self.remove_write = self.channel.remove_write
        self.poison = self.channel.poison

    def _retire(self):
        raise ChannelEndException('Not allowed to write to retired channelend!')

    def retire(self):
        if self.isretired:
            raise ChannelEndException('Cannot retire twice!')
        self.channel.leave_writer()
        self.__call__ = self._retire
        self.post_write = self._retire
        self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndWrite wrapping %s>" % self.channel
        else:
            return "<ChannelEndWrite wrapping %s named %s>" % (self.channel, self.channel.name)


class ChannelEndRead():
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False

        self.__call__ = self.channel._read
        self.post_read = self.channel.post_read

        self.remove_read = self.channel.remove_read
        self.poison = self.channel.poison

    def _retire(self):
        raise ChannelEndException('Not allowed to read from retired channelend!')

    def retire(self):
        if self.isretired:
            raise ChannelEndException('Cannot retire twice!')
        self.channel.leave_reader()
        self.__call__ = self._retire
        self.post_read = self._retire
        self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndRead wrapping %s>" % self.channel
        else:
            return "<ChannelEndRead wrapping %s named %s>" % (self.channel, self.channel.name)


def IN(channel):
    channel.join_reader()
    return ChannelEndRead(channel)

def OUT(channel):
    channel.join_writer()
    return ChannelEndWrite(channel)

def retire(*list_of_channelEnds):
    for channelEnd in list_of_channelEnds:
        channelEnd.retire()

def poison(*list_of_channelEnds):
    for channelEnd in list_of_channelEnds:
        channelEnd.poison()



