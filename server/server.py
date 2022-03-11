import socket
import threading
import sys
import json

class IRCServerHandler():
    clients = {}
    rooms = {}
    client_rooms = {}
    rooms_list = []

    def __init__(self):
        print("Initializing Server")

    def send_message_to_client(self, receiver, message):
        try:
            receiver_sock = self.clients[receiver]["address"]
            receiver_sock.sendall(bytes(message, encoding='utf8'))
        except Exception as e:
            print(e)
            print("Unable to send msg to client:", receiver)
    
    def broadcast_to_clients(self, room_name, sender, message):
        for receiver in self.rooms[room_name]:
            if receiver != sender:
                self.send_message_to_client(receiver, message)

    def list_chat_rooms(self, client_name):
        all_chat_rooms = "chat rooms : %s" % ",".join(x for x in self.rooms_list)
        self.send_message_to_client(client_name, all_chat_rooms)

    def create_chat_room(self, client_name, room_name, message):
        chat_room_clients = [client_name]
        self.rooms[room_name] = chat_room_clients
        self.client_rooms[client_name] = [room_name]
        self.rooms_list.append(room_name)

        self.send_message_to_client(client_name, "Successfully created chatroom")

    def join_chat_room(self, client_name, room_name, message):
        if room_name in self.rooms:
            self.rooms[room_name].append(client_name)
            if client_name not in self.client_rooms:
                self.client_rooms[client_name] = []
            self.client_rooms[client_name].append(room_name)
            self.broadcast_to_clients(room_name, client_name, message)
        else:
            self.send_message_to_client(client_name, "Error: room does not exist")

    def leave_chat_room(self, client_name, room_name, message):
        if room_name in self.rooms:
            if client_name in self.rooms[room_name]:
                self.rooms[room_name].remove(client_name)
                self.client_rooms[client_name].remove(room_name)
                self.broadcast_to_clients(room_name, client_name, message)
                self.send_message_to_client(client_name, "You have left the chatroom %s" % room_name)
            else:
                self.send_message_to_client("Error: you have not joined the chat room")
        else:
            self.send_message_to_client("Error: room does not exist")

    def send_chatroom_message(self, client_name, room_name, message):
        if room_name in self.rooms:
            if client_name in self.rooms[room_name]:
                self.broadcast_to_clients(room_name, client_name, message)
            else:
                self.send_message_to_client("Error: user is not in the room")
        else:
            self.send_message_to_client("Error: room does not exist")

    def send_direct_message(self, sender, receiver, message):
        if sender in self.clients:
            if receiver in self.clients:
                self.send_message_to_client(receiver, message)
            else:
                self.send_message_to_client("Error: receiver is not a registered client")
        else:
            self.send_message_to_client("Error: sender is not a registered client")

    def list_chat_room_clients(self, client_name, room_name):
        if client_name in self.rooms[room_name]:
            room_clients = "clients in room: %s" % ",".join(x for x in self.rooms[room_name])
            self.send_message_to_client(client_name, room_clients)
        else:
            self.send_message_to_client(client_name, "Error: You do not belong to the chat room, join chat room first")

    def leave_server(self, client_name):
        if client_name in self.client_rooms:
            for room_name in self.client_rooms[client_name]:
                self.rooms[room_name].remove(client_name)
            del self.client_rooms[client_name]
        client_socket = self.clients[client_name]["address"]
        client_socket.close()
        print("Disconnected the client %s " % client_name)
        sys.exit(1)

    def decode_client_message(self, clt):
        while True:
            data = clt.recv(1024)
            if data:
                # print("Client sent ", data)
                data_json = json.loads(data.decode('utf-8'))
                client_name = data_json['clientname'].strip()
                self.clients[client_name] = {
                    "address": clt
                }
                command = data_json['command']
                if command == 'CLIENTINIT':
                    print("%s connected to the server"  % client_name)
                elif command == 'CREATECHATROOM':
                    room_name = data_json['room_name']
                    message = data_json['message']
                    self.create_chat_room(client_name, room_name, message)
                elif command == 'JOINCHATROOM':
                    room_name = data_json['room_name']
                    message = data_json['message']
                    self.join_chat_room(client_name, room_name, message)
                elif command == 'LISTCHATROOMS':
                    room_name = data_json['room_name']
                    self.list_chat_rooms(client_name)
                elif command == 'LEAVECHATROOM':
                    room_name = data_json['room_name']
                    message = data_json['message']
                    self.leave_chat_room(client_name, room_name, message)
                elif command == 'SENDMESSAGE':
                    room_name = data_json['room_name']
                    message = '%s from %s says: ' % (client_name, room_name) + data_json['message']
                    self.send_chatroom_message(client_name, room_name, message)
                elif command == 'SENDDIRECTMESSAGE':
                    receiver = data_json['receiver']
                    message = '%s says: ' % client_name + data_json['message']
                    self.send_direct_message(client_name, receiver, message)
                elif command == 'LISTCHATROOMCLIENTS':
                    room_name = data_json['room_name']
                    message = data_json['message']
                    self.list_chat_room_clients(client_name, room_name)
                elif command == 'DISCONNECT':
                    self.leave_server(client_name)
                else:
                    print("WRONG COMMAND, send retry to user")
            else:
                self.leave_server(client_name)
                     
    def start_new_thread(self, clt, adr):
        print(adr[0] + " is now connected! and starting a new thread")
        self.decode_client_message(clt)

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((socket.gethostname(), 1078))
    s.listen(10)
    server = IRCServerHandler()
    while True:
        print("Waiting for new clients to connect")
        sys.stdout.flush()
        clt1, adr1 = s.accept()
        cltr_thread = threading.Thread(target=server.start_new_thread, args=(clt1, adr1,))
        cltr_thread.start()

if __name__ == "__main__":
    start_server()
