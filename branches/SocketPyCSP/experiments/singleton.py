class LockThreadConnector(object):
    """
    Singleton
    """
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self, process, process_cond):
        pass

    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''

        if len(args) == 3:
            _, process, process_cond = args
        else:
            raise Exception("LockThreadConnector() takes exactly 2 arguments (%d given)" % (len(args)-1))

        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)

            cls.__instance.process = [process]
            cls.__instance.process_cond = [process_cond]
            print args, kwargs

        else:
            cls.__instance.process.append(process)
            cls.__instance.process_cond.append(process_cond)

        return cls.__instance
    getInstance = classmethod(getInstance)


X = LockThreadConnector(1,2)

print X.process_cond


X2 = LockThreadConnector(3,4)

print X.process_cond
