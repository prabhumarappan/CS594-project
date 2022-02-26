import socket
import threading
import sys

class IRCServerHandler():
    def __init__(self) -> None:
        print("Initializing Server")
    
    def broadcast_to_clients(self):
        pass

    def list_chat_rooms(self):
        pass

    def create_chat_room(self):
        pass

    def join_chat_room(self):
        pass

    def leave_chat_room(self):
        pass

    def send_message(self):
        pass

    def send_direct_message(self):
        pass

    def list_clients(self):
        pass

    def enable_secure_messaging(self):
        pass

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
        cltThread=threading.Thread(target=server.startNewThread, args=(clt1, adr1,))
        cltThread.start()

if __name__ == "__main__":
    start_server()
