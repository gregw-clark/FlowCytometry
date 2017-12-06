#!/usr/bin/env python

import string, re, sys
import numpy as np
import scipy.stats as ss
import MySQLdb as mdb
from collections import defaultdict
import xlrd
import collections
import os
import datetime
import operator
import csv
import time
import smtplib
from scipy.stats.kde import gaussian_kde
import math
from FlowCytometryTools import FCMeasurement




class FlowUtilities:

	def open_xls_as_xlsx(self,filename,ExpDate,dataReturn=False):
	    	# first open using xlrd
		# This is us reading the files identified by FindXLFiles
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

		names=_columns[0]
		_columns.pop(0)
		_foundIMPC=[]
		valid_indices=[i for i,name in enumerate(names) if validname.search(name)]


		list_ids=[straintag.findall(name) for i,name in enumerate(names) if i in valid_indices]
		#print list_ids
		
		if any(filter(lambda p: len(p) != 1,list_ids)):
			print "\n\n"
			print "Error with filtering the names in this data set: %s\nPanel: %s\nSample Names: %s" % (filename,panel,names)
			print "\n\n"
			sys.exit()
		else:
			
			actual_ids=map(lambda p: str("_".join([ExpDate]+p[0].split("_")[1:3])), list_ids)	
		if dataReturn:
			return actual_ids,data
		else:
			return actual_ids


#	def FCSfile_v_binary(self,datafile):
		

	def FCScheck(self,datafile):
		filematch=re.compile("PANEL[\s_][AB][\s_][A][A-Z][A-Z][A-Z][\s_][0-9]{1,5}",flags=re.X | re.I)

		rawfilename = datafile.split("/")[-1]
	
		filesampleID="_".join(rawfilename.split("_")[2:4])	
		#sampleID=str(sampleID.strip().lstrip("(u\'"))

		codeonly=re.compile("[A][A-Z][A-Z][A-Z]_[0-9]{1,4}")
		controlonly=re.compile("[B][6][N][C]_[0-9]{1,4}")

		omitcontrol=re.compile("(^STAINED)|(Control)|(FMO)|(^UNSTAINED)|(^Specimen)|(,3a,)",flags=re.X | re.I)
		compFileNameA=re.compile("[A-z_]*PANELA$",flags=re.X|re.I)
		compFileNameB=re.compile("[A-z_]*PANELB$",flags=re.X|re.I)
		compFiles=re.compile("Compensation",flags=re.X|re.I)


		FluoroMatch=re.compile("""Compensation(\s|-|_){1,3}Controls(\s|-|_){0,3}(
			(CD25(\s|-|_){0,2}PE(\s|-|_){0,2}CY7)|
			(BV421)|
			(BV510)|
			(BV786)|
			(FITC)|
			(PE)|
			(APC)|
			(CD8a(\s|-|_){0,2}PE(\s|-|_){0,2}CF594)|
			(CD11b(\s|-|_){0,2}PE(\s|-|_){0,2}CF594)|
			(CD11C(\s|-|_){0,2}PE(\s|-|_){0,2}CY7)|
			(CD62L(\s|-|_){0,2}APC(\s|-|_){0,2}CY7)|
			(MHCII(\s|-|_){0,2}APC(\s|-|_){0,2}CY7)
			)""",flags=re.X | re.I)

		fullIMPC=re.compile("IMPC[12][\s_-]")
		
		sample=FCMeasurement(ID="Tops",datafile=datafile)
		mdata=sample.meta.keys()
		sampleID=sample.meta["TUBE NAME"]
		sampleID=str(sampleID.strip().lstrip("(u\'"))
		FullName=sample.meta["$FIL"]
		panel=sample.meta["$SRC"]
		if not panel.endswith("_"):
			panel="_".join(panel.split())+"_"
		else:
			panel="_".join(panel.split())

		return sampleID,filesampleID
