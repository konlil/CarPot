#coding: gbk
import log

DATABASE_ENGINE = 'mssql'	# canbe "mssql", "sqlite"

if DATABASE_ENGINE == 'sqlite':
	import sqlite3
else:
	import pymssql

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


class DBMSSql(DBBase):
	def __init__(self, host='218.4.157.251', user='sa', pwd='oracle54321::', db='park'):
		super(DBMSSql, self).__init__()
		self.conn = pymssql.connect(host=host, user = user, \
				password = pwd, database = db, charset='utf8')
		cur = self.conn.cursor()
		if not cur:
			log.critical('create db connection failed.' + str(self))
		else:
			log.info('connection to db: %s'%db)

	def tableExists(self, tblname):
		cmd = 'select count(*) from sysobjects where id=object_id("%s") and type="u";'%tblname
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
		cur = self.conn.cursor()
		cur.execute(cmd)
		return cur

	def Commit(self):
		self.conn.commit()

	def Close(self):
		self.conn.close()

if DATABASE_ENGINE == 'sqlite':
	obj = DBSqlite()	
else:
	obj = DBMSSql('218.4.157.251', 'sa', 'oracle54321::', 'park')	

if __name__ == "__main__":
	print obj.tableExists('test')
