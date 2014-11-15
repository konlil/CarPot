#coding: gbk
import asyncore
import log
import win32api
import config

SVR_IP = config.get('service', 'svr_addr')
SVR_PORT = config.get('service', 'svr_port')
log.info('read service config, ip:%s, port:%d'%(SVR_IP, int(SVR_PORT)))

import nethost2 as nethost
host = nethost.nethost()

def main():
	if host.startup(SVR_IP, int(SVR_PORT)) < 0:  #58.210.93.254
		return
	asyncore.loop()

def close(arg):
	host.shutdown()

win32api.SetConsoleCtrlHandler(close, 1)
if __name__ == "__main__":
	main()
