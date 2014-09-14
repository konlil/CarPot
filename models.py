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
		cmd = 'insert into %s(id,stat,updateTime) values(%d,%d,%s);'%( \
				self.tblname, self.tid, self.stat, now)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def updateToDB(self):
		#cmd = 'update %s set typ=%d,iostat=%d, curr=%d, total=%d,stat=%d,cnter=%d where id=%d;'%( \
		#	self.tblname, self.typ, self.io, self.curr, self.tot, self.stat, self.counter, self.tid)
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		cmd = 'update %s set stat=%d,updateTime=%s where id=%d;'%( \
			self.tblname, self.stat, now, self.tid)
		db.obj.Exec(cmd)
		db.obj.Commit()

	def writeToDB(self):
		if self.checkInDB():
			self.updateToDB()
		else:
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
		cmd = 'insert into %s(id,typ,iostat,curr,total,stat,cnter,updateTime) values(%d,%d,%d,%d,%d,%d,%d,%s);'%( \
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
		cmd = 'update %s set typ=%d,iostat=%d, curr=%d, total=%d,stat=%d,cnter=%d,updateTime=%s where id=%d;'%( \
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


class Terminal(Model):
	TABLE_DEF = {
		"tid": "int primary key",
		"pid": "int NOT NULL"
	}
	def __init__(self, tid, pid=None):
		super(Terminal, self).__init__()
		self.tid = tid
		self.pid = pid
	# 	if self.pid is None:
	# 		self.syncFromDB()

	# def __str__(self):
	# 	return '[DBRecord]Terminal tid: %d, pid: %d'%(self.tid, self.pid)

	# def checkInDB(self):
	# 	cmd = 'select count(*) from %s where tid=%d;'%(self.tblname, self.tid)
	# 	cursor = db.obj.Exec(cmd)
	# 	results = cursor.fetchone()
	# 	if results and results[0] > 0:
	# 		return True
	# 	else:
	# 		return False

	# def syncFromDB(self):
	# 	cmd = 'select pid from %s where tid=%d;'%(self.tblname, self.tid)
	# 	cursor = db.obj.Exec(cmd)
	# 	results = cursor.fetchone()
	# 	if results:
	# 		self.pid = results[0]
	# 		print self
	# 	else:
	# 		log.error('db: got no data from db (Terminal: %d).'%self.tid)
	# 		raise

	# def writeToDB(self):
	# 	if self.checkInDB():
	# 		cmd = 'update %s set pid=%d where tid=%d;'%(self.tblname, self.pid, self.tid)
	# 		db.obj.Exec(cmd)
	# 		log.warning('db: writeToDB failed, try to update already existed Terminal')
	# 	else:
	# 		cmd = 'insert into %s(tid, pid) values(%d, %d);'%(self.tblname, self.tid, self.pid)
	# 		db.obj.Exec(cmd)
	# 		log.info('db: writeToDB done. Terminal: %d, CarPark: %d'%(self.tid, self.pid))
	# 	db.obj.Commit()

class CarPark(Model):
	TABLE_DEF = {
		"pid": "int primary key",
		"stot": "int",
		"scnt": "int",
	}
	def __init__(self, pid, stot=None, scnt=None):
		super(CarPark, self).__init__()
		self.pid = pid
		self.stot = stot
		self.scnt = scnt
		self.tcnt = 0  			#终端数量
	# 	if self.stot is None or self.scnt is None:
	# 		self.syncFromDB()
	# 	self.initTerminalCount()

	# def __str__(self):
	# 	return '[DBRecord]CarPark pid: %d, stot: %d, scnt: %d'%(self.pid, self.stot, self.scnt)

	# def onRecv(self, raw_data):
	# 	if raw_data['iostat'] == 0xAA:
	# 		self.scnt -= 1
	# 	elif raw_data['iostat'] == 0x55:
	# 		self.scnt += 1
	# 	self.writeToDB()

	# 	if self.tcnt == 1:
	# 		pass
	# 	elif self.tcnt > 1:
	# 		return (self.stot, self.scnt)
	# 	else:
	# 		log.error('db: there is not Terminal in CarPark: %d ?'%self.pid)

	# def checkInDB(self):
	# 	cmd = 'select count(*) from %s where pid=%d;'%(self.tblname, self.pid)
	# 	cursor = db.obj.Exec(cmd)
	# 	results = cursor.fetchone()
	# 	if results and results[0] > 0:
	# 		return True
	# 	else:
	# 		return False

	# def syncFromDB(self):
	# 	cmd = 'select stot, scnt from %s where pid=%d;'%(self.tblname, self.pid)
	# 	cursor = db.obj.Exec(cmd)
	# 	results = cursor.fetchone()
	# 	if results:
	# 		self.stot = results[0]
	# 		self.scnt = results[1]
	# 	else:
	# 		log.error('db: got no data from db (CarPark: %d).'%self.pid)
	# 		raise

	# def writeToDB(self):
	# 	if self.checkInDB():
	# 		cmd = 'update %s set stot=%d, scnt=%d where pid=%d;'%(self.tblname, self.stot, self.scnt, self.pid)
	# 		db.obj.Exec(cmd)
	# 		log.warning('db: writeToDB failed, try to update already existed Terminal')
	# 	else:
	# 		cmd = 'insert into %s(stot, scnt, pid) values(%d, %d, %d);'%(self.tblname, self.stot, self.scnt, self.pid)
	# 		db.obj.Exec(cmd)
	# 		log.info('db: writeToDB done. CarPark: %d, Total: %d, Current: %d'%(self.pid, self.stot, self.scnt))
	# 	db.obj.Commit()

	# def initTerminalCount(self):
	# 	cmd = 'select count(*) from Terminal where pid = %d;' % (self.pid)
	# 	cursor = db.obj.Exec(cmd)
	# 	results = cursor.fetchone()
	# 	if results:
	# 		self.tcnt = results[0]
	# 	else:
	# 		log.error('db: init Terminal count for CarPark: %d failed.'%self.pid)
	# 		return

TerminalHeart.checkTable()
ParkLog.checkTable()

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
