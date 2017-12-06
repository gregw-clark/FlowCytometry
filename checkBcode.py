#!/usr/bin/env python

import string, re, sys
#from fuzzywuzzy import fuzz
import xlrd
import collections
from collections import defaultdict
import os
import datetime
from pandas import DataFrame
import numpy as np
import operator
import itertools
import MySQLdb as mdb
import subprocess
## written modules
from pandas import DataFrame
from Bio.Seq import Seq
from multiprocessing import Pool
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw
dbins=dbw()



def cleanRead(datavalue):
	d=str(str(datavalue).split(":")[1]).lstrip("u\'").rstrip("\'")
	return d


cnx,cur=dbins.connect(db_env='PROD',local_db='impc')
Bcnx,Bcur=dbins.connect(db_env='PROD',local_db='musmusculims')


if __name__ == "__main__":
	infile=sys.argv[1]
	op=open(infile,'r').readlines()
	header=",".join(op[0].split(",")[:-1])
	#print header
	#sys.exit()
	op.pop(0)
	#print header	
	datain=",".join(map(lambda p: "\""+p+"\"",op[1].split(",")))
	for j in range(len(op)):
		datain=",".join(map(lambda p: "\""+p+"\"",op[j].split(",")[:-1]))
		plaindata=op[j].strip().split(",")[:3]
		Scode,Eart=map(lambda quotab: "\""+quotab+"\"",[plaindata[1],plaindata[2]])
		print Scode,Eart,
		try:
			Barcode="SELECT A.DOB,A.DOD,A.MouseBCode FROM impc_Mice A JOIN impc_Mouseline B ON A.Mouseline = B.Mouseline_ID where SampleID = %s and B.StrainCode = %s" % (Eart,Scode)
			cur.execute(Barcode)
			#cnx.commit()
			returned=cur.fetchall()
			if len(returned) != 1:
				print "ERRRORS"
			else:
				DOB,DOD,MouseBCode=returned[0]
			print DOB,DOD,MouseBCode
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
		DOD="\""+str(DOD).split()[0]+"\""
		try:
			update="UPDATE impc_FlowCytometry SET MouseBCode = %s, DOD = %s,metadata_id=1 where strainCode = %s and earTag = %s" % (MouseBCode,DOD,Scode,Eart)
	#		print update
			Bcur.execute(update)
			Bcnx.commit()
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
Bcur.close()
Bcnx.close()
cur.close()
cnx.close()
