from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.rsa_public_key, self.rsa_private_key = generate_rsa_keys()
        self.rsa_public_key_str = serialize_public_key(self.rsa_public_key).decode()
        self.peer_public_key = None
        self.key_exchanged = False
        self.sent_pubkey = False 



    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''
        self.peer_public_key = None
        self.key_exchanged = False
    
    def send_my_public_key(self):
        if self.peer and not self.sent_pubkey:
            msg = json.dumps({
                "action": "send_public_key",
                "from": self.me,
                "to": self.peer,
                "public_key": self.rsa_public_key_str
            })
            mysend(self.s, msg)
            self.sent_pubkey = True
            self.out_msg += "[System] Your public key has been sent to peer.\n"

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                        self.send_my_public_key()
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING
                elif peer_msg["action"] == "send_public_key":
                    self.peer_public_key = deserialize_public_key(peer_msg["public_key"].encode())
                    if not self.key_exchanged:
                        self.send_my_public_key()
                        self.key_exchanged = True


#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                if self.peer_public_key is None:
                    self.out_msg += "[System] Waiting for peer's public key, cannot send encrypted messages yet.\n"
                else:
                    encrypted_bytes = rsa_encrypt(my_msg, self.peer_public_key)
                    encrypted_b64 = base64.b64encode(encrypted_bytes).decode()
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":encrypted_b64}))
                    if my_msg == 'bye':
                        self.disconnect()
                        self.state = S_LOGGEDIN
                        self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                elif peer_msg["action"] == "send_public_key":
                    self.peer_public_key = deserialize_public_key(peer_msg["public_key"].encode())
                    if not self.key_exchanged:
                        self.send_my_public_key()
                        self.key_exchanged = True
                    self.out_msg += "[System] Received public key from " + peer_msg["from"] + "\n"
                elif peer_msg["action"] == "exchange":
                    encrypted_b64 = peer_msg["message"]
                    encrypted_bytes = base64.b64decode(encrypted_b64)
                    decrypted_msg = rsa_decrypt(encrypted_bytes, self.rsa_private_key).decode()
                    self.out_msg += peer_msg["from"] + decrypted_msg
                
                elif peer_msg["action"] == "digit_result":
                    self.out_msg += (f"{peer_msg['from']} 识别数字: {peer_msg['digit']}\n"
                     f"识别时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(peer_msg['timestamp']))}")


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
