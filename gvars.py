#coding: gbk

#======================================================================
# netstate
#======================================================================
NET_STATE_STOP = 0				# state: init value
NET_STATE_CONNECTING = 1		# state: connecting
NET_STATE_ESTABLISHED = 2		# state: connected

#======================================================================
# nethost - basic tcp host
#======================================================================
NET_NEW =		0	# new connection：(id,tag) ip/d,port/w   <hid>
NET_LEAVE =		1	# lost connection：(id,tag)   		<hid>
NET_DATA =		2	# data comming：(id,tag) data...	<hid>
NET_TIMER =		3	# timer event: (none, none) 