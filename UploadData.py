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





def open_xls_as_xlsx(filename,panel,impc_order,IMdata):
    # first open using xlrd
	wb=xlrd.open_workbook(filename)
	sheet = wb.sheet_by_index(0)
	r=sheet.row(0)
	c=sheet.col_values(0)
	data=[]
	validname=re.compile("Panel[_\s][AB]_[A-Z][A-Z6][A-Z][A-Z]_[0-9]{1,4}_",flags=re.X | re.I)
	straintag=re.compile("_[A-Z][A-Z6][A-Z][A-Z]_[0-9]{1,4}_",flags=re.X|re.I)
	for i in xrange(sheet.nrows):
		data.append(sheet.row_values(i))
	_columns=zip(*data)
	_impc = dict((k,v) for k,v in impc_order.items() if v[0] == panel)
	_markers = dict((str(v[5]),k) for k,v in _impc.items())

	sortmarkers=sorted(_markers.items(), key=operator.itemgetter(1))
	
	datex=re.compile("[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]")
	splitDate=re.compile("[\-_\s]")
	allDates=map(lambda d: "-".join(re.split("[_\-\s]",d)),datex.findall(filename))
	
	if not all(x==allDates[0] for x in allDates):
		print "\n\n"
		print "Error with some dates in the file path: %s" % (filename)
		print "The dates in question:"," ".join(allDates)
		print "Please fix this before continuing."
		print "\n\n"
		sys.exit()

	lclDate=datex.findall(filename.split("/")[-1])
	if len(lclDate) != 1:
		print "Error with the filename for: %s\nWe expect there to be 1 date, we find %s!" % (filename,len(lclDAte))
		sys.exit()
	else:
		IDdate="-".join(re.split("[-_\s]",lclDate[0]))
	names=_columns[0]
	_columns.pop(0)
	_foundIMPC=[]
	valid_indices=[i for i,name in enumerate(names) if validname.search(name)]


	list_ids=[straintag.findall(name) for i,name in enumerate(names) if i in valid_indices]
	if any(filter(lambda p: len(p) != 1,list_ids)):
		print "\n\n"
		print "Error with filtering the names in this data set: %s\nPanel: %s\nSample Names: %s" % (filename,panel,names)
		print "\n\n"
		sys.exit()
	else:
		
		actual_ids=map(lambda p: str("_".join([IDdate]+p[0].split("_")[1:3])), list_ids)	


	headerfilter=re.compile("[A-z0-9\,\-\+]+[\s]{0,3}\|[\s]{0,3} Count$",flags=re.X | re.I)
	percentB=re.compile("CLOG-\/Live[\s]{0,3}\|[\s]{0,3}Freq.[\s]{0,3}of[\s]+Total",flags=re.X | re.I)
	clogcount=re.compile("CLOG-[\s]{0,3}\|[\s]{0,3}Count$",flags= re.X | re.I)	

	
	for column in _columns:
		header=column[0]
		
		if headerfilter.search(header) or clogcount.match(header) or percentB.match(header):
			foundbit="".join(header.split()).upper()	
			try:
				_markers[foundbit]
				IMData[_markers[foundbit]]=[(column[i],a) for i,a in zip(valid_indices,actual_ids)]
				_foundIMPC.append(_markers[foundbit])
			except KeyError:
				pass
				#sys.exit()
				#pass
	_foundIMPC.sort()
	return IMData



def findXLfiles(path):
	if not len(path):
		path="."
	datex=re.compile("[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]")
	impx=re.compile("IMPC\s{0,5}[-_]{0,1}[1-2]")
	xlsex=re.compile("xls$|xlsx$")
	Excel_runs=defaultdict(list)
	Excel_paths=defaultdict(list)
	for root, dirs, files in os.walk(path):
		path = root.split('/')
		base=path[-1]
		try:
			analysisdir=path[-2]
			datedir=path[-3]
			rawdates=datex.findall(datedir)
			nesteddata=path[-4]
			if re.match("IMPC",base) and re.search("ANALYSIS",analysisdir) and datex.search(datedir) and datex.search(nesteddata):
				xls=filter(lambda f: xlsex.search(f),files)
				if len(xls) > 1:
					print "\n\n"
					print "Error with the number of excel files found in: %s\nShould only be 1 file and we found %s.\nFiles: %s" % (root,len(xls),",".join(xls))
					print "\n\n"
					sys.exit()
				if re.search("1",base):
					Excel_runs[path[-4]].insert(0,xls[0])
					Excel_paths[path[-4]].insert(0,root)
				else:
					Excel_runs[path[-4]].append(xls[0])	
					Excel_paths[path[-4]].append(root)
			elif re.match("IMPC",base) and re.search("ANALYSIS",analysisdir) and datex.search(datedir):
				print "SKIPPING THESE FILES",base,datedir
		except IndexError:
			pass
	return Excel_runs,Excel_paths

if __name__ == "__main__":
	infile=sys.argv[1]
	op=open(infile,'r').readlines()
	header=",".join(op[0].split(",")[:-1])
	op.pop(0)
	#print header	
	datain=",".join(map(lambda p: "\""+p+"\"",op[1].split(",")))
	uploaded=0
	for j in range(len(op)):
		datain=",".join(map(lambda p: "\""+p+"\"",op[j].split(",")[:-1]))
		try:
			command="INSERT INTO impc_FlowCytometry (%s) VALUES (%s)" % (header,datain)
			print header
			print datain
			cur.execute(command)
			cnx.commit()
			uploaded+=1
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
	print "Uploaded %s files from %s" % (uploaded,infile)
