#coding: gbk
import ConfigParser

cf = ConfigParser.ConfigParser()
cf.read('config.ini')

def get(segment, key, default=None):
	try:
		return cf.get(segment, key)
	except:
		return default
