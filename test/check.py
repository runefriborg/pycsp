import sys
from pycsp_import import *


def print_state(received, poison, retire):
    sys.stdout.write("Received: " + str(received) + "\n")
    if poison:
        sys.stdout.write("Poisoned\n")
    if retire:
        sys.stdout.write("Retired\n")
    sys.stdout.flush()

@process
def Assert(cin, name = "", count = 0, minimum = 0, vocabulary = [], ordered = False, quit_on_count = False, debug = False):
    received = []
    poison = False
    retire = False
    while True:
        try:
            val = cin()
            if debug:
                sys.stdout.write("Debug: "+str(val)+"\n")
                sys.stdout.flush()
            received.append(val)
        except ChannelPoisonException, e:
            poison = True
            break                
        except ChannelRetireException:
            retire = True
            break
        
        if quit_on_count and len(received) == count:
            break
        
    error = ""

    if (len(received) < minimum):
        error += "Wrong number of values: "+str(len(received))+"\n"
        error += "Expected the minimum number of values: "+str(minimum)+"\n"
        
    if count:
        if minimum:
            if (len(received) > count):
                error += "Wrong number of values: "+str(len(received))+"\n"
                error += "Expected a maximum number of values: "+str(count)+"\n"
        else:
            if not (len(received) == count):
                error += "Wrong number of values: "+str(len(received))+"\n"
                error += "Expected number of values: "+str(count)+"\n"
            

    if vocabulary:
        for i in range(len(received)):
            if received[i] not in vocabulary:
                error += "Value "+ str(received[i]) + " not in vocabulary\n"

        if (ordered):
            for i in range(len(received)):
                if received[i] != vocabulary[i % len(vocabulary)]:
                    error += "Value "+ str(received[i]) + " != " + str(vocabulary[i % len(vocabulary)])+" in vocabulary\n"

    if error:
        sys.stdout.write(name+"\n")
        sys.stdout.write(error)
        print_state(received, poison, retire)
    else:
        sys.stdout.write("OK - "+ name+ "\n")

