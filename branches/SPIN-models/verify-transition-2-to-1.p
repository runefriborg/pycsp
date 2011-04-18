#define PROCESSES  5
#define CHANNELS  1

#include "transition.p";

proctype P1() {
	DECLARE_LOCAL_VARS
	read(0);
	read(0);
}

proctype P2() {
	DECLARE_LOCAL_VARS
	write(0);
}

proctype P3() {
	switch_sync_level(0, 1);
}

init {
	ch[0].sync_level = 0;
	run P1();
	run P2();
	run P2();

	run P3();
}
