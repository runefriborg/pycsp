#define CHANNELS 2
#define PROCESSES 3

#include "basic.p"

proctype ALTRW() {
	DECLARE_LOCAL_VARS
	byte result_chan, result_msg;
	alt(0, READ, NULL, 1, WRITE, 42, result_chan, result_msg);
	assert( (result_chan == 0 && result_msg == 55) ||
		(result_chan == 1 && result_msg == NULL) );
}

proctype ALTWR() {
	DECLARE_LOCAL_VARS
	byte result_chan, result_msg;
	alt(1, READ, NULL, 0, WRITE, 55, result_chan, result_msg);
	assert( (result_chan == 1 && result_msg == 42) ||
		(result_chan == 0 && result_msg == NULL) );
}


init
{
	run ALTRW();
	run ALTWR();
}
