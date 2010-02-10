from pycsp_import import *

def action(channel_input):
    print channel_input

@process
def read(cin1, cin2):
    while True:
        B = 'Fisk'
        Alternation([{
                    cin1:"print B,'cin1'",
                    cin2:action
                    }]).execute()
                    
        
C = [Channel(), Channel()]
Spawn(read(+C[0], +C[1]))


writeTo = -C[0]

writeTo('Hey')

poison(writeTo)
