#define LEN PROCESSES
#define READ 1
#define WRITE 2

#define DECLARE_LOCAL_VARS \
	byte r_pid, w_pid; \
	byte i; \
	byte w,r; \
	byte SL;

mtype = {READY, SUCCESS, SYNC, FAIL};

mtype proc_state[PROCESSES];
bit proc_lock[PROCESSES];
bit proc_wait[PROCESSES];
byte proc_sync_level[PROCESSES];

typedef chdef {
	byte rqueue[LEN];
	byte rlen;
	byte wqueue[LEN];
	byte wlen;
	bit lock;
};

/* To verify the transition between synchronization mechanisms, we set up two levels */
#define LEVELS 2
typedef chlvldef {
	byte sync_level;
	chdef lvl[LEVELS];
}

chlvldef ch[CHANNELS];

inline acquire(lock_id) {
        atomic {
                (proc_lock[lock_id] == 0);
                proc_lock[lock_id] = 1;
        }
}

inline release(lock_id) {
        proc_lock[lock_id] = 0;
}

inline wait(lock_id) {
        printf("Process %d waiting\n", _pid);
        assert(proc_lock[lock_id] == 1); /* only call wait when lock is required. */
        atomic {
                proc_lock[lock_id] = 0; /* release(lock_id); */
                proc_wait[lock_id] = 0;
        }
                (proc_wait[lock_id] == 1);
        atomic {
                (proc_lock[lock_id] == 0); /* reacquire(lock_id); */
                proc_lock[lock_id] = 1;

        }
        printf("Process %d running\n", _pid);
}

inline notify(lock_id) {
        proc_wait[lock_id] = 1;
}

inline match(ch_id, SL) {
	w = 0;
	r = 0;
	printf("Matching R:%d procs to W:%d procs at level %d\n",ch[ch_id].lvl[SL].rlen,ch[ch_id].lvl[SL].wlen, SL);
	do
	:: (r<ch[ch_id].lvl[SL].rlen) ->
		w = 0;
		do
		:: (w<ch[ch_id].lvl[SL].wlen) ->
			offer(ch_id, r, w, SL);
			w = w+1;
		:: else break;
		od;
		r = r+1;
	:: else break;	
	od;
	printf("debug: R:%d, W:%d\n", ch[ch_id].lvl[SL].rlen,ch[ch_id].lvl[SL].wlen);
}

inline offer(ch_id, r, w, SL) {
	r_pid = ch[ch_id].lvl[SL].rqueue[r];
	w_pid = ch[ch_id].lvl[SL].wqueue[w];
	printf("Try Offer for R:%d and W:%d at level %d\n", r_pid, w_pid, SL);
	if
	:: (r_pid < w_pid) ->
		acquire(r_pid);
		acquire(w_pid);
	:: else skip ->
		acquire(w_pid);
		acquire(r_pid);
	fi;
	printf("Offer for R:%d and W:%d at level %d\n", r_pid, w_pid, SL);
	if
	:: (proc_state[r_pid] == READY && proc_state[w_pid] == READY) ->
		printf("SUCCESS for R:%d and W:%d at level %d\n", r_pid, w_pid, SL);
		proc_state[r_pid] = SUCCESS;
		proc_state[w_pid] = SUCCESS;
		/* Transfer of message. Removed for clarity.
		In regular programming languages it is trivial to
		add the message buffer to posted channel requests.
		Example: r.msg = w.msg */

		notify(r_pid);
		notify(w_pid);
		r = LEN; /* break match loop */
		w = LEN;
	:: else skip;
	fi;
	if
	:: (r_pid < w_pid) ->
		release(w_pid);
		release(r_pid);
	:: else skip ->
		release(r_pid);
		release(w_pid);
	fi;
}

inline post_read(ch_id) {
	SL = ch[ch_id].sync_level;
	proc_sync_level[_pid] = SL;

	atomic { (ch[ch_id].lvl[SL].lock == 0) -> ch[ch_id].lvl[SL].lock = 1; } /* acquire */
	ch[ch_id].lvl[SL].rqueue[ch[ch_id].lvl[SL].rlen] = _pid;
	ch[ch_id].lvl[SL].rlen++;
	match(ch_id, SL);
	ch[ch_id].lvl[SL].lock = 0; /* release */
	printf("Posted read at level %d\n", SL);
	
}

inline remove_read(ch_id) {
	SL = proc_sync_level[_pid];
	atomic { (ch[ch_id].lvl[SL].lock == 0) -> ch[ch_id].lvl[SL].lock = 1; } /* acquire */
	i = 0;
	do
	:: (i < ch[ch_id].lvl[SL].rlen) ->
		if 
		::	(ch[ch_id].lvl[SL].rqueue[i] == _pid) ->
				ch[ch_id].lvl[SL].rlen--;
				ch[ch_id].lvl[SL].rqueue[i] = ch[ch_id].lvl[SL].rqueue[ch[ch_id].lvl[SL].rlen];
		:: 	else skip;
		fi;
		i++;
	:: else break;
	od;
	ch[ch_id].lvl[SL].lock = 0; /* release */
}

inline post_write(ch_id) {	
	SL = ch[ch_id].sync_level;
	proc_sync_level[_pid] = SL;

	atomic { (ch[ch_id].lvl[SL].lock == 0) -> ch[ch_id].lvl[SL].lock = 1; } /* acquire */
	ch[ch_id].lvl[SL].wqueue[ch[ch_id].lvl[SL].wlen] = _pid;
	ch[ch_id].lvl[SL].wlen++;
	match(ch_id, SL);
	ch[ch_id].lvl[SL].lock = 0; /* release */
	printf("Posted write at level %d\n", SL);
}

inline remove_write(ch_id) {
	SL = proc_sync_level[_pid];
	atomic { (ch[ch_id].lvl[SL].lock == 0) -> ch[ch_id].lvl[SL].lock = 1; } /* acquire */
	i = 0;
	do
	:: (i < ch[ch_id].lvl[SL].wlen) ->
		if 
		::	(ch[ch_id].lvl[SL].wqueue[i] == _pid) ->
				ch[ch_id].lvl[SL].wlen--;
				ch[ch_id].lvl[SL].wqueue[i] = ch[ch_id].lvl[SL].wqueue[ch[ch_id].lvl[SL].wlen];
		::	else skip;
		fi;
		i++;
	:: else break;
	od;
	ch[ch_id].lvl[SL].lock = 0; /* release */
}

/* Illegal to make concurrent calls to switch_sync_level.*/

inline switch_sync_level(ch_id, to_level) {
	byte SL;
	byte r,w,r_pid, w_pid;
	SL = ch[ch_id].sync_level;
	atomic { (ch[ch_id].lvl[SL].lock == 0) -> ch[ch_id].lvl[SL].lock = 1; } /* acquire */	
	ch[ch_id].sync_level = to_level;	

	/* Notify connected processes */
	r = 0;
	do
	:: (r<ch[ch_id].lvl[SL].rlen) ->
		r_pid = ch[ch_id].lvl[SL].rqueue[r];
		acquire(r_pid);
		if
		:: proc_state[r_pid] == READY ->
			printf("NOTIFY READ %d\n", r_pid);
			notify(r_pid); /* Notify process to transcend to new sync level */
		:: else -> skip;
		fi;
		release(r_pid);
		r = r+1;
	:: else break;	
	od;
	w = 0;
	do
	:: (w<ch[ch_id].lvl[SL].wlen) ->
		w_pid = ch[ch_id].lvl[SL].wqueue[w];
		acquire(w_pid);
		if
		:: proc_state[w_pid] == READY ->
			printf("NOTIFY WRITE %d\n", w_pid);
			notify(w_pid); /* Notify process to transcend to new sync level */
		:: else -> skip;
		fi;
		release(w_pid);
		w = w+1;
	:: else break;
	od;

	ch[ch_id].lvl[SL].lock = 0; /* release */
}



inline transcend_read(ch_id) {
	proc_state[_pid] = SYNC;
	release(_pid);
	remove_read(ch_id);	
	proc_state[_pid] = READY;
	post_read(ch_id);
	acquire(_pid);
}


inline transcend_write(ch_id) {
	proc_state[_pid] = SYNC;
	release(_pid);
	remove_write(ch_id);	
	proc_state[_pid] = READY;
	post_write(ch_id);
	acquire(_pid);
}


inline enter_read(ch_id) {
	proc_state[_pid] = READY;
	post_read(ch_id);
}

inline wait_read(ch_id) {
	/* if no success, then wait for success */
	acquire(_pid);
	do
	:: (proc_sync_level[_pid] == ch[ch_id].sync_level) && (proc_state[_pid] == READY) ->
		wait(_pid);
	:: (proc_sync_level[_pid] != ch[ch_id].sync_level) && (proc_state[_pid] == READY) ->
		transcend_read(ch_id);
	:: else break;
	od;
	release(_pid);
}

inline leave_read(ch_id){ 
	assert(proc_state[_pid] == SUCCESS);
	remove_read(ch_id);
}

inline enter_write(ch_id) {
	proc_state[_pid] = READY;
	post_write(ch_id);
}

inline wait_write(ch_id) {
	/* if no success, then wait for success */
	acquire(_pid);
	do
	:: (proc_sync_level[_pid] == ch[ch_id].sync_level) && (proc_state[_pid] == READY) ->
		wait(_pid);
	:: (proc_sync_level[_pid] != ch[ch_id].sync_level) && (proc_state[_pid] == READY) ->
		transcend_write(ch_id);
	:: else break;
	od;
	release(_pid);
}

inline leave_write(ch_id) {
	assert(proc_state[_pid] == SUCCESS);
	remove_write(ch_id);
}

inline read(ch_id) {
	enter_read(ch_id);
	wait_read(ch_id);
	leave_read(ch_id);
}

inline write(ch_id) {
	enter_write(ch_id);
	wait_write(ch_id);
	leave_write(ch_id);
}
