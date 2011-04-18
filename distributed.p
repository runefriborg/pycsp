#define LEN PROCESSES
#define READ 1
#define WRITE 2
#define NULL 255

#define DECLARE_LOCAL_CHANNEL_VARS \
	byte w_pid, r_pid; \
	byte w,r; \
	byte i; \
	byte cmd; \
	byte id; \
	byte msg; \
	byte w_state, r_state;

#define DECLARE_LOCAL_PROCESS_VARS

typedef processtype {
	byte state;
	bit lock;
	bit waitX;
	byte waiting_removes;
	byte result_ch;
	byte result_msg;
};

processtype proc[PROCESSES];

mtype = {READY, SUCCESS, FAIL};

chan proc_cmd_chan[PROCESSES] = [10] of {byte, byte, byte} /* command, ch_id, msg */
chan proc_acquire_lock_chan[PROCESSES] = [10] of {byte} /* ch_id */
chan proc_release_lock_chan[PROCESSES] = [10] of {byte, byte, byte} /* ch_id */
chan ch_cmd_chan[CHANNELS] = [10] of {byte, byte, byte}; /* command, process_id, msg */
chan ch_accept_lock_chan[CHANNELS] = [10] of {byte, byte}; /* pid, proc_state */

/* commands */
#define POST_WRITE 1
#define POST_READ 2
#define REMOVE_WRITE 3
#define REMOVE_READ 4
#define ACCEPT_LOCK 6
#define RELEASE_LOCK 7
#define NOTIFY_SUCCESS 8
#define REMOVE_ACK 9


typedef requesttype {
	byte id;
	byte msg;
};

typedef chtype {
	requesttype rqueue[LEN];
	byte rlen;
	requesttype wqueue[LEN];
	byte wlen;
	bit lock;
};

chtype ch[CHANNELS];

inline acquire(lock_id) {
	atomic {
		(proc[lock_id].lock == 0);
		proc[lock_id].lock = 1;
	}
}

inline release(lock_id) {
	proc[lock_id].lock = 0;
}

inline wait(lock_id) {
	printf("Process %d waiting\n", _pid);
	assert(proc[lock_id].lock == 1); /* only call wait when lock is required. */
	atomic {
		proc[lock_id].lock = 0; /* release(lock_id); */
		proc[lock_id].waitX = 0;
	}
		(proc[lock_id].waitX == 1);
	atomic {
		(proc[lock_id].lock == 0); /* reacquire(lock_id); */
		proc[lock_id].lock = 1;
		
	}
	printf("Process %d running\n", _pid);
}

inline notify(lock_id) {
	proc[lock_id].waitX = 1;
}


proctype lockP(byte id) {
	byte ch_id, cmd, msg;
	byte ch_id2;
	bit locked;

	printf("Lock process %d started for pid:%d\n", _pid, id);
	/* Create a queuing system using channels */
	do
	:: proc_acquire_lock_chan[id]?ch_id ->
		ch_accept_lock_chan[ch_id]!id, proc[id].state;
		locked = 1;
		do
		:: proc_release_lock_chan[id]?cmd, ch_id2, msg; -> /* process locked! */
			if
			:: cmd == RELEASE_LOCK ->
				assert(ch_id == ch_id2);
				break;
			:: cmd == NOTIFY_SUCCESS ->
				assert(ch_id == ch_id2);
				acquire(id);
				proc[id].state = SUCCESS;
				proc[id].result_ch = ch_id2;
				proc[id].result_msg = msg;
				notify(id);
				release(id);
			:: else -> assert(false);
			fi;
		od;
		locked = 0;
	:: proc_cmd_chan[id]?cmd, ch_id, msg ->
		if
		:: cmd == REMOVE_ACK ->
			proc[id].waiting_removes--;
		:: else -> assert(cmd == REMOVE_ACK);
		fi;
	:: timeout ->
		assert(locked == 0);
		assert(proc[id].waiting_removes == 0);
		printf("lockP(%d) done", id);
		break;
	od;
}

inline remote_acquire(ch_id, lock_pid, get_state) {
	proc_acquire_lock_chan[lock_pid]!ch_id;
	ch_accept_lock_chan[ch_id]?id, get_state;
	assert(lock_pid == id);
}

inline remote_release(ch_id, lock_pid) {
	proc_release_lock_chan[lock_pid]!RELEASE_LOCK, ch_id, NULL;
}


inline post_read(ch_id) {
	printf("Process %d posting read to %d\n", _pid, ch_id);
	ch_cmd_chan[ch_id]!POST_READ, _pid, NULL;
}

inline remove_read(ch_id) {
	ch_cmd_chan[ch_id]!REMOVE_READ, _pid, NULL;
}

inline post_write(ch_id, msg) {
	printf("Process %d posting write to %d\n", _pid, ch_id);
	ch_cmd_chan[ch_id]!POST_WRITE, _pid, msg;
}

inline remove_write(ch_id) {
	ch_cmd_chan[ch_id]!REMOVE_WRITE, _pid, NULL;
}

inline read(ch_id, result) {
	proc[_pid].waiting_removes == 0;
	proc[_pid].state = READY;

	post_read(ch_id);
	/* if no success, then wait for success */
	acquire(_pid);
	if
		:: (proc[_pid].state == READY) -> wait(_pid);
		:: else skip;
	fi;
	release(_pid);
	assert(proc[_pid].state == SUCCESS);

	proc[_pid].waiting_removes = 1;
	remove_read(ch_id);
		
	result = proc[_pid].result_msg;
}

inline write(ch_id, msg) {
	proc[_pid].waiting_removes == 0;
	proc[_pid].state = READY;

	post_write(ch_id, msg);
	/* if no success, then wait for success */
	acquire(_pid);
	if
		:: (proc[_pid].state == READY) -> wait(_pid);
		:: else skip;
	fi;
	release(_pid);
	assert(proc[_pid].state == SUCCESS);

	proc[_pid].waiting_removes = 1;
	remove_write(ch_id);
}

/* Two guards are enough to perform an exhaustive verification */
inline alt(ch_id1, op1, msg1, ch_id2, op2, msg2, result_chan, result) {
	proc[_pid].waiting_removes == 0;
	proc[_pid].state = READY;

	if
	:: (op1 == READ) -> 	post_read(ch_id1);
	:: else 		post_write(ch_id1, msg1);
	fi;
	if
	:: (op2 == READ) -> 	post_read(ch_id2);
	:: else 		post_write(ch_id2, msg2);
	fi;
	/* if no success, then wait for success */
	acquire(_pid);
	if
		:: (proc[_pid].state == READY) -> wait(_pid);
		:: else skip;
	fi;
	release(_pid);
	assert(proc[_pid].state == SUCCESS);

	proc[_pid].waiting_removes = 2;
	if
	:: (op1 == READ) -> 	remove_read(ch_id1);
	:: else 		remove_write(ch_id1);
	fi;
	if
	:: (op2 == READ) -> 	remove_read(ch_id2);
	:: else 		remove_write(ch_id2);
	fi;
	result_chan = proc[_pid].result_ch;
	result = proc[_pid].result_msg;
}

inline match(ch_id) {
	w = 0;
	r = 0;
	printf("Channel: %d Matching R:%d procs to W:%d procs\n",ch_id, ch[ch_id].rlen,ch[ch_id].wlen);
	do
	:: (r<ch[ch_id].rlen) ->
		w = 0;
		do
		:: (w<ch[ch_id].wlen) ->
			offer(ch_id, r, w);
			w = w+1;
		:: else break;
		od;
		r = r+1;
	:: else break;	
	od;
}

inline offer(ch_id, r, w) {
	r_pid = ch[ch_id].rqueue[r].id;
	w_pid = ch[ch_id].wqueue[w].id;

	if
	:: (r_pid < w_pid) ->
		remote_acquire(ch_id, r_pid, r_state);		
		remote_acquire(ch_id, w_pid, w_state);
	:: else skip ->
		remote_acquire(ch_id, w_pid, w_state);
		remote_acquire(ch_id, r_pid, r_state);
	fi;
	printf("Offer for R:%d and W:%d\n", r_pid, w_pid);
	if
	:: (r_state == READY && w_state == READY) ->
		printf("Success for R:%d and W:%d\n", r_pid, w_pid);	
		proc_release_lock_chan[r_pid]!NOTIFY_SUCCESS, ch_id, ch[ch_id].wqueue[w].msg;
		proc_release_lock_chan[w_pid]!NOTIFY_SUCCESS, ch_id, NULL;

		r = LEN; /* break match loop */
		w = LEN;
	:: else skip;
	fi;
	if
	:: (r_pid < w_pid) ->
		remote_release(ch_id, w_pid);
		remote_release(ch_id, r_pid);
	:: else skip ->
		remote_release(ch_id, r_pid);
		remote_release(ch_id, w_pid);
	fi;
}


proctype channel_home(byte ch_id) {
	DECLARE_LOCAL_CHANNEL_VARS

	do
	:: ch_cmd_chan[ch_id]?cmd, id, msg ->
		if
		:: cmd == POST_WRITE ->
			ch[ch_id].wqueue[ch[ch_id].wlen].id = id;
			ch[ch_id].wqueue[ch[ch_id].wlen].msg = msg;
			ch[ch_id].wlen++;
			match(ch_id);
		:: cmd == POST_READ ->
			ch[ch_id].rqueue[ch[ch_id].rlen].id = id;
			ch[ch_id].rqueue[ch[ch_id].rlen].msg = NULL;
			ch[ch_id].rlen++;
			match(ch_id);
		:: cmd == REMOVE_WRITE ->
			i = 0;
			do
			:: (i < ch[ch_id].wlen) ->
				if 
				:: (ch[ch_id].wqueue[i].id == id) ->
					proc_cmd_chan[id]!REMOVE_ACK, ch_id, NULL;

					ch[ch_id].wlen--;
					ch[ch_id].wqueue[i].id = ch[ch_id].wqueue[ch[ch_id].wlen].id;
					ch[ch_id].wqueue[i].msg = ch[ch_id].wqueue[ch[ch_id].wlen].msg;
				:: else skip;
				fi;
				i++;
			:: else break;
			od;
		:: cmd == REMOVE_READ ->
			i = 0;
			do
			:: (i < ch[ch_id].rlen) ->
				if 
				:: (ch[ch_id].rqueue[i].id == id) ->
					proc_cmd_chan[id]!REMOVE_ACK, ch_id, NULL;

					ch[ch_id].rlen--;
					ch[ch_id].rqueue[i].id = ch[ch_id].rqueue[ch[ch_id].rlen].id;
					ch[ch_id].rqueue[i].msg = ch[ch_id].rqueue[ch[ch_id].rlen].msg;
				:: else skip;
				fi;
				i++;
			:: else break;
			od;
		fi;
	:: timeout ->
		assert(ch[ch_id].rlen == 0 && ch[ch_id].wlen == 0);
		printf("Channel home %d quit\n", ch_id);
		break;
	od;
}
