#define PROCESSES 10
#define CHANNELS 1

#include "distributed.p"

proctype PR(byte ch_id) {
	DECLARE_LOCAL_PROCESS_VARS
	byte result;
	read(ch_id, result);
	assert(result > 42 && result < 42+PROCESSES);
	printf("read %d ok result:%d\n", _pid, result);
}

proctype PW(byte ch_id) {
	DECLARE_LOCAL_PROCESS_VARS
 	write(ch_id, 42+_pid);
	printf("write %d ok\n", _pid);
}

init {
	byte p;
	run channel_home(0);
	p = run PW(0); run lockP(p);
	p = run PR(0); run lockP(p);
	p = run PW(0); run lockP(p);
	p = run PR(0); run lockP(p);
}
