class ChannelHome(object):
    """
    Singleton
    """
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)
            
            cls.__instance.chan_home_db = {}
            
        return cls.__instance
    getInstance = classmethod(getInstance)

    def request(self, chan_id):
        if self.chan_home_db.has_key(chan_id):
            return self.chan_home_db[chan_id]
        else:
            return None

    def add(self, chan_id, chan_home):
        self.chan_home_db['chan_id'] = chan_home
