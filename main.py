#coding: gbk
import log
import nethost
import time

def main():
	host = nethost.nethost()
	if host.startup('58.210.93.254', 32005) < 0:
                return
	while 1:
		time.sleep(0.1)
		host.process()
	host.shutdown()


if __name__ == "__main__":
	main()
