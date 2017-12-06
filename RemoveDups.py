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

cnx,cur=dbins.connect(db_env='PROD',local_db='musmusculims')


cur.execute("""desc impc_FlowCytometry""")
descr=cur.fetchall()
columns={}
for d in descr:
#	print d[0],d[1]
	columns[d[0]]=d[1]





if __name__ == "__main__":

        try:
                command = "SELECT RecordID,strainCode,earTag FROM impc_FlowCytometry"
                cur.execute(command)
		allrecords=cur.fetchall()
	except mdb.Error,e:
		print e.args[0],e.args[1]
		sys.exit()
	clatter=[]
	original=[]
	duplicates=[]
	for rec in allrecords:
		print rec
		record,strain,tag=rec
		if strain+tag in clatter:
			print strain,tag
			duplicates.append(record)
		else:
			clatter.append(strain+tag)
	print len(duplicates)
				
