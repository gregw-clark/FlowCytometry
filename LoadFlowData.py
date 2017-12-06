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
import time
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw
dbins=dbw()


def cleanRead(datavalue):
	d=str(str(datavalue).split(":")[1]).lstrip("u\'").rstrip("\'")
	return d

Yes=re.compile("(y$)|(yes$)",flags=re.I)
No=re.compile("(n)|(no)",flags=re.I)



dev=False

if dev:
	I_cnx,I_cur=dbins.connect(local_db='impc')
	cnx,cur=dbins.connect(local_db='musmusculims')
else:

	print "\n\n\tYou are about to update the PRODUCTION database, continue (Y/N): " 
	proceed=raw_input().strip()
	if Yes.match(proceed):
		os.system('clear')
		print "\n\n\n\n\t\tOk, going ahead on PRODUCTION server.\n\n\n\n"
	else:
		print "Be safe then , aborting..."
		sys.exit()

	I_cnx,I_cur=dbins.connect(db_env='PROD',local_db='impc')
	cnx,cur=dbins.connect(db_env='PROD',local_db='musmusculims')



if __name__ == "__main__":
	infile=sys.argv[1]
	op=open(infile,'r').readlines()
	header=",".join(op[0].split(","))
	fullheader=",".join(["MouseBCode","DOD","metadata_id","QC_By","QC_Date"]+op[0].split(","))
	blankheader=map(lambda p : p.strip(),op[0].split(","))
	op.pop(0)
	datain=",".join(map(lambda p: "\""+p+"\"",op[1].split(",")))
	QC_By = "QC_FlowCyto_2016_11_21.py"
	QC_Date=(time.strftime("%Y-%m-%d"))
	for j in range(len(op)):
		exists=False
		datain=",".join(map(lambda p: "\""+p+"\"",op[j].split(",")))
		data_init=op[j].split(",")
		expDate,strainCode,earTag=map(lambda s: "\""+s+"\"",op[j].split(",")[:3])
		impc_data=op[j].split(",")[3:]
		wanted_impc=map(lambda p: p.strip(),header.split(",")[3:])
		row_data=dict(zip(wanted_impc,impc_data))	
		try:
			checkexist="select %s from impc_FlowCytometry where expDate = %s and strainCode = %s and earTag = %s"  % (",".join(wanted_impc),expDate,strainCode,earTag) 
			cur.execute(checkexist)
			existing=cur.fetchall()
		except mdb.Error,e:
			print e.args[0],e.args[1]
		if len(existing):
			#print len(existing)
			if len(existing[0]) > 0:
				exists=True
			else:
				exists=False

		if exists == False:
			## Get the Barcode First
			try:
				Barcode="""SELECT A.DOB,A.DOD,A.MouseBCode 
					FROM impc_Mice A JOIN impc_Mouseline B ON A.Mouseline = B.Mouseline_ID 
					Where SampleID = %s and B.StrainCode = %s""" % (earTag,strainCode)
				I_cur.execute(Barcode)
				returned=I_cur.fetchall()
				if len(returned) != 1:
					print "ERRRORS"
				else:
					DOB,DOD,MouseBCode=returned[0]
					print DOB,DOD,MouseBCode
					DOB=str(DOB).split()[0]
					DOD=str(DOD).split()[0]
					#print DOB,DOD,MouseBCode
					#(["MouseBCode","DOD","metadata_id","upload_date","QC_By","QC_Date"]
					data_init.insert(0,QC_Date)
					data_init.insert(0,QC_By)
					data_init.insert(0,"1")
					data_init.insert(0,DOD)
					data_init.insert(0,MouseBCode)
			except mdb.Error,e:
				print e.args[0],e.args[1]
				sys.exit()	
		
			data_init=",".join(map(lambda p: "\""+p.strip()+"\"",data_init))
			#print data_init
			#print fullheader
			print data_init.count(",")
			print fullheader.count(",")
			#sys.exit()
			try:
				print "\t\t********\tNew mouse added\t***********\n"
				command="INSERT INTO impc_FlowCytometry (%s) VALUES (%s)" % (fullheader,data_init)
				cur.execute(command)
				print "Created new mice data for Experiment %s, Mouse with StrainCode %s and earTag %s\n\n" % (expDate,strainCode,earTag)
				cnx.commit()
			except mdb.Error,e:
				print "ERROR",e.args[0],e.args[1]
				sys.exit()
		else:
			update_column=[]
			update_data=[]
			update_from=[]
			for n,a in zip(wanted_impc,existing[0]):
				if str(a) in ["None","Null","NULL","NONE"]:
					update_data.append(float(row_data[n]))
					update_from.append(a)
					update_column.append(n)	
				elif float(a) != float(row_data[n]):
					update_data.append(float(row_data[n]))
					update_from.append(float(a))
					update_column.append(n)	
			if len(update_data):
				update="UPDATE impc_FlowCytometry set "
				for param in update_column:
					update+=param+" = %s, "
				update=update.rstrip(", ")+" "
				update+="Where expDate = %s and strainCode = %s and earTag = %s"
				update_data+=[expDate,strainCode,earTag]
				command=update % tuple(update_data)
				try:
					cur.execute(command)
					print "Updating experiment %s; Mouse %s - Ear Tag %s." % (expDate,strainCode,earTag)
					for l,m,n in zip(update_column,update_from,update_data):
						print "\t\tUpdating column %s from %s to %s " % (l,m,n)
					cnx.commit()
				except mdb.Error,e:
					print e.args[0],e.args[1]
					sys.exit()
				print "\n\n"

	cur.close()
	cnx.close()
