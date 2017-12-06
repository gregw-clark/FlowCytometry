#!/usr/bin/env python

import string, re, sys

from DBwrap import MDB as dbw
import MySQLdb as mdb

ins=dbw()

#m=ins.connect(db_env='PROD')
m=ins.connect(db_env='PROD',local_db='impc')

if m:
	cnx,cur=m
else:
	print "Error connecting to Database"
	sys.exit()
print cnx,cur