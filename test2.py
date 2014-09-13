#coding: gbk
import netstream2 as netstream
import time
import asyncore

client = netstream.netstream()
client.connect_ex('58.210.93.254', 32005)

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
asyncore.loop()
while 1:
	time.sleep(1)

#client.close()
