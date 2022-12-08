import sys
import socket
import sys
import os
import json
import select

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", socket.gethostname())
SERVER_PORT = int(os.getenv("SERVER_PORT", 1078))
MSS = 1024


"""
IRC Client to interact with user through CLI and communicate the same with the server
"""


class IRCClient:
    def __init__(self, client_name) -> None:
        """
        Start a new client, connect them to the server by sending a intilaization message.

        Args:
            	client_name (str): Name of the client that will be send to the for future correspondence
        """
        print("Connecting Client %s To Server" % client_name, flush=True)
        self.client_name = client_name
        self.clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientSock.connect((SERVER_ADDRESS, SERVER_PORT))
        data = {
            "command": "CLIENTINIT",
            "room_name": client_name,
            "clientname": client_name,
            "message": "Joining %s Server" % client_name,
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)
        print("Connected Client %s To Server" % client_name, flush=True)

    def make_payload(
        self, command, client_name, message, room_name=None, receiver=None
    ) -> dict:
        """
        Function to create a payload that would be sent to the server

        Args:
                command (str): Command that needs to be executed at the server
                client_name (str): Client name that is sending the message
                message (str): The message that needs to be sent along
                room_name (str, optional): Room name that message needs to be sent to. Defaults to None.
                receiver (str, optional): _description_. Defaults to None.

        Returns:
                dict: Paylaod for the server
        """

        data = {"clientname": client_name, "message": message, "command": command}

        if room_name:
            data["room_name"] = room_name
        if receiver:
            data["receiver"] = receiver

        return data

    def create_chat_room(self, name):
        """
        Function to create a chat room from the clients end. Client will format and send a message to server so that it can create the specific chat room

        Args:
                name (str): Name of the chat room that needs to be created
        """
        data = {
            "command": "CREATECHATROOM",
            "room_name": name,
            "clientname": self.client_name,
            "message": "%s created this chatroom" % (self.client_name),
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def join_chat_room(self, name):
        """
        Function to join an existing chat room by it's name

        Args:
                name (str): Name of the chat room
        """
        data = {
            "command": "JOINCHATROOM",
            "room_name": name,
            "clientname": self.client_name,
            "message": "%s joined this chatroom" % (self.client_name),
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def send_message(self, name, message):
        """
        Function to send a message from the client to a specific chatroom on the server

        Args:
                name (str): Name of the chat room to which the client wants to send a message
                message (str): Message that the client wants to send a message
        """
        data = {
            "command": "SENDMESSAGE",
            "room_name": name,
            "clientname": self.client_name,
            "message": message,
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def send_direct_message(self, receiver, message):
        """
        Function to send a message to another client (a DM). This will format and send the message to the server, which will relay the message to the specific receiver.

        Args:
                        receiver (str): Name of the receiver, the client wishes to send a message
                        message (str): Message that the client wants to send
        """
        data = {
            "command": "SENDDIRECTMESSAGE",
            "receiver": receiver,
            "clientname": self.client_name,
            "message": message,
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def leave_chat_room(self, name):
        """
        Function to leave an existing chat room. Sends the chat room that the client is part of, and server removes them from that list

        Args:
                name (str): Name of the chat room from which they want to be removed
        """
        data = {
            "command": "LEAVECHATROOM",
            "room_name": name,
            "clientname": self.client_name,
            "message": "%s has left this chatroom" % (self.client_name),
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def disconnect(self):
        """
        Function to disconnect the client from the server. This sends the client a message and server kills the thread that it had assigned for the client.
        """
        data = {
            "command": "DISCONNECT",
            "room_name": None,
            "clientname": self.client_name,
            "message": "%s has left the server" % (self.client_name),
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def list_chat_rooms(self):
        """
        Function to list chat rooms on the server. This send back a list of chat rooms.
        """
        data = {
            "command": "LISTCHATROOMS",
            "room_name": None,
            "clientname": self.client_name,
            "message": None,
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def list_chat_room_clients(self, room_name):
        """
        Function to list clients on a specific chat room. Given a chat room name, the server responds with the clients names

        Args:
                room_name (str): Name of the chat room
        """
        data = {
            "command": "LISTCHATROOMCLIENTS",
            "room_name": room_name,
            "clientname": self.client_name,
            "message": None,
        }
        dataToSend = json.dumps(data).encode("utf-8")
        self.clientSock.sendall(dataToSend)

    def start_chat(self):
        """
        Function that helps the client to communicate with the server by constantly taking inputs from the user through a while loop and sending messages back and forth.
        """
        sockets_list = [sys.stdin, self.clientSock]

        while True:
            try:
                print("Input Command: ", flush=True)
                read, write, error = select.select(sockets_list, [], [])
                for fd in read:
                    if fd is self.clientSock:
                        msg = self.clientSock.recv(MSS)
                        if not msg:
                            print(
                                "The connection with the server has been closed",
                                flush=True,
                            )
                            sys.exit(1)
                        else:
                            msg = msg.decode("utf-8")
                            print(msg, flush=True)
                    elif fd is sys.stdin:
                        msg = sys.stdin.readline().replace("\n", "")
                        cmd = msg.split(" ", 1)[0]
                        if cmd == "CREATECHATROOM":
                            room_name = msg.split(" ", 1)[1]
                            self.create_chat_room(room_name)
                        elif cmd == "JOINCHATROOM":
                            room_name = msg.split(" ", 1)[1]
                            self.join_chat_room(room_name)
                        elif cmd == "SENDMESSAGE":
                            room_name, message = msg.split(" ", 2)[1:]
                            self.send_message(room_name, message)
                            # print("you say: %s" % message)
                        elif cmd == "SENDDIRECTMESSAGE":
                            receiver = msg.split(" ", 2)[1]
                            message = msg.split(" ", 2)[2]
                            self.send_direct_message(receiver, message)
                        elif cmd == "LEAVECHATROOM":
                            room_name = msg.split(" ", 1)[1]
                            self.leave_chat_room(room_name)
                        elif cmd == "DISCONNECT":
                            self.disconnect()
                        elif cmd == "LISTCHATROOMCLIENTS":
                            room_name = msg.split(" ", 1)[1]
                            self.list_chat_room_clients(room_name)
                        elif cmd == "LISTCHATROOMS":
                            self.list_chat_rooms()
                        else:
                            print("Invalid command")
            except select.error:
                # this happens when the socket connection has errored out, so in this case we shutdown the connection and close it.
                print("closing it")
                self.clientSock.shutdown(2)
                self.clientSock.close()
            except Exception as e:
                print("Exception Occurred!")
                print(e)


def main():
    """
    Main function to get the client name, initiate the client connection to the server and start the client to take/receieve commands.
    """
    clientName = input("Enter Client Name: ").strip()
    client = IRCClient(clientName)
    client.start_chat()


if __name__ == "__main__":
    main()
