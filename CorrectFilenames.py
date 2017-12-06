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
	correctFMO=re.compile("""FMO_PANEL_(A|B)_(CD62L|CD25|CD8A|CD23|TCRD|MHCII|CD161|CD11B|CD44|CD21-35|CD21,2f,35|LY6C|CD11C|CD5)""",flags=re.X)

	MatrixF=re.compile("""[A-z0-9\s_\-,]+MATRIX[A-z0-9\s_\-,]+[\.]mtx""",flags=re.X|re.I)
	# traverse root directory, and list directories as dirs and files as files
	#print "COMMONPATH: %s" % commonpath


	PanelFiles=re.compile("PANEL[\W_]{0,3}[AB][\W_]{1,2}[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}_[A-z0-9]{5,8}.fcs", flags = re.X | re.I)
	#PANEL_A_ABDR_92_C6C06008.fcs
	#correctPanel=re.compile("PANEL_[AB]_[AB][A-Z6][A-Z][A-Z]_[0-9]{2-3}_[BCFH][0-9][BCFH][0-9]{3,5}.fcs",flags=re.X)
	#correctPanel=re.compile("PANEL_[AB]_[AB][A-Z6][A-Z][A-Z]_[0-9]{1-3}_[A-Z0-9]{3,8}.fcs",flags=re.X)
	correctPanel=re.compile("PANEL_[AB]_[AB][A-Z6][A-Z][A-Z]_[0-9]{1,4}_[A-z_0-9]+.fcs",flags=re.X)


	UnstainedFiles=re.compile("^UNSTAINED[A-z0-9_\-\+]+\.fcs$",flags=re.X | re.I)	

	###LogData contains all filenames and paths as a dictionary, we check against it while looping
					
	##regex expressions
	dateend=re.compile("[2][0][1][0-9][-_][0-9]{0,1}[0-9]{0,1}[_-][0-3]{0,1}[0-9]$")
	datex=re.compile("[2][0][1][0-9][-_][0-9]{0,1}[0-9]{0,1}[_-][0-3]{0,1}[0-9]")
	impx=re.compile("IMPC[\W\-_]+[12]")
	##

	spltR=re.compile("(?<!^)PANEL_[AB]_(CD62L|CD25|CD8A|CD23|TCRD|MHCII|CD161|CD11B|CD44|CD21,2f,35|LY6C|CD11C|CD5)")#.split("Hoggens392_Porls")
#	finalFMO=re.compile("FMO_PANEL_[AB]_(CD62L|CD25|CD8A|CD23|TCRD|MHCII|CD161|CD11B|CD44|CD21,2f,35|LY6C|CD11C|CD5)_[A-z0-9]+.fcs")#.split("Hoggens392_Porls")
	finalFMO=re.compile("FMO_PANEL_[AB]_(CD62L|CD25|CD8A|CD23|TCRD|MHCII|CD161|CD11B|CD44|CD21-35|LY6C|CD11C|CD5)_[A-z0-9]+.fcs")#.split("Hoggens392_Porls")


	#def FMO_Repeater(filenamein):

	llp=open("bashqc.sh",'w')
	llp.write("#!/bin/bash\n")
	collectErrors=defaultdict(list)
	for root, dirs, files in os.walk(path,topdown=True):
		path = root.split('/')
		base=path[-1]
		try:
			
			if datex.match(base) and (any(FluoroMatch.match(f) for f in files) or any(FMOfiles.match(f) for f in files)):
				datedir=base
				#print "FluoroFiles",currentExperiment,datedir,"\t",path#base,compDir.match(base)
				alldates=re.findall(datex,root)
				#FcompFiles=map(lambda l: root+"/"+l,filter(lambda f: FluoroMatch.match(f), files))
				FmoFiles=map(lambda l: root+"/"+l,filter(lambda f: FMOfiles.match(f),files))
				Panels=map(lambda l: root+"/"+l,filter(lambda f: PanelFiles.match(f),files))
				Unstained=map(lambda l: root+"/"+l,filter(lambda f: UnstainedFiles.match(f),files))
				#print datedir,"\t\t\t",base
				
				if len(set(alldates)) == 1:
					#datedir=alldates[0]
				#	print datedir,"Controls"
					for fmo in FmoFiles:
						originalfilename=fmo.split("/")[-1].strip()
						if re.search("PANELA",originalfilename):
							newname=originalfilename.split("PANELA")[1]
							fmofilename="FMO_PANEL_A"+newname
						else:
							fmofilename=originalfilename
						if not correctFMO.match(fmofilename):
							print datedir,fmofilename	#,correctFMO.match(fmofilename)
							print os.path.join(root,fmofilename)
							print "FIX THIS"
							sys.exit()
							collectErrors[datedir].append(fmofilename)
						elif finalFMO.match(originalfilename):
							pass
						else:
							jkp=spltR.split(fmofilename)
							tol=spltR.findall(fmofilename)
							if re.search("PANEL_A",fmofilename):
								newname=jkp[0]+"PANEL_A_"+jkp[1].rstrip("_")+"_"+jkp[2].lstrip("_")
							elif re.search("PANEL_B",fmofilename):
								newname=jkp[0]+"PANEL_B_"+jkp[1].rstrip("_")+"_"+jkp[2].lstrip("_")
							if tol[0] == "CD21,2f,35":
								newname=newname.replace("CD21,2f,35","CD21-35")
							if not finalFMO.match(newname):
								print "ERROR",fmofilename,newname,"\t",tol
								sys.exit()
							else:
								cmd="mv "+os.path.join(root,originalfilename)+" "+os.path.join(root,newname)
								llp.write(cmd+"\n")
					for pfile in Panels:
						pfilename=pfile.split("/")[-1].strip()
						if not correctPanel.match(pfilename):
							if re.match("PANELA",pfilename):
								newname=pfilename.split("PANELA")[0]
								pfilename="PANEL_A"+newname
								print newname,pfilename
							if not correctPanel.match(pfilename):
								print datedir,pfilename, correctPanel.match(pfilename)
								print "FIX PANEL NAMES"
								sys.exit()
				#		print pfile
				#	for ufile in Unstained:
				#		print ufile
		except IndexError:
			pass
	llp.close()
	#allDerrs=collectErrors.keys()
	#allDerrs.sort()
	#for d in allDerrs:
	#	print d,collectErrors[d]

if __name__ == "__main__":


	#cnx=mdb.connect('127.0.0.1','root','F!shpr1c','musmusculims')
	#cur=cnx.cursor()

	#FindFlowFiles("/home/clarkg/FCS/2014 IMPC  FCS FILES/")
	#FindFlowFiles("/home/clarkg/FCS/2015 IMPC  FCS FILES/")
	FindFlowFiles("/home/clarkg/FLOWcyto/UPLOAD_DUMP/")
