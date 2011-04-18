#define PROCESSES 10
#define CHANNELS 2

#include "distributed.p"

proctype PR(byte ch_id) {
	DECLARE_LOCAL_PROCESS_VARS
	byte result;
	read(ch_id, result);
	assert(result == 109 || result == 221);
	printf("read %d ok result:%d\n", _pid, result);
}

proctype PW(byte ch_id) {
	DECLARE_LOCAL_PROCESS_VARS
 	write(ch_id, 42);
	printf("write %d ok\n", _pid);
}


proctype ALT() {
	DECLARE_LOCAL_PROCESS_VARS
	byte result_chan, result_msg;
	alt(0, READ, NULL, 1, WRITE, 109, result_chan, result_msg);
	assert(	(result_chan == 0 && result_msg == 42) ||
		(result_chan == 1 && result_msg == NULL));

	alt(0, READ, NULL, 1, WRITE, 221, result_chan, result_msg);
	assert(	(result_chan == 0 && result_msg == 42) ||
		(result_chan == 1 && result_msg == NULL));
}

init {
	byte p;
	run channel_home(0);
	run channel_home(1);
	p = run ALT(); run lockP(p);
	p = run PW(0); run lockP(p);
	p = run PR(1); run lockP(p);
}
