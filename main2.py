#coding: gbk
import asyncore
import ConfigParser
import log

cf = ConfigParser.ConfigParser()
cf.read('config.ini')

SVR_IP = cf.get('service', 'svr_addr')
SVR_PORT = cf.get('service', 'svr_port')
log.info('read service config, ip:%s, port:%d'%(SVR_IP, int(SVR_PORT)))

import nethost2 as nethost

def main():
	host = nethost.nethost()
	if host.startup(SVR_IP, int(SVR_PORT)) < 0:  #58.210.93.254
		return
	asyncore.loop()
	host.shutdown()


if __name__ == "__main__":
	main()
