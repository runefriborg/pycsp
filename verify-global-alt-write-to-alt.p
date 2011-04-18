#define CHANNELS 2
#define PROCESSES 9

#include "distributed.p"

proctype PW(byte ch_id) {
        DECLARE_LOCAL_PROCESS_VARS
        write(ch_id, 99);
        printf("write %d ok\n", _pid);
}

proctype ALTRW() {
	DECLARE_LOCAL_PROCESS_VARS
	byte result_chan, result_msg;
	alt(0, READ, NULL, 1, WRITE, 42, result_chan, result_msg);
	assert( (result_chan == 0 && result_msg == 55) ||
		(result_chan == 0 && result_msg == 99) ||
		(result_chan == 1 && result_msg == NULL) );
	alt(0, READ, NULL, 1, WRITE, 42, result_chan, result_msg);
	assert( (result_chan == 0 && result_msg == 55) ||
		(result_chan == 0 && result_msg == 99) ||
		(result_chan == 1 && result_msg == NULL) );
}

proctype ALTWR() {
	DECLARE_LOCAL_PROCESS_VARS
	byte result_chan, result_msg;
	alt(1, READ, NULL, 0, WRITE, 55, result_chan, result_msg);
	assert( (result_chan == 1 && result_msg == 42) ||
		(result_chan == 0 && result_msg == NULL) );
}


init
{
	byte p;
	run channel_home(0);
	run channel_home(1);
	p = run PW(0); run lockP(p);
	p = run ALTRW(); run lockP(p);
	p = run ALTWR(); run lockP(p);
}
