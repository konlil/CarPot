#coding:gbk

import socket
import datetime
import protoc
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 32005))
report = {
	'cid':		0x01,
	'ctype':	0x11,
	'scnt': 	198,
	'iostat':	0xAA,		#0xAA, 0x55
	'stot':		200,
	'stat':		0x00,
	'counter':	0x01,
}

pkg = protoc.PkgRep(report)
data = pkg.serialize()

while 1:
	wsize = sock.send(data)
	while 1:
		if wsize < len(data):
			data = data[wsize:]
		else:
			break
	print 'send at', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
	time.sleep(10)

sock.close()
