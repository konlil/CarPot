#coding: gbk
import netstream

client = netstream.netstream()
client.connect('127.0.0.1', 32005)
client.nodelay(0)
client.nodelay(1)

report = {
	'cid':		0x01, 
	'ctype':	0x11, 
	'scnt': 	198, 
	'iostat':	0xAA,		#0xAA, 0x55
	'stot':		200, 
	'stat':		0x00, 
	'counter':	0x01,
}
client.send_report(report)

client.close()
