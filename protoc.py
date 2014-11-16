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
	FMT = '!HB4BBB4BB2B4BB2BH'
	HEADER_FMT = '!HB'
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', \
		'hdr ftype cid1 cid2 cid3 cid4 ctype did scnt1 scnt2 scnt3 scnt4 iostat dcnt1 dcnt2 stot1 stot2 stot3 stot4 stat counter1 counter2 fend')
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
	def iostat(self):
		return self.data['iostat']
	@iostat.setter
	def iostat(self, v):
		self.data['iostat'] = v

	@property
	def stat(self):
		return self.data['stat']
	@stat.setter
	def stat(self, v):
		self.data['stat'] = v

	@property
	def scnt(self):
		return self.data['scnt1']*1000+self.data['scnt2']*100+self.data['scnt3']*10+self.data['scnt4']
	@scnt.setter
	def scnt(self, v):
		self.data['scnt1'] = int(v/1000)
		self.data['scnt2'] = int((v%1000)/100)
		self.data['scnt3'] = int((v%100)/10)
		self.data['scnt4'] = v%10

	@property
	def stot(self):
		return self.data['stot1']*1000+self.data['stot2']*100+self.data['stot3']*10+self.data['stot4']
	@stot.setter
	def stot(self, v):
		self.data['stot1'] = int(v/1000)
		self.data['stot2'] = int((v%1000)/100)
		self.data['stot3'] = int((v%100)/10)
		self.data['stot4'] = v%10

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

	def __str__(self):
		return 'PkgRep - id:0x%04X, did: 0x%01X, type:0x%02X, cnt:0x%04X, io:0x%02X, dcnt: 0x%02X, tot:0x%04X, stat:0x%02X, loop:0x%02X'% ( \
				self.cid, self.did, self.ctype, \
				self.scnt, \
				self.iostat, \
				self.dcnt, self.stot,\
				self.stat, self.counter )

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

class PkgManual(PkgRep):
	FRAME_TYPE = 0x55

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
	FMT = '!HB4BB4B4BBBH'
	HEADER_FMT = '!HB'
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid1 cid2 cid3 cid4 did scnt1 scnt2 scnt3 scnt4 stot1 stot2 stot3 stot4 counter hour fend')
	def __init__(self, data):
		self.data = {
			'hdr': 		HEAD_S2C,
			'ftype':	self.FRAME_TYPE,
			'counter':  time.localtime().tm_min,
			'hour': 	time.localtime().tm_hour,
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
	def did(self):
		return self.data['did']

	@did.setter
	def did(self, v):
		self.data['did'] = v

	@property
	def scnt(self):
		return self.data['scnt1']*1000+self.data['scnt2']*100+self.data['scnt3']*10+self.data['scnt4']
	@scnt.setter
	def scnt(self, v):
		self.data['scnt1'] = int(v/1000)
		self.data['scnt2'] = int((v%1000)/100)
		self.data['scnt3'] = int((v%100)/10)
		self.data['scnt4'] = v%10

	@property
	def stot(self):
		return self.data['stot1']*1000+self.data['stot2']*100+self.data['stot3']*10+self.data['stot4']
	@stot.setter
	def stot(self, v):
		self.data['stot1'] = int(v/1000)
		self.data['stot2'] = int((v%1000)/100)
		self.data['stot3'] = int((v%100)/10)
		self.data['stot4'] = v%10
	
	@property
	def counter(self):
		return self.data['counter']
	@counter.setter
	def counter(self, v):
		self.data['counter'] = v

	def __str__(self):
		return 'PkgSum - id:0x%04X, did: 0x%01X, cnt:0x%X(%d), tot:0x%X(%d), counter:0x%01X'% ( \
				self.cid, self.did, \
				self.scnt, self.scnt,\
				self.stot, self.stot,\
				self.counter )

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

