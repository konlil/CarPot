#coding:gbk
import socket
import time
import netstream2 as netstream
import log
import gvars
import protoc
import models
import asyncore

class nethost(asyncore.dispatcher):
	def __init__(self):
		asyncore.dispatcher.__init__(self)
		self.host = 0
		self.state = gvars.NET_STATE_STOP
		self.clients = []
		self.count = 0
		self.index = 1
		self.queue = []
		self.timeout = 120.0
		self.timeslap = long(time.time()*1000)
		self.period = 0

	#start listening
	def startup(self, addr='0.0.0.0', port = 0):
		self.shutdown()
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		try:
			self.bind((addr, port))
		except:
			try: self.close()
			except: pass
			log.critical('server startup failed.')
			return -1
		self.listen(65536)
		self.state = gvars.NET_STATE_ESTABLISHED
		self.timeslap = long(time.time()*1000)
		log.info('server startup.')
		return 0

	#shutdown service
	def shutdown(self):
		if self.state == gvars.NET_STATE_STOP:
			return
		try:
			self.close()
		except:
			pass

		for client in self.clients:
			if not client: continue
			try:
				client.close()
			except:
				pass
		self.clients = []
		self.state = gvars.NET_STATE_STOP
		log.info('server shutdown.')

	def handle_accept(self):
		current = time.time()
		if self.state != gvars.NET_STATE_ESTABLISHED:
			return 0
		sock = None
		try:
			sock, remote = self.accept()
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
			client.tag = -1
			client.active = current
			client.peername = sock.getpeername()

			client.on_recv = self.on_client_recv
			client.on_close = self.on_client_close

			self.clients[pos] = client
			self.count += 1
			self.queue.append((gvars.NET_NEW, hid, 0, repr(client.peername)))
			log.info('client connected, peer: %s, pos: %d, index: %d'%(client.peername, pos, self.index-1))

	def on_client_recv(self, client):
		current = time.time()
		if client.status() == gvars.NET_STATE_ESTABLISHED or 1:
			data = client.read_pkg()
			if data is None:
				return
			log.debug('recv pkg from client: %s, data: %s'%(client.peername, data))
			self.queue.append((gvars.NET_DATA, client.hid, client.tag, data))
			client.active = current
			self.process_event(client.hid, client.tag, data)

	def on_client_close(self, client):
		hid, tag = client.hid, client.tag
		pos = hid & 0xffff
		self.queue.append((gvars.NET_LEAVE, hid, tag, ''))
		self.clients[pos] = None
		log.info('client leave, peer: %s, pos: %d'%(client.peername, pos))
		del client
		self.count -= 1

	# send data to hid
	# def send(self, hid, data):
	# 	pos = hid & 0xffff
	# 	if (pos < 0) or (pos >= len(self.clients)): return -1
	# 	client = self.clients[pos]
	# 	if client == None: return -2
	# 	if client.hid != hid: return -3
	# 	client.send(data)
	# 	client.process()
	# 	return 0

	# # close client
	# def close(self, hid):
	# 	pos = hid & 0xffff
	# 	if (pos < 0) or (pos >= len(self.clients)): return -1
	# 	client = self.clients[pos]
	# 	if client == None: return -2
	# 	if client.hid != hid: return -3
	# 	client.close()
	# 	return 0

	# 向数据库注册终端
	def regist_terminal(self, cid, pid):
		term = models.Terminal(cid, pid)
		if term.checkInDB():
			log.warning('try to regist terminal which already exists in db.')
			return
		term.writeToDB()

	# 向数据库注册停车场
	def regist_carpark(self, pid, stot, scnt):
		park = models.CarPark(pid, stot, scnt)
		if park.checkInDB():
			log.warning('try to regist CarPark which already exists in db.')
			return
		park.writeToDB()

	def process_event(self, hid, tag, data):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if client.hid != hid: return -3

		raw_data = data.asdict()
		if isinstance(data, protoc.PkgHeart):
			pkg = models.TerminalHeart(raw_data['cid'], raw_data['ctype'], raw_data['iostat'], \
				raw_data['scnt'], raw_data['stot'], raw_data['stat'], raw_data['counter'])
			pkg.writeToDB()
		elif isinstance(data, protoc.PkgRep):
			pkg = models.ParkLog(raw_data['cid'], raw_data['scnt'])
			pkg.writeToDB()
