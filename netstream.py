#coding: gbk
import gvars
import errno
import socket
import log
import protoc

#======================================================================
# netstream - basic tcp stream
#======================================================================
class netstream(object):
	def __init__(self):
		self.sock = None
		self.send_buf = ''
		self.recv_buf = ''
		self.state = gvars.NET_STATE_STOP
		self.errd = ( errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK )
		self.conn = ( errno.EISCONN, 10057, 10053 )
		self.errc = 0
		self.headmask = False


	#connect the remote server
	def connect(self, address, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.sock.connect_ex((address, port))
		self.state = gvars.NET_STATE_CONNECTING
		self.send_buf = ''
		self.recv_buf = ''
		self.errc = 0

		return 0

	#close connection
	def close(self):
		self.state = gvars.NET_STATE_STOP
		if not self.sock:
			return 0
		try:
			self.sock.close()
		except:
			pass
		self.sock = None
		return 0

	#assign a socket to netstream
	def assign(self, sock):
		self.close()
		self.sock = sock
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.state = gvars.NET_STATE_ESTABLISHED
		self.send_buf = ''
		self.recv_buf = ''
		return 0

	# update 
	def process(self):
		if self.state == gvars.NET_STATE_STOP:
			return 0
		if self.state == gvars.NET_STATE_CONNECTING:
			self.__try_connect()
		if self.state == gvars.NET_STATE_ESTABLISHED:
			self.__try_recv()
		if self.state == gvars.NET_STATE_ESTABLISHED:
			self.__try_send()
		return 0

	def __try_connect(self):
		if (self.state == gvars.NET_STATE_ESTABLISHED):
			return 1
		if (self.state != gvars.NET_STATE_CONNECTING):
			return -1
		try:
			self.sock.recv(0)
		except socket.error, (code, strerror):
			if code in self.conn:
				return 0
			if code in self.errd:
				self.state = gvars.NET_STATE_ESTABLISHED
				self.recv_buf = ''
				log.info('connected to server.')
				return 1
			log.error('connect to server failed. error: ' + str(strerror))
			self.close()
			return -1
		log.info('connected to server.')
		self.state = gvars.NET_STATE_ESTABLISHED
		return 1

	# send data from send_buf until block (reached system buffer limits)
	def __try_send(self):
		wsize = 0
		if(len(self.send_buf) == 0):
			return 0
		try:
			wsize = self.sock.send(self.send_buf)
		except socket.error, (code, strerror):
			if not code in self.errd:
				log.error('send data to socket failed, error:' + str(strerror))
				self.errc = code
				self.close()
				return -1
		log.debug('send data: %d bytes' % wsize)
		self.send_buf = self.send_buf[wsize:]
		return wsize

	# try to receive all data to recv_buf
	def __try_recv(self):
		rdata = ''
		while 1:
			text = ''
			try:
				text = self.sock.recv(1024)
				if not text:
					return 0
			except socket.error, (code, strerror):
				if not code in self.errd:
					log.error('recv data from socket failed, error: '+str(strerror))
					self.errc = code
					self.close()
					return -1
			if text == '':
				break
			rdata  = rdata + text
		# log.debug('recv data: %s'%rdata)
		self.recv_buf = self.recv_buf + rdata
		return len(rdata)

	# peek data from recv_buf (read without delete it)
	def __peek_raw(self, size):
		self.process()
		if len(self.recv_buf) == 0:
			return ''
		if size > len(self.recv_buf):
			size = len(self.recv_buf)
		rdata = self.recv_buf[0:size]
		return rdata

	def __peek_protoc(self):
		self.process()
		if len(self.recv_buf) == 0:
			return None
		check_result = protoc.check_recv(self.recv_buf)
		#log.debug('peek protoc:%s'%self.recv_buf)
		return check_result

	# read data from recv_buf (read and delete it from recv_buf)
	def __recv_raw(self, size):
		rdata = self.__peek_raw(size)
		size = len(rdata)
		self.recv_buf = self.recv_buf[size:]
		return rdata

	# append data to send_buf then try to send it out (__try_send)
	def __send_raw(self, data):
		self.send_buf = self.send_buf + data
		self.process()
		return 0

	# return state
	def status(self):
		return self.state
	
	# error code
	def error(self):
		return self.errc

	def recv(self):
		peek_result = self.__peek_protoc()
		if peek_result:
			data, pkgClass = peek_result[0], peek_result[1]
			rsize = pkgClass.raw_size()
			self.recv_buf = self.recv_buf[rsize:]
			# log.info('recv obj: ' + str(data))
			pkg = pkgClass(data)
			return pkg

	def send_report(self, report):
		pkg = protoc.PkgRep(report)
		data = pkg.serialize()
		self.__send_raw(data)

	def send_ack(self, ack):
		pkg = protoc.PkgSum(ack)
		data = pkg.serialize()
		self.__send_raw(data)

	# set tcp nodelay flag
	def nodelay(self, nodelay = 0):
		if not 'TCP_NODELAY' in socket.__dict__:
			return -1
		if self.state != 2:
			return -2
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, nodelay)
		return 0
