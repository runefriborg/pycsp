#define LEN PROCESSES
#define READ 1
#define WRITE 2
#define NULL 255

#define DECLARE_LOCAL_VARS \
	byte r_pid, w_pid; \
	byte i; \
	byte w,r;


mtype = {READY, SUCCESS, FAIL};

typedef processtype {
	mtype state;
	bit lock;
	bit waitX;
	byte result_ch;
};

processtype proc[PROCESSES];

typedef requesttype {
	byte id;
	byte msg;
};

typedef chdef {
	requesttype rqueue[LEN];
	byte rlen;
	requesttype wqueue[LEN];
	byte wlen;
	bit lock;
};

chdef ch[CHANNELS];

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

inline match(ch_id) {
	w = 0;
	r = 0;
	printf("Matching R:%d procs to W:%d procs\n",ch[ch_id].rlen,ch[ch_id].wlen);
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
	printf("debug: R:%d, W:%d\n", ch[ch_id].rlen,ch[ch_id].wlen);
}

inline offer(ch_id, r, w) {
	r_pid = ch[ch_id].rqueue[r].id;
	w_pid = ch[ch_id].wqueue[w].id;
	if
	:: (r_pid < w_pid) ->
		acquire(r_pid);
		acquire(w_pid);
	:: else skip ->
		acquire(w_pid);
		acquire(r_pid);
	fi;
	printf("Offer for R:%d and W:%d\n", r_pid, w_pid);
	if
	:: (proc[r_pid].state == READY && proc[w_pid].state == READY) ->
		printf("Success for R:%d and W:%d\n", r_pid, w_pid);
		proc[r_pid].state = SUCCESS;
		proc[w_pid].state = SUCCESS;

		/* Transfer of message. */
		ch[ch_id].rqueue[r].msg = ch[ch_id].wqueue[w].msg;
		ch[ch_id].wqueue[w].msg = NULL;
		proc[r_pid].result_ch = ch_id;
		proc[w_pid].result_ch = ch_id;

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
	atomic { (ch[ch_id].lock == 0) -> ch[ch_id].lock = 1; } /* acquire */
	ch[ch_id].rqueue[ch[ch_id].rlen].id = _pid;
	ch[ch_id].rqueue[ch[ch_id].rlen].msg = NULL;
	ch[ch_id].rlen++;
	match(ch_id);
	ch[ch_id].lock = 0; /* release */
	printf("Posted read\n");
	
}

inline remove_read(ch_id, result) {
	atomic { (ch[ch_id].lock == 0) -> ch[ch_id].lock = 1; } /* acquire */
	i = 0;
	do
	:: (i < ch[ch_id].rlen) ->
		if 
		::	(ch[ch_id].rqueue[i].id == _pid) ->									if /* Retrieve result */
				:: (proc[_pid].result_ch == ch_id) ->
					result = ch[ch_id].rqueue[i].msg;
				:: else skip;
				fi;
				ch[ch_id].rlen--;
				ch[ch_id].rqueue[i].id = ch[ch_id].rqueue[ch[ch_id].rlen].id;
				ch[ch_id].rqueue[i].msg = ch[ch_id].rqueue[ch[ch_id].rlen].msg;
		:: 	else skip;
		fi;
		i++;
	:: else break;
	od;
	ch[ch_id].lock = 0; /* release */
}

inline post_write(ch_id, msg_to_write) {
	atomic { (ch[ch_id].lock == 0) -> ch[ch_id].lock = 1; } /* acquire */
	ch[ch_id].wqueue[ch[ch_id].wlen].id = _pid;
	ch[ch_id].wqueue[ch[ch_id].wlen].msg = msg_to_write;
	ch[ch_id].wlen++;
	match(ch_id);
	ch[ch_id].lock = 0; /* release */
	printf("Posted write\n");
}

inline remove_write(ch_id) {
	atomic { (ch[ch_id].lock == 0) -> ch[ch_id].lock = 1; } /* acquire */
	i = 0;
	do
	:: (i < ch[ch_id].wlen) ->
		if 
		::	(ch[ch_id].wqueue[i].id == _pid) ->
				ch[ch_id].wlen--;
				ch[ch_id].wqueue[i].id = ch[ch_id].wqueue[ch[ch_id].wlen].id;
				ch[ch_id].wqueue[i].msg = ch[ch_id].wqueue[ch[ch_id].wlen].msg;
		::	else skip;
		fi;
		i++;
	:: else break;
	od;
	ch[ch_id].lock = 0; /* release */
}

inline read(ch_id, result) {
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
	remove_read(ch_id, result);
}

inline write(ch_id, msg) {
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
	remove_write(ch_id)
}


inline alt(ch_id1, op1, msg1, ch_id2, op2, msg2, result_chan, result) {
	proc[_pid].state = READY;
	result = NULL;

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

	if
	:: (op1 == READ) -> 	remove_read(ch_id1, result);
	:: else 		remove_write(ch_id1);
	fi;
	if
	:: (op2 == READ) -> 	remove_read(ch_id2, result);
	:: else 		remove_write(ch_id2);
	fi;
	result_chan = proc[_pid].result_ch;
}
