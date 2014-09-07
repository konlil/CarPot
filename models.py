#coding: gbk
import db
import log

class Model(object):
	TABLE_DEF = {}
	def __init__(self):
		self.dbobj = db.DBSqlite()
		self.tblname = self.__class__.__name__
		if not self.dbobj.tableExists(self.tblname):
			tabledesc = ''
			for k, v in self.TABLE_DEF.iteritems():
				tabledesc += '%s %s,'%(k, v)
			tabledesc = tabledesc[:-1]  # remove the last comma
			self.dbobj.createTable(self.tblname, tabledesc)
			self.dbobj.Commit()
			log.info('db: table %s created.'%self.tblname)

	def createTable(self):
		raise NotImplementedError

	def checkTable(self):
		raise NotImplementedError

class Terminal(Model):
	TABLE_DEF = {
		"tid": "int primary key",
		"pid": "int NOT NULL"
	}
	def __init__(self, tid, pid=None):
		super(Terminal, self).__init__()
		self.tid = tid
		self.pid = pid
		if self.pid is None:
			self.syncFromDB()

	def __str__(self):
		return '[DBRecord]Terminal tid: %d, pid: %d'%(self.tid, self.pid)

	def checkInDB(self):
		cmd = 'select count(*) from %s where tid=%d;'%(self.tblname, self.tid)
		cursor = self.dbobj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			return True
		else:
			return False

	def syncFromDB(self):
		cmd = 'select pid from %s where tid=%d;'%(self.tblname, self.tid)
		cursor = self.dbobj.Exec(cmd)
		results = cursor.fetchone()
		if results:
			self.pid = results[0]
			print self
		else:
			log.error('db: got no data from db (Terminal: %d).'%self.tid)
			raise

	def writeToDB(self):
		if self.checkInDB():
			cmd = 'update %s set pid=%d where tid=%d;'%(self.tblname, self.pid, self.tid)
			self.dbobj.Exec(cmd)
			log.warning('db: writeToDB failed, try to update already existed Terminal')
		else:
			cmd = 'insert into %s(tid, pid) values(%d, %d);'%(self.tblname, self.tid, self.pid)
			self.dbobj.Exec(cmd)
			log.info('db: writeToDB done. Terminal: %d, CarPark: %d'%(self.tid, self.pid))
		self.dbobj.Commit()

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
		if self.stot is None or self.scnt is None:
			self.syncFromDB()
		self.initTerminalCount()

	def __str__(self):
		return '[DBRecord]CarPark pid: %d, stot: %d, scnt: %d'%(self.pid, self.stot, self.scnt)

	def onRecv(self, raw_data):
		if raw_data['iostat'] == 0xAA:
			self.scnt -= 1
		elif raw_data['iostat'] == 0x55:
			self.scnt += 1
		self.writeToDB()

		if self.tcnt == 1:
			pass
		elif self.tcnt > 1:
			return (self.stot, self.scnt)
		else:
			log.error('db: there is not Terminal in CarPark: %d ?'%self.pid)

	def checkInDB(self):
		cmd = 'select count(*) from %s where pid=%d;'%(self.tblname, self.pid)
		cursor = self.dbobj.Exec(cmd)
		results = cursor.fetchone()
		if results and results[0] > 0:
			return True
		else:
			return False

	def syncFromDB(self):
		cmd = 'select stot, scnt from %s where pid=%d;'%(self.tblname, self.pid)
		cursor = self.dbobj.Exec(cmd)
		results = cursor.fetchone()
		if results:
			self.stot = results[0]
			self.scnt = results[1]
		else:
			log.error('db: got no data from db (CarPark: %d).'%self.pid)
			raise

	def writeToDB(self):
		if self.checkInDB():
			cmd = 'update %s set stot=%d, scnt=%d where pid=%d;'%(self.tblname, self.stot, self.scnt, self.pid)
			self.dbobj.Exec(cmd)
			log.warning('db: writeToDB failed, try to update already existed Terminal')
		else:
			cmd = 'insert into %s(stot, scnt, pid) values(%d, %d, %d);'%(self.tblname, self.stot, self.scnt, self.pid)
			self.dbobj.Exec(cmd)
			log.info('db: writeToDB done. CarPark: %d, Total: %d, Current: %d'%(self.pid, self.stot, self.scnt))
		self.dbobj.Commit()

	def initTerminalCount(self):
		cmd = 'select count(*) from Terminal where pid = %d;' % (self.pid)
		cursor = self.dbobj.Exec(cmd)
		results = cursor.fetchone()
		if results:
			self.tcnt = results[0]
		else:
			log.error('db: init Terminal count for CarPark: %d failed.'%self.pid)
			return

if __name__ == "__main__":
	m1 = Terminal(0x01, 0x10)
	m1.writeToDB()
	m1
	m2 = CarPark(0x10, 100, 90)
	m2.writeToDB()
	m2
