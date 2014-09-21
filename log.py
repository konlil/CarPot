#coding: gbk

import logging

# create a logger
logger = logging.getLogger('netlogger')
logger.setLevel(logging.DEBUG)

# create a handler to file
fh = logging.RotatingFileHandler('net.log', maxBytes=100*1024*1024, backupCount=10)
fh.setLevel(logging.DEBUG)

# create a handler to console stream
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# define handler's format
formatter = logging.Formatter('%(asctime)s\t[%(levelname)s]\t%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

def info(s):
	logger.info(s)

def debug(s):
	logger.debug(s)

def warning(s):
	logger.warning(s)

def error(s):
	logger.error(s)

def critical(s):
	logger.critical(s)
