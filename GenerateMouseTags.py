#!/usr/bin/env python

import string, re, sys
#from fuzzywuzzy import fuzz
import xlrd
import collections
from collections import defaultdict
import os
import datetime
import numpy as np
import operator
import csv
import time
import MySQLdb as mdb
import smtplib
import filecmp
from shutil import copy#,disk_usage
import glob
from LiteUtils import FlowUtilities

func=FlowUtilities()




def GetSampleNames(dType,files,datedir):
	datex=re.compile("[2][0][1][0-9][-_][0-9]{0,1}[0-9]{0,1}[_-][0-3]{0,1}[0-9]")
	ProperCode=re.compile("[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}", flags = re.X | re.I)

	if dType not in ["Excel","FCS"]:	sys.exit()
	if not datex.match(datedir): print "Date is incorrect %s" % datedir;sys.exit()

	if dType == "FCS":
		fcsfiles=files
		allFCS_=map(lambda k: func.FCScheck(k),fcsfiles)
		uqFCS_=map(lambda s : "_".join(str(s).split("_")[:2]),allFCS_)
		flatFCS_=list(set(uqFCS_))	
		flatFCS_.sort()
		return flatFCS_
	elif dType =="Excel":
		xlfiles=files
		allXL_=map(lambda k: func.open_xls_as_xlsx(k,datedir),xlfiles)
		flatXL_=list(set([item for sublist in allXL_ for item in sublist]))	
		XLnames = map(lambda s: ProperCode.findall(s)[0], flatXL_)
		XLnames.sort()
		return XLnames

statvfs=os.statvfs('/home/clarkg/')

reload(sys)  
sys.setdefaultencoding('utf8')

######################################################
#                                                    #
#                                                    #
#	UU  UU	SSSS	 AA	 GGGG	EEEEE	     #
#	UU  UU  SS      A  A	G	E            #
#	UU  UU	$$$$   AAAAAAA	G GGG	EEEEE        #
#	UU  UU    $$   A     A  G   G	E            #
#	 UUUU   $$$$   A     A   GGGG	EEEEE        #
#                                                    #
#                                                    #
######################################################


def compare(allfiles, currentfile):
	filename=currentfile.split("/")[-1]
	opposites=filter(lambda l: re.search(filename,l),allfiles)
	opposites.remove(currentfile)
	return opposites


#matrixfiles={}
allfiles=defaultdict(list)

def FindFlowFiles(path):

	if not len(path):
		path="."
	

	omitcontrol=re.compile("(^STAINED)|(Control)|(FMO)|(^UNSTAINED)|(^Specimen)|(,3a,)",flags=re.X | re.I)
	compFileNameA=re.compile("[A-z_]*PANELA$",flags=re.X|re.I)
	compFileNameB=re.compile("[A-z_]*PANELB$",flags=re.X|re.I)
	compFiles=re.compile("Compensation",flags=re.X|re.I)

	FluoroMatch=re.compile("""Compensation(\W|-|_){1,3}Controls(\W|-|_){0,3}(
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

	FMOfiles=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}(A|B)""",flags=re.X|re.I)

	MatrixF=re.compile("""[A-z0-9\s_\-,]+MATRIX[A-z0-9\s_\-,]+[\.]mtx""",flags=re.X|re.I)
	# traverse root directory, and list directories as dirs and files as files
	#print "COMMONPATH: %s" % commonpath

	##IMPC_96 Well - U bottom'
	compDir=re.compile("IMPC[\W_]+96[\W_]+Well[\W_]+U[\W_]+bottom",flags=re.X | re.I)
	PanelFiles=re.compile("PANEL[\W_]{0,3}[AB][\W_]{1,2}[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}_[A-z0-9]{5,8}.fcs", flags = re.X | re.I)

	#PanelFiles=re.compile("PANEL[\W_]+[AB][AB][A-Z][A-Z][A-Z]_[0-9]{1,6}_[A-z0-9]+[\.]fcs$")
	fullIMPC=re.compile("IMPC[12][\s_-]")

	UnstainedFiles=re.compile("^UNSTAINED[A-z0-9_\-\+]+\.fcs$",flags=re.X | re.I)	

	###LogData contains all filenames and paths as a dictionary, we check against it while looping
					
	##regex expressions
	dateend=re.compile("[2][0][1][0-9][-_][0-9]{0,1}[0-9]{0,1}[_-][0-3]{0,1}[0-9]$")
	datex=re.compile("[2][0][1][0-9][-_][0-9]{0,1}[0-9]{0,1}[_-][0-3]{0,1}[0-9]")
	impx=re.compile("IMPC[\W\-_]+[12]")
	xlsex=re.compile("xls$|xlsx$")
	ignorepaths=re.compile("(Pending[\W]+analysis)|(BMS[\W\-_]+MICE)|(IMPC[\W]+Non[\W]+Submission)|(Blood[\W_\-]+Documents)",flags=re.X|re.I)
	##

	#print logdata
	#sys.exit()	


	Excel_runs=defaultdict(list)
	Excel_paths=defaultdict(list)


	xl_path_re = re.compile(r"/home/clarkg/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES(/IMPC RUNS){0,1}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/Analysis[\-_]201[4567][\-_][0-9]{2}[\-_][0-9]{2}/IMPC[\W\-_]*[12]$",re.IGNORECASE)
	fcs_path_re = re.compile(r"/home/clarkg/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES(/IMPC RUNS){0,1}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/IMPC_96[\W]+Well[\W\-_]{2,4}U[\W]+bottom$")
	
	for root, dirs, files in os.walk(path,topdown=True):
		path = root.split('/')
		base=path[-1]
		dev_=os.statvfs("/")
		mem_remaining=(dev_.f_bavail*dev_.f_frsize)/(1048576*1000)	##GB Left	
		#print mem_remaining
		if mem_remaining < 3:
			print "Less than 3Gb remaining so we'll just leave it there...thanks"
			sys.exit()
		try:
			analysisdir=path[-2]
			datedir=path[-3]
			rawdates=datex.findall(datedir)
			nesteddata=path[-4]
			currentExperiment=datedir
			#if any(ignorepaths.match(p) for p in path):
				#These are not proper FCS files or analysis paths that we are interested in
				pass
			if xl_path_re.match(root) and datex.search(datedir) and datex.search(nesteddata):
				#print base,analysisdir,datedir,nesteddata
				currentExperiment=datedir
				xls=filter(lambda f: xlsex.search(f),files)
				excelfiles=map(lambda l: os.path.join(root,l),xls)
				for xl in xls:
					filetocopy=os.path.join(path,xl)
					cmd="cp "+filetocopy+" /home/clarkg/"
					print datedir,path,xl
				Excel_samples=GetSampleNames("Excel",excelfiles,datedir)
				#print datedir,"Excel",",".join(Excel_samples)
		
			if fcs_path_re.match(root) and (any(FluoroMatch.match(f) for f in files) or any(FMOfiles.match(f) for f in files)):
				#print "FluoroFiles",currentExperiment,datedir,"\t",path#base,compDir.match(base)
				currentExperiment=datedir
				alldates=re.findall(datex,root)
				#FcompFiles=map(lambda l: root+"/"+l,filter(lambda f: FluoroMatch.match(f), files))
				FmoFiles=map(lambda l: root+"/"+l,filter(lambda f: FMOfiles.match(f),files))
				Panels=map(lambda l: root+"/"+l,filter(lambda f: PanelFiles.match(f),files))
				#print datedir,"\t\t\t",base
				
				if len(set(alldates)) == 1:
					datedir=alldates[0]
					FCS_samples=GetSampleNames("FCS",Panels,datedir)
		except IndexError:
			pass

if __name__ == "__main__":


	cnx=mdb.connect('127.0.0.1','root','F!shpr1c','musmusculims')
	cur=cnx.cursor()

	#FindFlowFiles("/home/clarkg/FCS/2014 IMPC  FCS FILES/")
	FindFlowFiles("/home/clarkg/FCS/2015 IMPC  FCS FILES/")
	#FindFlowFiles("/home/clarkg/FCS/2016 IMPC FCS FILES/")
