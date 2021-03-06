#!/usr/bin/python

import socket
import sys
import thread
import threading
import os

# Sequence to define who is who
req_father = 'M'
ack_child_accept = 'P'
ack_child_deny = 'R'

# Global var for parents, father and children
parent = None
me = None
F = []
NF = []
V = []
NE = []
end = False
my_port = None

# Get all neighbour from file
def get_neighbour(neighbour_file):
	with open(neighbour_file) as f:
		for line in f:
			NE.append(line.rstrip())
	f.close()

def socket_send(message, ip, port, id):
	
	# Forge message
	message = str(ip) + ':' + str(port) + ':' + str(message) + ':' + str(id)
			
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	# Connect the socket to the port where the server is listening
	# send message to the neighbour (child or father)
	server_address = (ip, int(port))
	sock.connect(server_address)
	sock.send(message)
	sock.close()
	
def socket_receive(ip, port, end, parent):
	
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	
	# Bind the socket to the port
	server_address = (ip, port)
	sock.bind(server_address)
	
	# Listen for incoming connections
	sock.listen(50)
	peer_ip = ""
	while not end:

		# Wait for a connection
		connection, client_address = sock.accept()		
		try:
		
			# Receive the data in small chunks and retransmit it
			message = connection.recv(1024)
			
			# Get peer ip and port
			peer_ip, peer_port = connection.getpeername()
		finally:
		
			# Clean up the connection
			connection.close()
			
		# Split received messsage 
		sent_ip, sent_port, sent_message, send_id = message.split(":") 
		sent_ip = peer_ip
	
		if sent_message == req_father:
			if parent== None:
				parent= sent_ip + ":" + send_id
				NE.remove(parent)
				if len(NE) != 0:
					# Neighbour not explored yet
					child = NE.pop()

					# Split child ip and port
					child_ip, child_port = child.split(':')

					# After sending to the first child wait for the P(ack_child_accept)
					socket_send(req_father, child_ip, child_port, my_port)
				else:

					father_ip, father_port = parent.split(':')
					socket_send(ack_child_accept, father_ip, father_port, my_port)
					end=True

					# Print chlidren
					print("child")
					for i in F:
						print(i)
					print("parent")
					print(parent)
					print("end")
			else:
				socket_send(ack_child_deny, sent_ip, sent_port)
			
		elif (sent_message == ack_child_accept) or (sent_message == ack_child_deny):
			if sent_message == ack_child_accept:
				F.append(sent_ip + ":" + send_id)
			elif sent_message == ack_child_deny:
				NF.append(sent_ip + ":" + send_id)
			if len(NE) != 0:
			
				# Neighbour not explored yet
				child = NE.pop()

				# Split child ip and port
				child_ip, child_port = child.split(':')

				# After sending to the first child wait for the P(ack_child_accept)
				socket_send(req_father, child_ip, child_port, my_port)
			else:
				if parent != me:
					father_ip, father_port = parent.split(':')
					socket_send(ack_child_accept, father_ip, father_port, my_port)
					end=True

					# Print child and parent
					print("child")
					for i in F:
						print(i)
					print("parent")
					print(parent)
					print("end")
		

# Main function
if __name__ == "__main__":

	# Check args (prog[0], port[1], file[2], status[3])
	if len(sys.argv) != 4:
		print ("distributed_alg <port> <neighbour_file> <status>")
		sys.exit(1)
	
	# My port and status
	my_port = int(sys.argv[1])
	status = sys.argv[3]

	# Get my IP address
	interface="eth0"
	my_ip = os.popen("ip addr show "+interface).read().split("inet ")[1].split("/")[0]

	# Get all neighbour from file
	get_neighbour(sys.argv[2])

	# Root node
	if status == 'INIT':

		parent=str(my_ip)+":"+str(my_port)

		# CReate thread for the receiver
		thread_receive = threading.Thread(target=socket_receive,args=(my_ip, my_port, end, parent))
		
		# start to receive message
		thread_receive.start()

		if  len(NE) != 0:
		
			# Get neighbour not explored yet
			child = NE.pop()
		child_ip, child_port = child.split(':')

		# After sending to the first child wait for the P(ack_child_accept)
		socket_send(req_father, child_ip, child_port, my_port)
		
	# Other node
	elif status == 'WAIT':

		# CReate thread for the receiver
		thread_receive = threading.Thread(target=socket_receive,args=(my_ip, my_port, end, parent))

		# start to receive message
		thread_receive.start()

	# The main function must join the thread receiver cause otherwise, the main can finish before the thread !
	thread_receive.join()
