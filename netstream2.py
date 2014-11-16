#coding: gbk
import gvars
import errno
import socket
import asyncore
import log
import protoc

def hex_dump(buf):
	tmp = ''
	for i in xrange(len(buf)):
		tmp += '%02X '%ord(buf[i])
	return tmp

#======================================================================
# netstream - basic tcp stream
#======================================================================
class netstream(asyncore.dispatcher):
	def __init__(self):
		asyncore.dispatcher.__init__(self)
		self.send_buf = ''
		self.recv_buf = ''
		self.state = gvars.NET_STATE_STOP
		self.on_recv = None
		self.on_close = None

	#connect the remote server
	def connect_ex(self, address, port):
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((address, port))
		self.state = gvars.NET_STATE_CONNECTING
		self.send_buf = ''
		self.recv_buf = ''
		return 0

	def handle_close(self):
		self.close()
		self.state = gvars.NET_STATE_STOP
		if self.on_close:
			self.on_close(self)

	#assign a socket to netstream
	def assign(self, sock):
		sock.setblocking(0)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.set_socket(sock)
		self.state = gvars.NET_STATE_ESTABLISHED
		self.send_buf = ''
		self.recv_buf = ''
		return 0

	def handle_connect(self):
		self.state = gvars.NET_STATE_ESTABLISHED

	def handle_read(self):
		rdata = self.recv(1024)
		log.debug('from %s: %s'%(self, hex_dump(rdata)))
		self.recv_buf = self.recv_buf + rdata
		if self.on_recv:
			self.on_recv(self)

	def handle_write(self):
		# print 'handle_write', self.send_buf
		wsize = self.send(self.send_buf)
		self.send_buf = self.send_buf[wsize:]

	def writable(self):
		return len(self.send_buf) > 0

	# peek data from recv_buf (read without delete it)
	def __peek_raw(self, size):
		if len(self.recv_buf) == 0:
			return ''
		if size > len(self.recv_buf):
			size = len(self.recv_buf)
		rdata = self.recv_buf[0:size]
		return rdata

	def __peek_protoc(self):
		if len(self.recv_buf) == 0:
			return None

		check_result, proto_class, err = protoc.check_recv(self.recv_buf)
		# wait for un-complete package
		if err in [protoc.PKG_ERR_NOT_READY, protoc.PKG_ERR_TOO_SHORT]:
			log.debug('package un-complete, wait for it')
			return None

		bad_pkg_bytes = 0
		while err != protoc.PKG_OK and len(self.recv_buf) > 0:
			bad_pkg_bytes += 1
			self.recv_buf = self.recv_buf[1:]
			check_result, proto_class, err = protoc.check_recv(self.recv_buf)

		if bad_pkg_bytes:
			log.critical('detect bad package, ignored %d bytes' % bad_pkg_bytes)

		if err == protoc.PKG_OK:
			# log.debug('peek package:: %s, %s' % (str(check_result), str(proto_class)))
			return (check_result, proto_class)
		return None

	# read data from recv_buf (read and delete it from recv_buf)
	def __recv_raw(self, size):
		rdata = self.__peek_raw(size)
		size = len(rdata)
		self.recv_buf = self.recv_buf[size:]
		return rdata

	# append data to send_buf then try to send it out (__try_send)
	def __send_raw(self, data):
		self.send_buf = self.send_buf + data
		return 0

	# return state
	def status(self):
		return self.state

	# error code
	def error(self):
		return self.errc

	def read_pkg(self):
		# print 'read_pkg', self.recv_buf, len(self.recv_buf)
		peek_result = self.__peek_protoc()
		if peek_result:
			data, pkgClass = peek_result[0], peek_result[1]
			rsize = pkgClass.raw_size()
			self.recv_buf = self.recv_buf[rsize:]
			pkg = pkgClass(data)
			return pkg

	def send_report(self, report):
		pkg = protoc.PkgRep(report)
		data = pkg.serialize()
		self.__send_raw(data)

	def send_ack(self, pkg):
		data = pkg.serialize()
		self.__send_raw(data)
