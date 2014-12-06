#coding: gbk
import db
import datetime
import log
import config

class Model(object):
	TABLE_DEF = {}
	tblname = None
	def __init__(self):
		pass

	@classmethod
	def checkTable(cls):
		if not cls.tblname:
			cls.tblname = cls.__name__

		if not db.obj.tableExists(cls.tblname):
			tabledesc = ''
			for k, v in cls.TABLE_DEF.iteritems():
				tabledesc += '%s %s,'%(k, v)
			tabledesc = tabledesc[:-1]  # remove the last comma
			db.obj.createTable(cls.tblname, tabledesc)
			db.obj.Commit()
			log.info('db: table %s created.'%cls.tblname)

class TerminalHeart(Model):
	TABLE_DEF = {
		"id": "int primary key",
		#"typ": "int NOT NULL",
		#"iostat":	"int NOT NULL",
		#"curr": "int NOT NULL",
		#"total": "int NOT NULL",
		"stat": "int NOT NULL",
		#"cnter": "int NOT NULL"
		'updateTime': "datetime",
	}
	tblname = 'HeartBeat'
	def __init__(self, tid, stat):
		super(TerminalHeart, self).__init__()
		self.tid = tid
		self.stat = stat

	def checkInDB(self):
		cmd = 'select count(*) from %s where id=%d;'%(self.tblname, self.tid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			return True
		else:
			return False

	def insertNewToDB(self):
		#cmd = 'insert into %s(id,typ,iostat,curr,total,stat,cnter) values(%d,%d,%d,%d,%d,%d,%d);'%( \
		#		self.tblname, self.tid, self.typ, self.io, self.curr, self.tot, self.stat, self.counter)
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = "insert into %s(id,stat,updateTime) values(%d,%d,'%s');"%( \
				self.tblname, self.tid, self.stat, now)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def updateToDB(self):
		#cmd = 'update %s set typ=%d,iostat=%d, curr=%d, total=%d,stat=%d,cnter=%d where id=%d;'%( \
		#	self.tblname, self.typ, self.io, self.curr, self.tot, self.stat, self.counter, self.tid)
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = "update %s set stat=%d,updateTime='%s' where id=%d;"%( \
			self.tblname, self.stat, now, self.tid)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def writeToDB(self):
		if self.checkInDB():
			self.updateToDB()
		else:
			self.insertNewToDB()

class ParkLogIdentity(Model):
	TABLE_DEF = {
		"id": "uniqueidentifier PRIMARY KEY NOT NULL DEFAULT newid()",
		"tid": "int NOT NULL",
		"tdid": "int NOT NULL",
		"typ": "int NOT NULL",
		"curr": "int NOT NULL",
		"sinc": "int NOT NULL",
		"sdec": "int NOT NULL",
		"stat": "int NOT NULL",
		"cnter": "int NOT NULL",
		'updateTime': "datetime",
	}
	tblname = 'park_LogUniqIdent5'
	err = 0
	def __init__(self, tid, tdid, typ, curr, sinc, sdec, stat, counter):
		super(ParkLogIdentity, self).__init__()
		self.tid = tid
		self.tdid = tdid
		self.typ = typ
		self.curr = curr
		self.sinc = sinc
		self.sdec = sdec
		self.stat = stat
		self.counter = counter

	def insertNewToDB(self):
		if self.err > 0:
			return
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = "insert into %s(tid, tdid, typ, curr, sinc, sdec, stat, cnter,updateTime) values(%d,%d,%d,%d,%d,%d,%d,%d,'%s');"%( \
				self.tblname, self.tid, self.tdid, self.typ, self.curr, self.sinc, self.sdec, self.stat, self.counter, now)
		#log.debug("insert logident: %s" % cmd)
		db.obj.Exec(cmd)
		db.obj.Commit()
	
	def writeToDB(self):
		if self.err > 0:
			return
		self.insertNewToDB()

class ParkLog(Model):
	RB_NONE = 0 	#������base
	RB_MANUAL = 1 	#�ֹ�����base
	RB_AUTO = 2 	#�Զ�����base

	TABLE_DEF = {
		"id": "int primary key",			#�ն�ID(ʵ�ʱ�ʾ����ID)
		"typ": "int NOT NULL",				#��������
		"curr": "int NOT NULL",				#��ǰʣ�೵λ��
		"stat": "int NOT NULL",				#����״̬
		"base": "int NOT NULL",				#��λ����
		'updateTime': "datetime",			#����ʱ��
	}
	tblname = 'park_Log5'
	err = 0
	def __init__(self, tid, tdid, typ, curr, sinc, sdec, stat, reset_base=0):
		super(ParkLog, self).__init__()
		self.tid = tid
		self.tdid = tdid
		self.typ = typ
		self.curr = curr
		self.sinc = sinc
		self.sdec = sdec
		self.stat = stat

		self.reset_base = reset_base
		if self.reset_base == self.RB_AUTO:
			self.curr = self.queryCurrent()		#�����ݿ��ȡ��ǰ��λ����Ϊ��ǰ����
		elif self.reset_base == self.RB_MANUAL:
			self.curr = curr
		else:
			if self.typ > 0x01:		#����
				last_curr = self.queryBase()
				self.curr = last_curr + self.sinc - self.sdec

	# @classmethod
	# def checkTable(cls):
	# 	if not db.obj.tableExists(cls.tblname):
	# 		cls.err = 1
	# 		log.critical('table %s not exists.'%cls.tblname)

	def checkInDB(self):
		if self.err > 0:
			return
		cmd = 'select count(*) from %s where id=%d;'%(self.tblname, self.tid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			return True
		else:
			return False

	def insertNewToDB(self):
		if self.err > 0:
			return
		base = self.curr
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = "insert into %s(id, typ, curr, stat, base, updateTime) values(%d,%d,%d,%d,%d,'%s');"%( \
				self.tblname, self.tid, self.typ, self.curr, self.stat, base, now)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def queryCurrent(self):
		if self.err > 0:
			return
		cmd = "select curr from %s where id=%d;"%(self.tblname, self.tid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and len(results) > 0:
			return results[0]
		else:
			log.warning("query current failed, tblname: %s, tid: 0x%0X" %( self.tblname, self.tid ))
			return 0

	def queryBase(self):
		if self.err > 0:
			return
		cmd = "select base from %s where id=%d;"%(self.tblname, self.tid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and len(results) > 0:
			return results[0]
		else:
			log.warning("query base failed, tblname: %s, tid: 0x%0X" %( self.tblname, self.tid ))
			return 0

	def updateToDB(self):
		if self.err > 0:
			return
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

		if self.reset_base:
			#����ǰ��λ���ͻ���������Ϊ���õĻ���
			cmd = "update %s set curr=%d, base=%d, updateTime='%s' where id=%d;"%( \
				self.tblname, self.curr, self.curr, now, self.tid)
			log.debug('manual set update db. tid: 0x%0X, cur: %d' %(self.tid, self.curr))
		else:
			cmd = "update %s set typ=%d, curr=%d, stat=%d, updateTime='%s' where id=%d;"%( \
				self.tblname, self.typ, self.curr, self.stat, now, self.tid)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def writeToDB(self):
		if self.err > 0:
			return
		if self.checkInDB():
			self.updateToDB()
		else:
			self.insertNewToDB()

class ParkEquip(Model):
	tblname = 'park_equip'
	def __init__(self, tid):
		super(ParkEquip, self).__init__()
		self.tid = tid
		self.pid = None

	# def __str__(self):
	# 	return '[DBRecord]Terminal tid: %d, pid: %d'%(self.tid, self.pid)

	def getParkId(self):
		if not self.tid:
			return
		cmd = "select parkcode from %s where equipid='%d'" % (self.tblname, self.tid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			self.pid = results[0]
			return results[0]

class ParkInfo(Model):
	tblname = config.get('table', 'park_info_tbl', 'parkInfo')
	cache_stot = {}
	def __init__(self, pid):
		super(ParkInfo, self).__init__()
		self.pid = pid
		self.stot = self.queryTotal()

	def queryTotal(self):
		#��cache���棬�������ݿ��ѯ
		if self.cache_stot.has_key(self.pid):
			return self.cache_stot[self.pid]

		column_name = config.get('table', 'park_info_column_total')
		cmd = "select %s from %s where id=%d;"%(column_name, self.tblname, self.pid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			self.cache_stot[self.pid] = results[0]
			return results[0]
		else:
			log.critical("query part info failed, tblname: %s, id: 0x%0X" %( self.tblname, self.pid ))
			return 0

	def checkInDB(self):
		cmd = 'select count(*) from %s where Code=%d;'%(self.tblname, self.pid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			return True
		else:
			return False

TerminalHeart.checkTable()
ParkLog.checkTable()
ParkLogIdentity.checkTable()

if __name__ == "__main__":
        tid = 0x10
        typ = 0x11
        io = 0x01
        curr = 100
        tot = 200
        stat = 1
        counter = 1
        #p1 = TerminalHeart(tid, typ, io, curr, tot, stat, counter)
        #p1.writeToDB()

        p2 = ParkLog(1111, 111)
        p2.writeToDB()
