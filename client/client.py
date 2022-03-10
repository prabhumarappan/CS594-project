import sys
import socket
import sys
import os
import json
import select

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", socket.gethostname())
SERVER_PORT = int(os.getenv("SERVER_PORT", 1078))
MSS = 1024

print(SERVER_ADDRESS, SERVER_PORT)

class IRCClient():
	def __init__(self, client_name) -> None:
		print("Connecting Client %s To Server" % client_name, flush=True)
		self.client_name = client_name
		self.clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.clientSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.clientSock.connect((SERVER_ADDRESS, SERVER_PORT))
		data = {
			"command": "CLIENTINIT",
			"room_name": client_name, 
			"clientname": client_name,
			"message": 'Joining %s Server' % client_name
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)
		print("Connected Client %s To Server" % client_name, flush=True)

	def create_chat_room(self, name):
		data = {
			"command": "CREATECHATROOM",
			"room_name": name,
			"clientname": self.client_name, 
			"message": "%s created this chatroom" % (self.client_name)
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def join_chat_room(self, name):
		data = {
			"command": "JOINCHATROOM",
			"room_name": name,
			"clientname": self.client_name, 
			"message": "%s joined this chatroom" % (self.client_name)
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)
	
	def send_message(self, name, message):
		data = {
			"command": "SENDMESSAGE",
			"room_name": name,
			"clientname": self.client_name, 
			"message": message
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def send_direct_message(self, receiver, message):
		data = {
			"command": "SENDDIRECTMESSAGE",
			"receiver": receiver,
			"clientname": self.client_name, 
			"message": message
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def leave_chat_room(self, name):
		data = {
			"command": "LEAVECHATROOM",
			"room_name": name,
			"clientname": self.client_name, 
			"message": "%s has left this chatroom" % (self.client_name)
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def disconnect(self):
		data = {
			"command": "DISCONNECT",
			"room_name": None,
			"clientname": self.client_name, 
			"message": "%s has left the server" % (self.client_name)
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def list_chat_rooms(self):
		data = {
			"command": "LISTCHATROOMS",
			"room_name": None,
			"clientname": self.client_name, 
			"message": None
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def list_chat_room_clients(self, room_name):
		data = {
			"command": "LISTCHATROOMCLIENTS",
			"room_name": room_name,
			"clientname": self.client_name, 
			"message": None
		}
		dataToSend = json.dumps(data).encode("utf-8")
		self.clientSock.sendall(dataToSend)

	def start_chat(self):
		sockets_list = [sys.stdin, self.clientSock]

		while True:
			try:
				print("Input Command: ", flush=True)
				read, write, error = select.select(sockets_list,[],[])
				for fd in read:
					if fd is self.clientSock:
						msg = self.clientSock.recv(MSS)
						if not msg:
							print("The connection with the server has been closed", flush=True)
							sys.exit(1)
						else:
							msg = msg.decode('utf-8')
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
							receiver = msg.split(" ",2)[1]
							message = msg.split(" ", 2)[2]
							self.send_direct_message(receiver, message)
						elif cmd == "LEAVECHATROOM":
							room_name = msg.split(" ",1)[1]
							self.leave_chat_room(room_name)
						elif cmd == "DISCONNECT":
							self.disconnect()
						elif cmd == "LISTCHATROOMCLIENTS":
							room_name = msg.split(" ",1)[1]
							self.list_chat_room_clients(room_name)
						elif cmd == "LISTCHATROOMS":
							self.list_chat_rooms()
						else:
							print("Invalid command")
			except select.error:
				print('closing it')
				self.clientSock.shutdown(2)
				self.clientSock.close()
			except Exception as e:
				print("Exception Occurred!")
				print(e)
	


def main():
	clientName = input("Enter Client Name: ").strip()
	client = IRCClient(clientName)
	client.start_chat()

if __name__ == "__main__":
	main()
