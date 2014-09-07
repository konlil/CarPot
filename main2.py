#coding: gbk
import nethost2 as nethost
import asyncore

def main():
	host = nethost.nethost()
	if host.startup('0.0.0.0', 32005) < 0:  #58.210.93.254
		return
	asyncore.loop()
	host.shutdown()


if __name__ == "__main__":
	main()
