#coding: gbk
import sqlite3
import log

class DBBase(object):
	def __init__(self):
		self.conn = None

class DBSqlite(DBBase):
	DBFILE = 'pot.db'
	def __init__(self):
		super(DBSqlite, self).__init__()
		self.conn = sqlite3.connect(self.DBFILE)
		if not self.conn:
			log.critical('create db connection failed. ' + str(self))
		else:
			log.info('connection to db: %s'%self.DBFILE)

	def tableExists(self, tblname):
		cmd = 'select count(*) from sqlite_master where type="table" and name="%s";'%tblname
		cursor = self.conn.execute(cmd)
		if cursor:
			next = cursor.next()
			if next[0] == 0:
				return False
			else:
				return True
		return False

	def createTable(self, tblname, tbldesc):
		cmd = 'create table %s (%s)'%(tblname, tbldesc)
		log.debug('db: %s'%cmd)
		self.conn.execute(cmd)

	def Exec(self, cmd):
		log.debug('db %s' % cmd)
		return self.conn.execute(cmd)

	def Commit(self):
		self.conn.commit()
