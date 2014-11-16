#coding: gbk

import logging
from logging.handlers import RotatingFileHandler
import config

log_level_dict = {
	'DEBUG': logging.DEBUG,
	'INFO': logging.INFO,
	'WARN': logging.WARN,
	'ERROR': logging.ERROR,
	'CRITICAL': logging.CRITICAL,
}
log_level_def = config.get('debug', 'log_level', 'INFO')
log_level = log_level_dict.get(log_level_def)

# create a logger
logger = logging.getLogger('netlogger')
logger.setLevel(log_level)

# create a handler to file
fh = RotatingFileHandler('net.log', maxBytes=100*1024*1024, backupCount=10)
fh.setLevel(log_level)

# create a handler to console stream
ch = logging.StreamHandler()
ch.setLevel(log_level)

# define handler's format
formatter = logging.Formatter('%(asctime)s\t[%(levelname)s]\t%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

logger.debug('log level set at: %s' % log_level_def)

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
