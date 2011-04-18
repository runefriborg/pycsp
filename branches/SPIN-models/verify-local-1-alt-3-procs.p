#define PROCESSES 4
#define CHANNELS 2

#include "basic.p"

proctype PR(byte ch_id) {
        DECLARE_LOCAL_VARS
	byte result;
	read(ch_id, result);
	assert(result == 109 || result == 221);
	printf("read %d ok result:%d\n", _pid, result);
}

proctype PW(byte ch_id) {
        DECLARE_LOCAL_VARS
 	write(ch_id, 42);
	printf("write %d ok\n", _pid);
}

proctype ALT() {
	DECLARE_LOCAL_VARS
	byte result_chan, result_msg;
	alt(0, READ, NULL, 1, WRITE, 109, result_chan, result_msg);
	assert(	(result_chan == 0 && result_msg == 42) ||
		(result_chan == 1 && result_msg == NULL));

	alt(0, READ, NULL, 1, WRITE, 221, result_chan, result_msg);
	assert(	(result_chan == 0 && result_msg == 42) ||
		(result_chan == 1 && result_msg == NULL));
}

init
{
	run ALT();
	run PW(0);
	run PR(1);
}
