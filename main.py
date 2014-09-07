#coding: gbk
import nethost
import time
import gvars

def main():
	host = nethost.nethost()
	if host.startup('0.0.0.0', 32005) < 0:  #58.210.93.254
		return
	while 1:
		time.sleep(0.1)
		host.process()
		event, wparam, lparam, data = host.read()
		if event < 0: continue
		print 'event=%d wparam=%xh lparam=%xh data="%s"'%(event, wparam, lparam, data)
		if event == gvars.NET_DATA:
			host.process_event(wparam, lparam, data)
		elif event == gvars.NET_NEW:
			# host.settag(wparam, wparam)
			host.nodelay(wparam, 1)
	host.shutdown()


if __name__ == "__main__":
	main()
