import socket
import threading
import sys
import json


class IRCServerHandler:
    """
    IRC Server Handler to connect multiple clients to a server and then send messages between them    
    """
    clients = {}  # name of clients and their address stored in a dictionary
    rooms = {}  # rooms and their clients stored in a dictionary
    client_rooms = {}  # clients and their rooms stored in a dictionary
    rooms_list = []  # list of rooms stored

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
            receiver_socket = self.clients[receiver]["address"]
            receiver_socket.sendall(bytes(message, encoding="utf8"))
        except Exception as err:
            print(err)
            print("Unable to send msg to client:", receiver)

    def broadcast_to_clients(self, room_name, sender, message):
        """
        Function to send a message to all clients in a single room

        Args:
            room_name (str): Name of the room to which the broadcast needs to be sent to
            sender (str): The name of the sender
            message (str): The message that needs to be sent across
        """
        # go through all the clients on the requested room
        for receiver in self.rooms[room_name]:
            # do not send the message back to the client themselves
            if receiver != sender:
                self.send_message_to_client(receiver, message)

    def list_chat_rooms(self, client_name):
        """
        Function to list chat rooms on the server

        Args:
            client_name (str): The name of the client
        """
        all_chat_rooms = ",".join(x for x in self.rooms_list)
        all_chat_rooms = f"chat rooms : {all_chat_rooms}"
        self.send_message_to_client(client_name, all_chat_rooms)

    def create_chat_room(self, client_name, room_name):
        """
        Function to create a chat room

        Args:
            client_name (str): Name of the client
            room_name (str): Name of the room that needs to be created
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
        # check if room exists on the server rooms list
        if room_name in self.rooms:
            # add client name to rooms clients
            self.rooms[room_name].append(client_name)
            if client_name not in self.client_rooms:
                self.client_rooms[client_name] = []
            self.client_rooms[client_name].append(room_name)
            self.broadcast_to_clients(room_name, client_name, message)
        else:
            # send error message if the room does not exist
            self.send_message_to_client(client_name, "Error: room does not exist")

    def leave_chat_room(self, client_name, room_name, message):
        """
        Function to leave chat room

        Args:
            client_name (str): Name of the client that wants to leave the chat room
            room_name (str): Name of the chat room that the user will leave
            message (str): Message that will be broadcasted to clients upon leaving
        """
        # check if room exists on the server rooms list
        if room_name in self.rooms:
            # check if client is part of the chat room
            if client_name in self.rooms[room_name]:
                # remove them from the chat room and broadcast a message to all existing clients
                self.rooms[room_name].remove(client_name)
                self.client_rooms[client_name].remove(room_name)
                self.broadcast_to_clients(room_name, client_name, message)
                self.send_message_to_client(client_name, f"You have left the chatroom {room_name}")
            else:
                # send an error if client is not part of the chat room
                self.send_message_to_client(client_name, "Error: you have not joined the chat room")
        else:
            # send error message if the room does not exist
            self.send_message_to_client(client_name, "Error: room does not exist")

    def send_chatroom_message(self, client_name, room_name, message):
        """
        Function to send a message from a client to a chatroom

        Args:
            client_name (str): Client name that wants to send a message to a chatroom
            room_name (str): Name of the chat room to which we send a message
            message (str): Message that needs to be sent across
        """
        # check if room exists on the server rooms list
        if room_name in self.rooms:
            # if client is part of the chat room broadcast a message to all clients
            if client_name in self.rooms[room_name]:
                self.broadcast_to_clients(room_name, client_name, message)
            else:
                # throw an error if the client is not part of the chat room
                self.send_message_to_client(client_name, "Error: user is not in the room")
        else:
            # send error message if the room does not exist
            self.send_message_to_client(client_name, "Error: room does not exist")

    def send_direct_message(self, sender, receiver, message):
        """
        Function to send a direct message to another client

        Args:
            sender (str): Name of the sender who wants to send a DM
            receiver (str): Name of the receiver who sender wishes to send a message
            message (str): Message the sender wishes to send
        """
        # check if sender is there in the clients list
        if sender in self.clients:
            # check if the intended receiver is on the clients list
            if receiver in self.clients:
                # send a message to the receiver
                self.send_message_to_client(receiver, message)
            else:
                # send an error if the receiver is not found
                self.send_message_to_client(sender, "Error: receiver is not a registered client")
        else:
            # send an error if the sender is not found
            self.send_message_to_client(sender, "Error: sender is not a registered client")

    def list_chat_room_clients(self, client_name, room_name):
        """
        Function to list clients in a specific chat rooms

        Args:
            client_name (str): Name of the client that wishes to do the operation
            room_name (str): Name of the chat room for which they want to list clients
        """
        # check if client is part of the request chat room
        if client_name in self.rooms[room_name]:
            # form a string with the clients in that room
            room_clients = ",".join(x for x in self.rooms[room_name])
            room_clients = f"clients in room: {room_clients}"
            # send the message with the client names to the client
            self.send_message_to_client(client_name, room_clients)
        else:
            # send an error if the client is not part of the room
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
        # check if client is part of the client room
        if client_name in self.client_rooms:
            # remove the client from the room
            for room_name in self.client_rooms[client_name]:
                self.rooms[room_name].remove(client_name)
            del self.client_rooms[client_name]
        client_socket = self.clients[client_name]["address"]
        client_socket.close()
        print(f"Disconnected the client {client_name}")
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
                    print(f"{client_name} connected to the server")
                elif command == "CREATECHATROOM":
                    room_name = data_json["room_name"]
                    self.create_chat_room(client_name, room_name)
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
                    message = f"{client_name} from {room_name} says: " + data_json["message"]
                    self.send_chatroom_message(client_name, room_name, message)
                elif command == "SENDDIRECTMESSAGE":
                    receiver = data_json["receiver"]
                    message = f"{client_name} says: " + data_json["message"]
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
        This will be used to start a new thread for each new client. We will have new thread
        for each client because that way messages won't be lost

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
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((socket.gethostname(), 1078))
    server.listen(10)
    server = IRCServerHandler()
    while True:
        print("Waiting for new clients to connect")
        sys.stdout.flush()
        clt1, adr1 = server.accept()
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
