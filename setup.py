#coding: gbk

from distutils.core import setup
import py2exe

setup(
	name = 'park_service',
	description = 'Parking Lot Service Program',
	version = '1.0',
	console=['main2.py'],
	data_files=["config.ini"]
)
	
