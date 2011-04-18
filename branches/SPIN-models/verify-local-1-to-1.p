#define PROCESSES 3
#define CHANNELS 1

#include "basic.p"

proctype PR(byte ch_id) {
        DECLARE_LOCAL_VARS
	byte result;
        read(ch_id, result);
	assert(result == 42);
	printf("read %d ok result:%d\n", _pid, result);
}

proctype PW(byte ch_id) {
        DECLARE_LOCAL_VARS
        write(ch_id, 42);
        printf("write %d ok\n", _pid);
}



init
{
	run PW(0);
	run PR(0);
}
