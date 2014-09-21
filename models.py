#coding: gbk
import db
import datetime
import log

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
		"id": "int IDENTITY(1,1) PRIMARY KEY",
		"tid": "int NOT NULL",
		"typ": "int NOT NULL",
		"iostat":	"int NOT NULL",
		"curr": "int NOT NULL",
		"total": "int NOT NULL",
		"stat": "int NOT NULL",
		"cnter": "int NOT NULL",
		'updateTime': "datetime",
	}
	tblname = 'park_LogIdent'
	err = 0
	def __init__(self, tid, typ, io, curr, tot, stat, counter):
		super(ParkLogIdentity, self).__init__()
		self.tid = tid
		self.typ = typ
		self.io = io
		self.curr = curr
		self.tot = tot
		self.stat = stat
		self.counter = counter

	def insertNewToDB(self):
		if self.err > 0:
			return
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = "insert into %s(tid,typ,iostat,curr,total,stat,cnter,updateTime) values(%d,%d,%d,%d,%d,%d,%d,'%s');"%( \
				self.tblname, self.tid, self.typ, self.io, self.curr, self.tot, self.stat, self.counter, now)
		#log.debug("insert logident: %s" % cmd)
		db.obj.Exec(cmd)
		db.obj.Commit()
	
	def writeToDB(self):
		if self.err > 0:
			return
		self.insertNewToDB()

class ParkLog(Model):
	TABLE_DEF = {
		"id": "int primary key",
		"typ": "int NOT NULL",
		"iostat":	"int NOT NULL",
		"curr": "int NOT NULL",
		"total": "int NOT NULL",
		"stat": "int NOT NULL",
		"cnter": "int NOT NULL",
		'updateTime': "datetime",
	}
	tblname = 'park_Log2'
	err = 0
	def __init__(self, tid, typ, io, curr, tot, stat, counter):
		super(ParkLog, self).__init__()
		self.tid = tid
		self.typ = typ
		self.io = io
		self.curr = curr
		self.tot = tot
		self.stat = stat
		self.counter = counter

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
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = "insert into %s(id,typ,iostat,curr,total,stat,cnter,updateTime) values(%d,%d,%d,%d,%d,%d,%d,'%s');"%( \
				self.tblname, self.tid, self.typ, self.io, self.curr, self.tot, self.stat, self.counter, now)
		#cmd = "insert into %s(id,currCnt,updateTime) values(%d,%d,'%s');"%( \
		#		self.tblname, self.tid, self.cnt, now)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def updateToDB(self):
		if self.err > 0:
			return
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		#cmd = "update %s set currCnt=%d,updateTime='%s' where id=%d;"%( \
		#	self.tblname, self.cnt, now, self.tid)
		cmd = "update %s set typ=%d,iostat=%d, curr=%d, total=%d,stat=%d,cnter=%d,updateTime='%s' where id=%d;"%( \
			self.tblname, self.typ, self.io, self.curr, self.tot, self.stat, self.counter, now, self.tid)
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
	tblname = 'parkInfo'
	def __init__(self, pid, scnt=None):
		super(ParkInfo, self).__init__()
		self.pid = pid
		self.scnt = scnt

	# def __str__(self):
	# 	return '[DBRecord]CarPark pid: %d, stot: %d, scnt: %d'%(self.pid, self.stot, self.scnt)
	
	def checkInDB(self):
		cmd = 'select count(*) from %s where Code=%d;'%(self.tblname, self.pid)
		cursor = db.obj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			return True
		else:
			return False

	def writeToDB(self):
		if not ( self.scnt and self.pid ):
			log.error('db: writeToDB failed, try write invalid parkinfo data (%s,%s) to db' % (str(self.pid), str(self.scnt)))
			return

		if self.checkInDB():
			cmd = 'update %s set syberth=%d where pid=%d;'%(self.tblname, self.scnt, self.pid)
			db.obj.Exec(cmd)
			db.obj.Commit()
		else:
			log.error('db: writeToDB failed, record of park %d not found.' % self.pid)

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
