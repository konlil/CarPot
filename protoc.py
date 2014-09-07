#coding: gbk
import struct
from collections import namedtuple

#==========================
# format of headers and end
#============================
HEAD_C2S = 0x6868
HEAD_S2C = 0x5867
END_FRAME = 0x0D0A

#===========================
# factory method
#===========================
def check_recv(buf):
	classes = [PkgRep, PkgHeart]
	for c in classes:
		obj = c.check(buf)
		if obj:
			return (obj, c)
	return None

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
		fsize = struct.calcsize(cls.FMT)
		hsize = struct.calcsize(cls.HEADER_FMT)
		if len(buf) < fsize:
			return False
		header_hdr, header_type = struct.unpack(cls.HEADER_FMT, buf[:hsize])
		#print '[check]', cls, header_hdr, HEAD_C2S, header_type, cls.FRAME_TYPE
		if header_hdr == HEAD_C2S and header_type == cls.FRAME_TYPE:
			obj = cls.unserialize(buf[:fsize])
			if obj['fend'] == END_FRAME:
				return obj
		return None

	@classmethod
	def unserialize(cls, buf):
		obj = cls.TUPLE_TYPE._make(struct.unpack(cls.FMT, buf))
		return cls.TUPLE_TYPE._asdict(obj)

#主动包
class PkgRep(PkgC2S):
	FRAME_TYPE = 0x55
	FRAME_SIZE = 15
	FMT = '!HBHBHBHBBH'
	HEADER_FMT = '!HB'
	HEADER_SIZE = 3
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid ctype scnt iostat stot stat counter fend')
	def __init__(self, data):
		super(PkgRep, self).__init__()
		self.data = {
			'hdr': 		HEAD_C2S,
			'ftype':	self.FRAME_TYPE,
			'fend':		END_FRAME,
		}
		self.data.update(data)

	# def serialize(self):
	# 	tmp = []
	# 	for item in self.TUPLE_TYPE._fields:
	# 		if item == 'hdr':
	# 			tmp.append(HEAD_C2S)
	# 		elif item == 'ftype':
	# 			tmp.append(self.FRAME_TYPE)
	# 		elif item == 'fend':
	# 			tmp.append(END_FRAME)
	# 		else:
	# 			tmp.append(self.data[item])
	# 	return struct.pack(self.FMT, *tmp)

#心跳包
class PkgHeart(PkgC2S):
	FRAME_TYPE = 0xAA
	FRAME_SIZE = 15
	FMT = '!HBHBHBHBBH'
	HEADER_FMT = '!HB'
	HEADER_SIZE = 3
	TUPLE_TYPE = namedtuple('TUPLE_TYPE', 'hdr ftype cid ctype scnt iostat stot stat counter fend')
	def __init__(self, data):
		super(PkgHeart, self).__init__()
		self.data = {
			'hdr': 		HEAD_C2S,
			'ftype':	self.FRAME_TYPE,
			'fend':		END_FRAME,
		}
		self.data.update(data)
		self.data['iostat'] = 0x00

	# def serialize(self):
	# 	tmp = []
	# 	for item in self.TUPLE_TYPE._fields:
	# 		if item == 'hdr':
	# 			tmp.append(HEAD_C2S)
	# 		elif item == 'ftype':
	# 			tmp.append(self.FRAME_TYPE)
	# 		elif item == 'fend':
	# 			tmp.append(END_FRAME)
	# 		else:
	# 			tmp.append(self.data[item])
	# 	return struct.pack(self.FMT, *tmp)

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

