#coding: gbk
import struct
from collections import namedtuple

#==========================
# format of headers and end
#============================
HEAD_C2S = 0x6868
HEAD_S2C = 0x5867
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
	classes = [PkgRep, PkgHeart]
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
	FRAME_TYPE = 0x55
	FMT = '!HB4BB3BB3BB2BH'
	HEADER_FMT = '!HB'
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid1 cid2 cid3 cid4 ctype scnt1 scnt2 scnt3 iostat stot1 stot2 stot3 stat counter1 counter2 fend')
	def __init__(self, data):
		super(PkgRep, self).__init__()
		self.data = {
			'hdr': 		HEAD_C2S,
			'ftype':	self.FRAME_TYPE,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	@property
	def cid(self):
		return self.data['cid1']*1000+self.data['cid2']*100+self.data['cid3']*10+self.data['cid4']
	@cid.setter
	def cid(self, v):
		self.data['cid1'] = int(v/1000)
		self.data['cid2'] = int((v%1000)/100)
		self.data['cid3'] = int((v%100)/10)
		self.data['cid4'] = v%10

	@property
	def scnt(self):
		return self.data['scnt1']*100+self.data['scnt2']*10+self.data['scnt3']
	@scnt.setter
	def scnt(self, v):
		self.data['scnt1'] = int(v/100)
		self.data['scnt2'] = int((v%100)/10)
		self.data['scnt3'] = v%10

	@property
	def stot(self):
		return self.data['stot1']*100+self.data['stot2']*10+self.data['stot3']
	@stot.setter
	def stot(self, v):
		self.data['stot1'] = int(v/100)
		self.data['stot2'] = int((v%100)/10)
		self.data['stot3'] = v%10
	
	@property
	def counter(self):
		return self.data['counter1']*10+self.data['counter2']
	@counter.setter
	def counter(self, v):
		self.data['counter1'] = int(v/10)
		self.data['counter2'] = v%10


	def __str__(self):
		return 'PkgRep - id:0x%04X, type:0x%02X, cnt:0x%04X, io:0x%02X, tot:0x%04X, stat:0x%02X, loop:0x%02X'% ( \
				self.cid, self.data['ctype'], \
				self.scnt, \
				self.data['iostat'], \
				self.stot, \
				self.data['stat'], self.counter )

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

#心跳包
class PkgHeart(PkgC2S):
	FRAME_TYPE = 0xAA
	FMT = '!HB4BB3BB3BB2BH'
	HEADER_FMT = '!HB'
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid1 cid2 cid3 cid4 ctype scnt1 scnt2 scnt3 iostat stot1 stot2 stot3 stat counter1 counter2 fend')
	def __init__(self, data):
		super(PkgHeart, self).__init__()
		self.data = {
			'hdr': 		HEAD_C2S,
			'ftype':	self.FRAME_TYPE,
			'fend':		END_FRAME,
		}
		self.data.update(data)
		self.data['iostat'] = 0x00

	@property
	def cid(self):
		return self.data['cid1']*1000+self.data['cid2']*100+self.data['cid3']*10+self.data['cid4']
	@cid.setter
	def cid(self, v):
		self.data['cid1'] = int(v/1000)
		self.data['cid2'] = int((v%1000)/100)
		self.data['cid3'] = int((v%100)/10)
		self.data['cid4'] = v%10

	@property
	def scnt(self):
		return self.data['scnt1']*100+self.data['scnt2']*10+self.data['scnt3']
	@scnt.setter
	def scnt(self, v):
		self.data['scnt1'] = int(v/100)
		self.data['scnt2'] = int((v%100)/10)
		self.data['scnt3'] = v%10

	@property
	def stot(self):
		return self.data['stot1']*100+self.data['stot2']*10+self.data['stot3']
	@stot.setter
	def stot(self, v):
		self.data['stot1'] = int(v/100)
		self.data['stot2'] = int((v%100)/10)
		self.data['stot3'] = v%10
	
	@property
	def counter(self):
		return self.data['counter1']*10+self.data['counter2']
	@counter.setter
	def counter(self, v):
		self.data['counter1'] = int(v/10)
		self.data['counter2'] = v%10

	def __str__(self):
		return 'PkgHeart - id:0x%04X, type:0x%02X, cnt:0x%04X, io:0x%02X, tot:0x%04X, stat:0x%02X, loop:0x%02X'% ( \
				self.cid, self.data['ctype'], \
				self.scnt, \
				self.data['iostat'], \
				self.stot, \
				self.data['stat'], self.counter)

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

class PkgSum(object):
	FRAME_TYPE = 0xDD
	FRAME_SIZE = 13
	FMT = '!HBHBHHBBH'
	HEADER_FMT = '!HB'
	HEADER_SIZE = 3
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid ctype scnt stot counter cksum fend')
	def __init__(self, data):
		self.data = {
			'hdr': 		HEAD_S2C,
			'ftype':	self.FRAME_TYPE,
			'counter':	0,
			'cksum':	0,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	def serialize(self):
		tmp = []
		for item in self.TUPLE_TYPE._fields:
			tmp.append(self.data[item])
		return struct.pack(self.FMT, *tmp)

	# def unserialize(self):
	# 	pass

class PkgCmd(object):
	FRAME_TYPE = 0xBB
	FRAME_SIZE = 17
	FMT = '!HBHBIHHBH'
	HEADER_FMT = '!HB'
	HEADER_SIZE = 3
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid ctype ip port stot cksum fend')
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

