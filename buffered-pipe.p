#define BUFFER_SIZE 2
#define true 1
#define false 0

/* internal */
chan msg_chan = [99] of {bit, byte}; /* (require ack, msg) sender -> receiver */
chan ack_chan = [BUFFER_SIZE] of {bit}; /* receiver -> sender */
chan token_chan = [0] of {byte}; /* receiver -> sender */

/* enable / disable ack-tokens on buffered pipe. */
chan toggle_buffers_enabled = [0] of {bit};

bit send_ok = 0;

/* external */
chan put_link = [0] of {byte};
chan get_link = [0] of {byte};

active proctype sender() {
	byte msg;
	byte ack_tokens = 0;
	byte new_ack_tokens;
	bit ack;

	do
	:: put_link?msg ->
		if
		:: (ack_tokens > 0) ->
			ack_tokens--;
			send_ok = 1; /* accept send */
			msg_chan!false,msg;
		:: else ->
			msg_chan!true,msg;
			do
			:: ack_chan?ack ->
				send_ok = 1; /* accept send */
				printf("GOT ACK!\n");
				break;
			:: token_chan?new_ack_tokens ->	
				printf("GOT TOKENS: %d\n", new_ack_tokens);
				if
				:: (new_ack_tokens == 0) ->
					ack_tokens= 0;
				:: else ->
					ack_tokens = ack_tokens + new_ack_tokens;
				fi;
			od;

		fi;
	:: token_chan?new_ack_tokens ->
		printf("GOT TOKENS: %d\n", new_ack_tokens);
		if
		:: (new_ack_tokens == 0) ->
			ack_tokens= 0;
		:: else ->
			ack_tokens = ack_tokens + new_ack_tokens;
		fi;
	:: timeout ->
		break;
	od;
}

active proctype receiver() {
	chan buffer = [BUFFER_SIZE] of {byte};
	byte msg, next;
	byte items = 0;
	byte ack_tokens = BUFFER_SIZE;
	bit require_ack;
	bit buffers_enabled;

	do
	:: msg_chan?require_ack,msg ->
		if
		:: (items == BUFFER_SIZE) ->
			buffer!msg;
			get_link!next;
			buffer?next;
		:: (items == 0) ->
			items++;
			next = msg;
		:: else ->
			items++;
			buffer!msg;
		fi;
		if
		:: require_ack==true ->
			printf("SENDING ACK\n");
			ack_chan!true;
		:: else skip;
		fi;
	:: toggle_buffers_enabled?buffers_enabled ->
		if
		:: buffers_enabled == true ->
			ack_tokens = BUFFER_SIZE;
			token_chan!ack_tokens;
		:: else ->			
			ack_tokens = 0;
			token_chan!ack_tokens;
			printf("DISABLE BUFFERS\n");
		fi;

	:: (items > 0) ->
		printf("LOOP: items=%d, ack_tokens=%d\n",items, ack_tokens);
		if
		:: get_link!next ->
			printf("LOOP_DELIVERED!\n");
			items--;
			printf("ITEMS left:%d, items\n", items);
			if
			:: (items > 0) ->
				buffer?next
			:: else skip;
			fi;
			if
			:: buffers_enabled == true ->
				ack_tokens++;
			:: else skip;
			fi;
	
		fi;
		printf("LOOP2\n");
	:: (ack_tokens > 0) ->
		printf("TRY UPDATE TOKENS:%d\n", ack_tokens);
		token_chan!ack_tokens;
		ack_tokens = 0;
	:: timeout ->
		assert(items == 0);
		break;
	od;
}

inline send (msg) {
	send_ok = 0;
	put_link!msg;
	send_ok == 1; /* wait for ok */
	printf("SEND(%d): %d\n", _pid, msg);
}

inline receive(msg) {
	get_link?msg;
	printf("GOT(%d): %d\n", _pid, msg);
}

active proctype P1() {
	send(42);
	send(111);
	send(5);
}

active proctype P2() {
	byte result;
	receive(result) -> assert(result == 42);
	receive(result) -> assert(result == 111);
	receive(result) -> assert(result == 5);

}

active proctype P3() {
	toggle_buffers_enabled!false;
}
