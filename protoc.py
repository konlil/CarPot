#coding: gbk
import struct
import time
from collections import namedtuple

#==========================
# format of headers and end
#============================
HEAD_C2S = 0x6868
HEAD_S2C = 0x7E7E
END_FRAME = 0x0D0A

PKG_OK = 0
PKG_ERR_TOO_SHORT = 1
PKG_ERR_INVALID_HEADER = 2
PKG_ERR_INVALID_END = 3
PKG_ERR_NOT_READY = 4
PKG_ERR_UNKNOWN = 5
PKG_ERR_INVALID_FRAMETYPE = 6
#===========================
# factory method
#===========================
def hex_dump(buf):
	tmp = ''
	for i in xrange(len(buf)):
		tmp += '%02X '%ord(buf[i])
	return tmp
def check_recv(buf):
	# classes = [PkgRep, PkgHeart]
	classes = [PkgRep, PkgManual]
	err = PKG_ERR_UNKNOWN
	err = PKG_ERR_UNKNOWN
	for c in classes:
		obj, err = c.check(buf)
		if err == PKG_OK:
			return (obj, c, PKG_OK)
		elif err == PKG_ERR_NOT_READY:		#真的是太短了
			return (None, None, err)
		elif err in [PKG_ERR_INVALID_FRAMETYPE, PKG_ERR_TOO_SHORT]:
			continue
		else:
		#	pkg = ''
		#	for i in xrange(len(buf)):
		#		pkg += '%02X '%(ord(buf[i]))
		#	log.error('found invalid package, err: %d, pkg: %s'%(err, pkg))
			return (None, None, err)
	return (None, None, err)

def format_tuple_def(proto):
	rtn = []
	for v in proto:
		if v[1] > 1:
			for i in xrange(v[1]):
				rtn.append('%s%d'%(v[0], i+1))
		elif v[1] == 1:
			rtn.append(v[0])
		else:
			pass
	return ' '.join(rtn)

def getter_4_bytes(pkg, k):
	return pkg.data['%s1'%k]*1000+pkg.data['%s2'%k]*100+pkg.data['%s3'%k]*10+pkg.data['%s4'%k]

def setter_4_bytes(pkg, k, v):
	pkg.data['%s1'%k] = int(v/1000)
	pkg.data['%s2'%k] = int((v%1000)/100)
	pkg.data['%s3'%k] = int((v%100)/10)
	pkg.data['%s4'%k] = v%10

class PkgC2S(object):
	FRAME_TYPE = None
	FRAME_SIZE = None
	FMT = None
	HEADER_FMT = None
	HEADER_SIZE = None
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'empty')
	def __init__(self):
		self.data = {}

	def asdict(self):
		return self.data

	@classmethod
	def raw_size(cls):
		return struct.calcsize(cls.FMT)

	@classmethod
	def check(cls, buf):
		hsize = struct.calcsize(cls.HEADER_FMT)
		if len(buf) < hsize:
			return (None, PKG_ERR_NOT_READY)

		header_hdr, header_type = struct.unpack(cls.HEADER_FMT, buf[:hsize])
		if header_hdr != HEAD_C2S:
			return (None, PKG_ERR_INVALID_HEADER)

		if header_type != cls.FRAME_TYPE:
			return (None, PKG_ERR_INVALID_FRAMETYPE)

		fsize = struct.calcsize(cls.FMT)
		if len(buf) < fsize:
			return (None, PKG_ERR_TOO_SHORT)

		obj = cls.unserialize(buf[:fsize])
		if obj['fend'] == END_FRAME:
			return (obj, PKG_OK)
		else:
			return (None, PKG_ERR_INVALID_END)

	@classmethod
	def unserialize(cls, buf):
		unpacked = struct.unpack(cls.FMT, buf)
		obj = cls.TUPLE_TYPE._make(unpacked)
		return cls.TUPLE_TYPE._asdict(obj)
#主动包
class PkgRep(PkgC2S):
	FRAME_TYPE = 0xAA
	# FMT = '!HB4BBB4BB2B4BB2BH'
	# HEADER_FMT = '!HB'
	PROTOC_DEF = (
		('hdr', 	1,	'H'),		#帧头
		('ftype', 	1,  'B'),		#帧类型
		('cid', 	4,  'B'),		#车场ID
		('ctype',	1, 	'B'),		#车场类型
		('did',		1,  'B'),		#子门编号
		('scnt',	4,  'B'),		#当前剩余车位
		('stot',	4, 	'B'),		#总车位数
		('sdec',	4, 	'B'),		#车辆进数目
		('sinc',	4, 	'B'),		#车辆出数目
		('stat',	1,	'B'),		#工作状态
		('counter', 2, 	'B'),		#帧计数器
		('fend',	1,	'H'),		#帧结尾
	)
	FMT = '!' + ''.join(['%d%s'%(v[1],v[2]) for v in PROTOC_DEF])
	HEADER_FMT = '!' + ''.join([ '%d%s'%(v[1],v[2]) for v in PROTOC_DEF[:2] ])
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', format_tuple_def(PROTOC_DEF))

	def __init__(self, data):
		super(PkgRep, self).__init__()
		self.data = {
			'hdr': 		HEAD_C2S,
			'ftype':	self.FRAME_TYPE,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	def getter_4_bytes(self, k):
		return self.data['%s1'%k]*1000+self.data['%s2'%k]*100+self.data['%s3'%k]*10+self.data['%s4'%k]

	def setter_4_bytes(self, k, v):
		self.data['%s1'%k] = int(v/1000)
		self.data['%s2'%k] = int((v%1000)/100)
		self.data['%s3'%k] = int((v%100)/10)
		self.data['%s4'%k] = v%10

	@property
	def cid(self):
		return self.getter_4_bytes('cid')
	@cid.setter
	def cid(self, v):
		self.setter_4_bytes('cid', v)

	@property
	def did(self):
		return self.data['did']

	@did.setter
	def did(self, v):
		self.data['did'] = v

	@property
	def ctype(self):
		return self.data['ctype']
	@ctype.setter
	def ctype(self, v):
		self.data['ctype'] = v

	@property 
	def sinc(self):
		return self.getter_4_bytes('sinc')
	@sinc.setter
	def sinc(self, v):
		self.setter_4_bytes('sinc', v)

	@property 
	def sdec(self):
		return self.getter_4_bytes('sdec')

	@sdec.setter
	def sdec(self, v):
		self.setter_4_bytes('sdec', v)
		
	@property
	def stat(self):
		return self.data['stat']
	@stat.setter
	def stat(self, v):
		self.data['stat'] = v

	@property
	def scnt(self):
		return getter_4_bytes(self, 'scnt')
	@scnt.setter
	def scnt(self, v):
		setter_4_bytes(self, 'scnt', v)

	@property
	def stot(self):
		return getter_4_bytes(self, 'stot')
	@stot.setter
	def stot(self, v):
		setter_4_bytes(self, 'stot')

	@property
	def dcnt(self):
		return self.data['dcnt1']*10+self.data['dcnt2']
	@dcnt.setter
	def dcnt(self, v):
		self.data['dcnt1'] = int((v%100)/10)
		self.data['dcnt2'] = v%10 
	
	@property
	def counter(self):
		return self.data['counter1']*10+self.data['counter2']
	@counter.setter
	def counter(self, v):
		self.data['counter1'] = int(v/10)
		self.data['counter2'] = v%10

	def serialize(self):
		tmp = []
		for item in self.TUPLE_TYPE._fields:
			if item == 'hdr':
				tmp.append(HEAD_C2S)
			elif item == 'ftype':
				tmp.append(self.FRAME_TYPE)
			elif item == 'fend':
				tmp.append(END_FRAME)
			else:
				tmp.append(self.data[item])
		return struct.pack(self.FMT, *tmp)

#终端初始化或修正车场当前车位数，此时仅有当前剩余车位数有效
class PkgManual(PkgRep):
	FRAME_TYPE = 0x55

# #心跳包
# class PkgHeart(PkgC2S):
# 	FRAME_TYPE = 0xAA
# 	FMT = '!HB4BB3BB3BB2BH'
# 	HEADER_FMT = '!HB'
# 	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid1 cid2 cid3 cid4 ctype scnt1 scnt2 scnt3 iostat stot1 stot2 stot3 stat counter1 counter2 fend')
# 	def __init__(self, data):
# 		super(PkgHeart, self).__init__()
# 		self.data = {
# 			'hdr': 		HEAD_C2S,
# 			'ftype':	self.FRAME_TYPE,
# 			'fend':		END_FRAME,
# 		}
# 		self.data.update(data)
# 		self.data['iostat'] = 0x00

# 	@property
# 	def cid(self):
# 		return self.data['cid1']*1000+self.data['cid2']*100+self.data['cid3']*10+self.data['cid4']
# 	@cid.setter
# 	def cid(self, v):
# 		self.data['cid1'] = int(v/1000)
# 		self.data['cid2'] = int((v%1000)/100)
# 		self.data['cid3'] = int((v%100)/10)
# 		self.data['cid4'] = v%10

# 	@property
# 	def scnt(self):
# 		return self.data['scnt1']*100+self.data['scnt2']*10+self.data['scnt3']
# 	@scnt.setter
# 	def scnt(self, v):
# 		self.data['scnt1'] = int(v/100)
# 		self.data['scnt2'] = int((v%100)/10)
# 		self.data['scnt3'] = v%10

# 	@property
# 	def stot(self):
# 		return self.data['stot1']*100+self.data['stot2']*10+self.data['stot3']
# 	@stot.setter
# 	def stot(self, v):
# 		self.data['stot1'] = int(v/100)
# 		self.data['stot2'] = int((v%100)/10)
# 		self.data['stot3'] = v%10
	
# 	@property
# 	def counter(self):
# 		return self.data['counter1']*10+self.data['counter2']
# 	@counter.setter
# 	def counter(self, v):
# 		self.data['counter1'] = int(v/10)
# 		self.data['counter2'] = v%10

# 	def __str__(self):
# 		return 'PkgHeart - id:0x%04X, type:0x%02X, cnt:0x%04X, io:0x%02X, tot:0x%04X, stat:0x%02X, loop:0x%02X'% ( \
# 				self.cid, self.data['ctype'], \
# 				self.scnt, \
# 				self.data['iostat'], \
# 				self.stot, \
# 				self.data['stat'], self.counter)

# 	def serialize(self):
# 		tmp = []
# 		for item in self.TUPLE_TYPE._fields:
# 			if item == 'hdr':
# 				tmp.append(HEAD_C2S)
# 			elif item == 'ftype':
# 				tmp.append(self.FRAME_TYPE)
# 			elif item == 'fend':
# 				tmp.append(END_FRAME)
# 			else:
# 				tmp.append(self.data[item])
# 		return struct.pack(self.FMT, *tmp)

#服务器向多门终端发送剩余车位数
class PkgSum(object):
	FRAME_TYPE = 0xDD
	PROTOC_DEF = (
		('hdr', 	1,	'H'),		#帧头
		('ftype', 	1,  'B'),		#帧类型
		('cid', 	1,  'I'),		#车场ID
		('did',		1,  'B'),		#子门编号
		('scnt',	1,  'I'),		#当前剩余车位
		('stot',	1, 	'I'),		#车位总数
		('second',	1, 	'B'),		#帧发送当前时间的分钟部分
		('hour',	1, 	'B'),		#帧发送当前时间的小时部分
		('fend',	1,	'H'),		#帧结尾
	)
	FMT = '!' + ''.join(['%d%s'%(v[1],v[2]) for v in PROTOC_DEF])
	HEADER_FMT = '!' + ''.join([ '%d%s'%(v[1],v[2]) for v in PROTOC_DEF[:2] ])
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', format_tuple_def(PROTOC_DEF))

	def __init__(self, data):
		self.data = {
			'hdr': 		HEAD_S2C,
			'ftype':	self.FRAME_TYPE,
			'second':  time.localtime().tm_min,
			'hour': 	time.localtime().tm_hour,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	@property
	def cid(self):
		#return getter_4_bytes(self, 'cid')
		return self.data['cid']

	@cid.setter
	def cid(self, v):
		#setter_4_bytes(self, 'cid', v)
		self.data['cid'] = v

	@property
	def did(self):
		return self.data['did']

	@did.setter
	def did(self, v):
		self.data['did'] = v

	@property
	def scnt(self):
		# return getter_4_bytes(self, 'scnt')
		return self.data['scnt']

	@scnt.setter
	def scnt(self, v):
		# setter_4_bytes(self, 'scnt', v)
		self.data['scnt'] = v

	@property
	def stot(self):
		return self.data['stot']
		# return getter_4_bytes(self, 'stot')
	@stot.setter
	def stot(self, v):
		self.data['stot'] = v
		# setter_4_bytes(self, 'stot', v)
	
	@property
	def second(self):
		return self.data['second']
	@second.setter
	def second(self, v):
		self.data['second'] = v

	# def __str__(self):
	# 	return 'PkgSum - id:0x%04X, did: 0x%01X, cnt:0x%X(%d), tot:0x%X(%d), counter:0x%01X'% ( \
	# 			self.cid, self.did, \
	# 			self.scnt, self.scnt,\
	# 			self.stot, self.stot,\
	# 			self.counter )

	def serialize(self):
		tmp = []
		for item in self.TUPLE_TYPE._fields:
			if item == 'hdr':
				tmp.append(HEAD_S2C)
			elif item == 'ftype':
				tmp.append(self.FRAME_TYPE)
			elif item == 'fend':
				tmp.append(END_FRAME)
			else:
				tmp.append(self.data[item])
		return struct.pack(self.FMT, *tmp)

class PkgReset(object):
	FRAME_TYPE = 0x55
	PROTOC_DEF = (
		('hdr', 	1,	'H'),		#帧头
		('ftype', 	1,  'B'),		#帧类型
		('cid', 	1,  'I'),		#车场ID
		('did',		1,  'B'),		#子门编号
		('cmd',		1,  'B'),		#帧命令
		('counter',	1, 	'B'),		#剩余车位数
		('fend',	1,	'H'),		#帧结尾
	)
	FMT = '!' + ''.join(['%d%s'%(v[1],v[2]) for v in PROTOC_DEF])
	HEADER_FMT = '!' + ''.join([ '%d%s'%(v[1],v[2]) for v in PROTOC_DEF[:2] ])
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', format_tuple_def(PROTOC_DEF))

	def __init__(self, data):
		self.data = {
			'hdr': 		HEAD_S2C,
			'ftype':	self.FRAME_TYPE,
			'cid':		0,
			'did':		0,
			'cmd':		0,
			'counter':	0,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	def serialize(self):
		tmp = []
		for item in self.TUPLE_TYPE._fields:
			if item == 'hdr':
				tmp.append(HEAD_S2C)
			elif item == 'ftype':
				tmp.append(self.FRAME_TYPE)
			elif item == 'fend':
				tmp.append(END_FRAME)
			else:
				tmp.append(self.data[item])
		return struct.pack(self.FMT, *tmp)

class PkgCmd(object):
	FRAME_TYPE = 0xBB
	PROTOC_DEF = (
		('hdr', 	1,	'H'),		#帧头
		('ftype', 	1,  'B'),		#帧类型
		('cid', 	1,  'I'),		#车场ID
		('did',		1,  'B'),		#子门编号
		('ip',		1,  'I'),		#ip
		('scnt',	1, 	'I'),		#剩余车位数
		('stot',	1, 	'I'),		#车位总数
		('fend',	1,	'H'),		#帧结尾
	)
	FMT = '!' + ''.join(['%d%s'%(v[1],v[2]) for v in PROTOC_DEF])
	HEADER_FMT = '!' + ''.join([ '%d%s'%(v[1],v[2]) for v in PROTOC_DEF[:2] ])
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', format_tuple_def(PROTOC_DEF))

	def __init__(self, data):
		self.data = {
			'hdr': 		HEAD_S2C,
			'ftype':	self.FRAME_TYPE,
			'cksum':	0,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	def serialize(self):
		tmp = []
		for item in self.TUPLE_TYPE._fields:
			tmp.append(self.data[item])
		return struct.pack(self.FMT, *tmp)

