#coding:gbk
import socket
import time
import netstream2 as netstream
import log
import gvars
import protoc
import models
import asyncore
import config
from datetime import datetime, timedelta

RESET_TIME = config.get('service', 'reset_time')

#车场类，用于管理车场id和终端id的对应关系
class netpark(object):
	def __init__(self, tid, typ):
		self.tid = tid
		self.typ = typ
		self.cnt_base = 0
		self.tdids = {}

	def active_child(self, pos, did):
		active = time.time()
		self.tdids[pos] = (did, active)

	def deactive_child(self, pos):
		self.tdids[pos] = None

	def reset_cnt_base(self, base):
		self.cnt_base = base

class nethost(asyncore.dispatcher):
	def __init__(self):
		asyncore.dispatcher.__init__(self)
		self.host = 0
		self.state = gvars.NET_STATE_STOP
		self.clients = []
		self.parks = {}
		self.count = 0
		self.index = 1
		#self.queue = []
		self.timeout = 120.0
		self.timeslap = long(time.time()*1000)
		self.period = 0

		self.last_scheduled_time = None
		reset_time = datetime.strptime(RESET_TIME, '%H:%M:%S')
		now = datetime.now()
		self.next_schedule_time = datetime(now.year,now.month,now.day, reset_time.hour, reset_time.minute, reset_time.second)
		if self.next_schedule_time - now < timedelta():
			self.next_schedule_time = self.next_schedule_time + timedelta(days=1)

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
			self.timer.cancel()
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
			#self.queue.append((gvars.NET_NEW, hid, 0, repr(client.peername)))
			log.info('client connected, peer: %s, pos: %d, index: %d'%(client.peername, pos, self.index-1))

	def on_client_recv(self, client):
		current = time.time()
		client.active = current
		data = client.read_pkg()
		if data is None:
			return
		#log.debug('recv pkg from client: %s, data: %s'%(client.peername, data))
		#self.queue.append((gvars.NET_DATA, client.hid, client.tag, data))
		self.process_event(client.hid, client.tag, data)

		self.checkScheduledProc()

	def on_client_close(self, client):
		hid, tag = client.hid, client.tag
		pos = hid & 0xffff
		#self.queue.append((gvars.NET_LEAVE, hid, tag, ''))
		self.clients[pos] = None
		log.info('client leave, peer: %s, pos: %d'%(client.peername, pos))

		if client.park_id:
			park = self.parks.get(client.park_id, None)
			if park:
				park.deactive_child(pos)

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
		if (pos < 0) or (pos >= len(self.clients)):
			log.error('process event error, invalid client position: %d'%pos)
			return -1
		client = self.clients[pos]
		if client == None:
			log.error('process event error, invalid client handle: None')
			return -2
		if client.hid != hid:
			log.error('process event error, hid mismatch, client: %d, hid: %d'%(client.hid, hid))
			return -3

		if not self.parks.has_key(data.cid):
			park = netpark(data.cid, data.ctype)
			self.parks[data.cid] = park
		park = self.parks[data.cid]
		park.active_child(pos, data.did)

		# raw_data = data.asdict()
		# if isinstance(data, protoc.PkgHeart):
		# 	pkg = models.TerminalHeart(data.cid, raw_data['stat'])
		# 	pkg.writeToDB()
		if isinstance(data, protoc.PkgManual):
			#手工设置当前车位数，重置基数
			park.reset_cnt_base(data.scnt)

			pkg = models.ParkLog(data.cid, data.did, data.ctype, data.scnt, data.sinc, data.sdec, data.stat, reset_base=models.ParkLog.RB_MANUAL)
			pkg.writeToDB()

			park = self.parks.get(data.cid)
			if park:
				for cpos, cinfo in park.tdids.iteritems():
					pkgSum = protoc.PkgSum({})
					pkgSum.cid = pkg.tid
					pkgSum.did = cinfo[0]
					pkgSum.scnt = pkg.curr
					pkgSum.stot = data.stot
					if pkgSum.scnt < 0:
						pkgSum.scnt = 0
					door_client = self.clients[cpos]
					if door_client:
						door_client.send_ack(pkgSum)
					log.debug('send manual set. tid: 0x%0X, did: %d, curr: %d, tot: %d' %(pkgSum.cid, pkgSum.did, pkgSum.scnt, pkgSum.stot))

		elif isinstance(data, protoc.PkgRep):
			client.status = data.stat
			client.park_id = data.cid
			client.door_id = data.did
			if client.status == 0x01:		#标识复位成功
				client.reset_counter = 0
			else:
				client.sinc = data.sinc
				client.sdec = data.sdec

				# (self, tid, tdid, typ, curr, sinc, sdec, stat, counter):
				pkgIdent = models.ParkLogIdentity(data.cid, data.did, data.ctype, data.scnt, data.sinc, data.sdec, data.stat, data.counter)
				pkgIdent.writeToDB()

				# (self, tid, tdid, typ, curr, sinc, sdec, stat):
				pkg = models.ParkLog(data.cid, data.did, data.ctype, data.scnt, data.sinc, data.sdec, data.stat)

				if data.ctype > 0x01:    #多门
					park = self.parks.get(data.cid)
					if park:
						curr = pkg.queryBase()
						for cpos, cinfo in park.tdids.iteritems():
							door_client = self.clients[cpos]
							if door_client:
								curr = curr + door_client.sinc - door_client.sdec
						pkg.resetCurrent(curr)
						pkg.writeToDB()
						
						for cpos, cinfo in park.tdids.iteritems():
							door_client = self.clients[cpos]
							if door_client:
								pkgSum = protoc.PkgSum({})
								pkgSum.cid = pkg.tid
								pkgSum.did = cinfo[0]
								pkgSum.scnt = pkg.curr
								pkgSum.stot = data.stot
								if pkgSum.scnt < 0:
									pkgSum.scnt = 0
								log.debug('send to door client. tid: 0x%0X, did: %d, curr: %d, tot: %d'%(pkg.tid, cinfo[0], pkg.curr, data.stot))
								door_client.send_ack(pkgSum)
				else:
					pkg.writeToDB()

		log.debug('data processed. tid: 0x%0X, did: %d, curr: %d, sinc: %d, sdec: %d, stat: %d'%(data.cid, data.did, data.scnt, data.sinc, data.sdec, data.stat))



	def checkScheduledProc(self):
		now = datetime.now()
		#检查所有客户端如果需要发送重置，则发送(给半个小时的时间处理)
		if self.last_scheduled_time != None and now - self.last_scheduled_time <= timedelta(minutes=30):
			pkg = protoc.PkgReset({})
			for i in xrange(len(self.clients)):
				client = self.clients[i]
				if client != None and client.reset_counter > 0:
					if client.park_id and client.door_id:
						log.debug('send reset command to client. tid: 0x%0X, did: %d'%(client.park_id, client.door_id))
					client.send_ack(pkg)
					client.reset_counter -= 1

		#凌晨3点开始重置终端
		delta = self.next_schedule_time - now
		if delta <= timedelta():
			#重设基数
			for tid, park in self.parks.iteritems():
				pkg = models.ParkLog(park.tid, 0, park.typ, 0, 0, 0, 0, reset_base=models.ParkLog.RB_AUTO)
				pkg.resetCurrent(None)	#自动从数据库读取当前值
				park.reset_cnt_base(pkg.curr)
				pkg.writeToDB()
				log.info('auto reset park base. tid: 0x%0X, base: %d' %(tid, pkg.curr))
			for i in xrange(len(self.clients)):
				client = self.clients[i]
				if client != None:
					client.reset_counter = 10  #重置10次
			self.last_scheduled_time = now
			self.next_schedule_time = now + timedelta(days=1)

