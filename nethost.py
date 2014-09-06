#coding:gbk
import socket
import select
import sys
import time
import errno
import netstream
import log
import gvars


class nethost(object):
	def __init__(self):
		self.host = 0
		self.state = gvars.NET_STATE_STOP
		self.clients = []
		self.count = 0
		self.index = 1
		self.queue = []
		self.sock = None
		self.port = 0
		self.timeout = 120.0
		self.timeslap = long(time.time()*1000)
		self.period = 0

	#start listening
	def startup(self, addr='0.0.0.0', port = 0):
		self.shutdown()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			self.sock.bind((addr, port))
		except:
			try: self.sock.close()
			except: pass
			log.critical('server startup failed.')
			return -1
		self.sock.listen(65536)
		self.sock.setblocking(0)
		self.port = self.sock.getsockname()[1]
		self.state = gvars.NET_STATE_ESTABLISHED
		self.timeslap = long(time.time()*1000)
		log.info('server startup.')
		return 0

	#shutdown service
	def shutdown(self):
		if self.sock:
			try:
				self.sock.close()
			except:
				pass
			self.sock = None

			for client in self.clients:
				if not client: continue
				try: 
					client.clise()
				except: 
					pass
			self.clients = []
			self.state = gvars.NET_STATE_STOP
			log.info('server shutdown.')

	def process(self):
		current = time.time()
		if self.state != gvars.NET_STATE_ESTABLISHED:
			return 0
		sock = None
		try:
			sock, remote = self.sock.accept()
			sock.setblocking(0)
		except:
			pass
		# 最大支持65536个客户端连接
		if self.count >= 0x10000:
			try:
				sock.close()
			except:
				pass
		if sock:
			pos = -1
			#找到空位
			for i in xrange(len(self.clients)):
				if self.clients[i] == None:
					pos = i
					break
			#没找到空位则新增
			if pos < 0:
				pos = len(self.clients)
				self.clients.append(None)

			hid = (pos & 0xffff) | (self.index << 16)
			self.index += 1
			if self.index >= 0x7fff:
				self.index = 1

			client = netstream.netstream()
			client.assign(sock)
			client.hid = hid
			client.tag = 0
			client.active = current
			client.peername = sock.getpeername()
			self.clients[pos] = client
			self.count += 1
			self.queue.append((gvars.NET_NEW, hid, 0, repr(client.peername)))
			log.info('client connected, peer: %s, pos: %d, index: %d'%(client.peername, pos, self.index-1))

		for pos in xrange(len(self.clients)):
			client = self.clients[pos]
			if not client:
				continue

			#handle client message
			client.process()
			# log.debug('try recv client data...., client stats: %d'%client.status())
			while client.status() == gvars.NET_STATE_ESTABLISHED:
				data = client.recv()
				if data is None:
					break
				self.queue.append((gvars.NET_DATA, client.hid, client.tag, data))
				client.active = current

			# handle client leave
			timeout = current - client.active
			if (client.status() == gvars.NET_STATE_STOP) or (timeout >= self.timeout):
				hid, tag = client.hid, client.tag
				self.queue.append((gvars.NET_LEAVE, hid, tag, ''))
				self.clients[pos] = None
				client.close()
				log.info('client leave, peer: %s, pos: %d'%(client.peername, pos))
				del client
				self.count -= 1

		current = long(time.time()* 1000)
		if current - self.timeslap > 100000:
			self.timeslap = current
		period = self.period
		if period > 0:
			while self.timeslap < current:
				self.queue.append(gvars.NET_TIMER, 0, 0, '')
				self.timeslap += period
		
		return 0	
