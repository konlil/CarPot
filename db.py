#coding: gbk
import log
import ConfigParser

cf = ConfigParser.ConfigParser()
cf.read('config.ini')
sects = cf.sections()
dbcfg = cf.options("db")
items = cf.items('db')

DB_ENGINE = cf.get('db', 'db_engine')
DB_HOST = cf.get('db', 'db_host')
DB_PORT = cf.get('db', 'db_port')
DB_USER = cf.get('db', 'db_user')
DB_PASS = cf.get('db', 'db_pass')
DB_NAME = cf.get('db', 'db_name')

if DB_ENGINE == 'sqlite':
	import sqlite3
else:
	import pymssql

import _mssql
import decimal
import uuid
decimal.__version__
uuid.ctypes.__version__
_mssql.__version__

class DBBase(object):
	def __init__(self):
		self.conn = None

class DBSqlite(DBBase):
	def __init__(self):
		super(DBSqlite, self).__init__()
		self.conn = sqlite3.connect(DB_NAME)
		if not self.conn:
			log.critical('create db connection failed. ' + str(self))
		else:
			log.info('connection to db: %s'%DB_NAME)

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
		#log.debug('db %s' % cmd)
		return self.conn.execute(cmd)

	def Commit(self):
		self.conn.commit()


class DBMSSql(DBBase):
	def __init__(self, host, user, pwd, db):
		super(DBMSSql, self).__init__()
		log.info('connecting db: %s %s %s %s'%(host, user, pwd, db))
		self.conn = pymssql.connect(host=host, user = user, \
				password = pwd, database = db, charset='utf8')
		cur = self.conn.cursor()
		if not cur:
			log.critical('create db connection failed.' + str(self))
		else:
			log.info('connection to db: %s'%db)

	def tableExists(self, tblname):
		cmd = "select count(*) from sysobjects where name='%s' and type='U';"%tblname
		cur = self.conn.cursor()
		cur.execute(cmd)
		next = cur.next()
		if next and next[0] > 0:
			return True
		return False

	def createTable(self, tblname, tbldesc):
		cmd = 'create table %s (%s)'%(tblname, tbldesc)
		log.debug('db: %s'%cmd)
		cur = self.conn.cursor()
		cur.execute(cmd)

	def Exec(self, cmd):
		#log.debug('db %s' % cmd)
		cur = self.conn.cursor()
		cur.execute(cmd)
		return cur

	def Commit(self):
		self.conn.commit()

	def Close(self):
		self.conn.close()

if DB_ENGINE == 'sqlite':
	obj = DBSqlite()
else:
	if DB_PORT:
		host = '%s:%s'%(DB_HOST, DB_PORT)
	else:
		host = DB_HOST
	obj = DBMSSql(host, DB_USER, DB_PASS, DB_NAME)

if __name__ == "__main__":
	print obj.tableExists('park_Log')
