import socket
import threading
import sys
import json

"""
IRC Server Handler to connect multiple clients to a server and then send messages between them
"""


class IRCServerHandler:
    clients = {}
    rooms = {}
    client_rooms = {}
    rooms_list = []

    def __init__(self):
        """
        Initializing the IRC server
        """
        print("Initializing Server")

    def send_message_to_client(self, receiver, message):
        """
        Function to send message from a client to a receiver

        Args:
            receiver (str): This is the name of the client to which you want to send message to
            message (str): This is the message that needs to be sent across
        """
        try:
            receiver_sock = self.clients[receiver]["address"]
            receiver_sock.sendall(bytes(message, encoding="utf8"))
        except Exception as e:
            print(e)
            print("Unable to send msg to client:", receiver)

    def broadcast_to_clients(self, room_name, sender, message):
        """
        Function to send a message to all clients in a single room

        Args:
            room_name (str): Name of the room to which the broadcast needs to be sent to
            sender (str): The name of the sender
            message (str): The message that needs to be sent across
        """
        for receiver in self.rooms[room_name]:
            if receiver != sender:
                self.send_message_to_client(receiver, message)

    def list_chat_rooms(self, client_name):
        """
        Function to list chat rooms on the server

        Args:
            client_name (str): The name of the client
        """
        all_chat_rooms = "chat rooms : %s" % ",".join(x for x in self.rooms_list)
        self.send_message_to_client(client_name, all_chat_rooms)

    def create_chat_room(self, client_name, room_name, message):
        """
        Function to create a chat room

        Args:
            client_name (str): Name of the client
            room_name (str): Name of the room that needs to be created
            message (str): The first message that needs to be sent
        """
        chat_room_clients = [client_name]
        self.rooms[room_name] = chat_room_clients
        self.client_rooms[client_name] = [room_name]
        self.rooms_list.append(room_name)

        self.send_message_to_client(client_name, "Successfully created chatroom")

    def join_chat_room(self, client_name, room_name, message):
        """
        Function to join a chat room for the client

        Args:
            client_name (str): Name of the client that needs to join the room
            room_name (str): Name of the room
            message (str): Message that needs to be sent
        """
        if room_name in self.rooms:
            self.rooms[room_name].append(client_name)
            if client_name not in self.client_rooms:
                self.client_rooms[client_name] = []
            self.client_rooms[client_name].append(room_name)
            self.broadcast_to_clients(room_name, client_name, message)
        else:
            self.send_message_to_client(client_name, "Error: room does not exist")

    def leave_chat_room(self, client_name, room_name, message):
        """
        Function to leave chat room

        Args:
            client_name (str): Name of the client that wants to leave the chat room
            room_name (str): Name of the chat room that the user will leave
            message (str): Message that will be broadcasted to clients upon leaving
        """
        if room_name in self.rooms:
            if client_name in self.rooms[room_name]:
                self.rooms[room_name].remove(client_name)
                self.client_rooms[client_name].remove(room_name)
                self.broadcast_to_clients(room_name, client_name, message)
                self.send_message_to_client(
                    client_name, "You have left the chatroom %s" % room_name
                )
            else:
                self.send_message_to_client(client_name, "Error: you have not joined the chat room")
        else:
            self.send_message_to_client(client_name, "Error: room does not exist")

    def send_chatroom_message(self, client_name, room_name, message):
        """
        Function to send a message from a client to a chatroom

        Args:
            client_name (str): Client name that wants to send a message to a chatroom
            room_name (str): Name of the chat room to which we send a message
            message (str): Message that needs to be sent across
        """
        if room_name in self.rooms:
            if client_name in self.rooms[room_name]:
                self.broadcast_to_clients(room_name, client_name, message)
            else:
                self.send_message_to_client(client_name, "Error: user is not in the room")
        else:
            self.send_message_to_client(client_name, "Error: room does not exist")

    def send_direct_message(self, sender, receiver, message):
        """
        Function to send a direct message to another client

        Args:
            sender (str): Name of the sender who wants to send a DM
            receiver (str): Name of the receiver who sender wishes to send a message
            message (str): Message the sender wishes to send
        """
        if sender in self.clients:
            if receiver in self.clients:
                self.send_message_to_client(receiver, message)
            else:
                self.send_message_to_client(
                    "Error: receiver is not a registered client"
                )
        else:
            self.send_message_to_client(sender, "Error: sender is not a registered client")

    def list_chat_room_clients(self, client_name, room_name):
        """
        Function to list clients in a specific chat rooms

        Args:
            client_name (str): Name of the client that wishes to do the operation
            room_name (str): Name of the chat room for which they want to list clients
        """
        if client_name in self.rooms[room_name]:
            room_clients = "clients in room: %s" % ",".join(
                x for x in self.rooms[room_name]
            )
            self.send_message_to_client(client_name, room_clients)
        else:
            self.send_message_to_client(
                client_name,
                "Error: You do not belong to the chat room, join chat room first",
            )

    def leave_server(self, client_name):
        """
        Function to remove a client from the server

        Args:
            client_name (str): Client that wants to leave the server
        """
        if client_name in self.client_rooms:
            for room_name in self.client_rooms[client_name]:
                self.rooms[room_name].remove(client_name)
            del self.client_rooms[client_name]
        client_socket = self.clients[client_name]["address"]
        client_socket.close()
        print("Disconnected the client %s " % client_name)
        sys.exit(1)

    def decode_client_message(self, clt):
        """
        Function to decode each incoming message from respective client and invoke their function

        Args:
            clt (object): Socket object from which we will receive and send message to
        """
        while True:
            data = clt.recv(1024)
            if data:
                data_json = json.loads(data.decode("utf-8"))
                client_name = data_json["clientname"].strip()
                self.clients[client_name] = {"address": clt}
                command = data_json["command"]
                if command == "CLIENTINIT":
                    print("%s connected to the server" % client_name)
                elif command == "CREATECHATROOM":
                    room_name = data_json["room_name"]
                    message = data_json["message"]
                    self.create_chat_room(client_name, room_name, message)
                elif command == "JOINCHATROOM":
                    room_name = data_json["room_name"]
                    message = data_json["message"]
                    self.join_chat_room(client_name, room_name, message)
                elif command == "LISTCHATROOMS":
                    self.list_chat_rooms(client_name)
                elif command == "LEAVECHATROOM":
                    room_name = data_json["room_name"]
                    message = data_json["message"]
                    self.leave_chat_room(client_name, room_name, message)
                elif command == "SENDMESSAGE":
                    room_name = data_json["room_name"]
                    message = (
                        "%s from %s says: " % (client_name, room_name)
                        + data_json["message"]
                    )
                    self.send_chatroom_message(client_name, room_name, message)
                elif command == "SENDDIRECTMESSAGE":
                    receiver = data_json["receiver"]
                    message = "%s says: " % client_name + data_json["message"]
                    self.send_direct_message(client_name, receiver, message)
                elif command == "LISTCHATROOMCLIENTS":
                    room_name = data_json["room_name"]
                    message = data_json["message"]
                    self.list_chat_room_clients(client_name, room_name)
                elif command == "DISCONNECT":
                    self.leave_server(client_name)
                else:
                    print("WRONG COMMAND, send retry to user")
            else:
                self.leave_server(client_name)

    def start_new_thread(self, clt, adr):
        """
        This will be used to start a new thread for each new client. We will have new thread for each client because that way messages won't be lost

        Args:
            clt (object): The socket object with which we have to read and send messages to
            adr (Address): Address from which the connection was being made
        """
        print(adr[0] + " is now connected! and starting a new thread")
        self.decode_client_message(clt)


def start_server():
    """
    The main function start starts the IRC server and starts listening for 10 clients at max!
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((socket.gethostname(), 1078))
    s.listen(10)
    server = IRCServerHandler()
    while True:
        print("Waiting for new clients to connect")
        sys.stdout.flush()
        clt1, adr1 = s.accept()
        cltr_thread = threading.Thread(
            target=server.start_new_thread,
            args=(
                clt1,
                adr1,
            ),
        )
        cltr_thread.start()


if __name__ == "__main__":
    start_server()
