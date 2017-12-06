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
from FlowClass.Regex import rgx
from FlowClass.Logging import Log as logging

logging.log=True




#basedir="/home/clarkg"
basedir="/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/"
statvfs=os.statvfs(basedir)


#completed=map(lambda k: k.strip(),open("completed.txt",'r').readlines())
#completed.sort()

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


def overwrite_protect(path,infile):
	listings=glob.glob(os.path.join(path,'*'))
	fileexists=False
	nameexists=False
	for l in listings:
		if filecmp.cmp(l,infile):
			fileexists=True 
		rawname=l.split("/")[-1].strip()
		if rawname == infile:
			nameexists=True
		#print f,a,filecmp.cmp(f,a)
	if not fileexists and not nameexists:
		copy(infile,path)
	if not fileexists and nameexists:
		print "DIFFERENT FILE BUT NAME IS SAME, WAAAAG"

#controlfiles={}
#fmofiles={}
#excelfiles={}
#matrixfiles={}
allfiles=defaultdict(list)

def FindFlowFiles(path):

	if not len(path):
		path="."
	

	Excel_runs=defaultdict(list)
	Excel_paths=defaultdict(list)

	for root, dirs, files in os.walk(path,topdown=True):
		path = root.split('/')
		base=path[-1]
		dev_=os.statvfs("/")
		mem_remaining=(dev_.f_bavail*dev_.f_frsize)/(1048576*1000)	##GB Left	
		#print mem_remaining
		if mem_remaining < 10:
			print "Less than 10Gb remaining so we'll just leave it there...thanks"
			sys.exit()
		try:
			analysisdir=path[-2]
			datedir=path[-3]
			rawdates=rgx.datex.findall(datedir)
			nesteddata=path[-4]
			currentExperiment=datedir
			#print root
			if rgx.xl_path_re.match(root) and rgx.datex.search(datedir) and rgx.datex.search(nesteddata):
				currentExperiment=datedir
				#print currentExperiment
				#print "XLS",files
				xls=filter(lambda f: rgx.xlsex.search(f),files)
				excelfiles=map(lambda l: os.path.join(root,l),xls)
				Matrices=map(lambda l: root+"/"+l,filter(lambda f: rgx.MatrixF.match(f),files))
				Workspace=map(lambda l: root+"/"+l,filter(lambda f: rgx.wspFiles.match(f),files))
				if datedir not in logging.memfile:
					writepath=os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP",str(datedir))
					if not os.path.isdir(writepath):
						os.makedirs(os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP",str(datedir)))
			#		for efile in excelfiles:
			#			overwrite_protect(writepath,efile)	
					for ufile in Matrices:
						overwrite_protect(writepath,ufile)
				else:
					pass
					#print "passing",datedir
			if rgx.fcs_path_re.match(root) and (any(rgx.FluoroMatch.match(f) for f in files) or any(rgx.FMOfiles.match(f) for f in files)):
				#print "Yeeaaaah",root
				#print "FluoroFiles",currentExperiment,datedir,"\t",path#base,compDir.match(base)
				currentExperiment=datedir
				#alldates=re.findall(datex,root)
				alldates=re.findall(rgx.datex,root)

				#Not concerned with Compensation Files
				#FcompFiles=map(lambda l: root+"/"+l,filter(lambda f: FluoroMatch.match(f), files))
			#	print currentExperiment
			#	print "FCS",files
				FmoFiles=map(lambda l: root+"/"+l,filter(lambda f: rgx.FMOfiles.match(f),files))
				Panels=map(lambda l: root+"/"+l,filter(lambda f: rgx.PanelFiles.match(f),files))
				Unstained=map(lambda l: root+"/"+l,filter(lambda f: rgx.UnstainedFiles.match(f),files))
				Sytox=map(lambda l: root+"/"+l,filter(lambda f: rgx.UnstainedSytox.match(f),files))
				Matrices=map(lambda l: root+"/"+l,filter(lambda f: rgx.MatrixF.match(f),files))
				Workspace=map(lambda l: root+"/"+l,filter(lambda f: rgx.wspFiles.match(f),files))
				#Workspace	
				if len(set(alldates)) == 1:
					datedir=alldates[0]
				#	print datedir,"Controls"
					if datedir not in logging.memfile:
						writepath=os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP",datedir)
						if not os.path.isdir(writepath):	os.makedirs(writepath)
						for fmo in FmoFiles:
							overwrite_protect(writepath,fmo)	
						for pfile in Panels:
							overwrite_protect(writepath,pfile)
						for ufile in Unstained+Sytox:
							overwrite_protect(writepath,ufile)
						for ufile in Matrices:#+Matrices:
							overwrite_protect(writepath,ufile)
						#Brinkman doesn't care about Compensation Files
						#for fcomp in FcompFiles:
						#	overwrite_protect(writepath,fcomp)
				#		logging.memfile.append(currentExperiment)
				elif len(set(alldates)) > 1:
					print "Multiple dates",list(set(alldates))
				#	print len(Ffiles),len(FmoFiles),datedir
				#print currentExperiment,len(Ffiles)#,Ffiles
				#print currentExperiment,len(FmoFiles)#,FmoFiles
		except IndexError:
			pass
		#print "\n\n"

if __name__ == "__main__":


	#cnx=mdb.connect('127.0.0.1','root','F!shpr1c','musmusculims')
	#cur=cnx.cursor()

	#FindFlowFiles("/home/clarkg/FCS/2014 IMPC  FCS FILES/")
	#FindFlowFiles("/home/clarkg/FCS/2015 IMPC  FCS FILES/")
	#FindFlowFiles("/home/clarkg/FCS/2016 IMPC FCS FILES/")
	logger=logging()
	
	logger.log=True
	logging.start_log(logger)
	#FindFlowFiles("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2016 IMPC FCS FILES/")
	FindFlowFiles("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2016 IMPC FCS FILES/")
	#FindFlowFiles("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2017 IMPC FCS FILES/")
	logging.end_log(logger)
