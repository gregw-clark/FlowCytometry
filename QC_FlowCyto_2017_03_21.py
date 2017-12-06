#!/usr/bin/env python

import string, re, sys
#from fuzzywuzzy import fuzz
sys.path.append("/home/clarkg/anaconda2/lib/python2.7/site-packages")
import xlrd
import collections
from collections import defaultdict
import os
import datetime
from pandas import DataFrame
import numpy as np
import operator
import csv
import time
import MySQLdb as mdb
import smtplib
import scipy.stats as ss
from scipy.stats.kde import gaussian_kde
import math
from sklearn.neighbors import KernelDensity
from FlowClass.FlowUtils import FlowUtilities,FlowData,MouseData
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw


dbins=dbw()


homepath="/home/clarkg/FLOWcyto"
datapath="/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/"
os.chdir(homepath)
reload(sys)  
sys.setdefaultencoding('utf8')

nx=FlowUtilities()

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


if __name__ == "__main__":

	impc_order=nx.panelsToimpc("/home/clarkg/FLOWcyto/FlowClass/MatchingColumns.xls")

	nx.FindNewExperiments(datapath)
	nx.findXLfiles("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/")
	###nx.ExperimentDirs has Experiment Date as key and common path as value
	###nx.ExperimentExcels has Experiment Date as key and {Excel_Filename:Excel_path} as value

	allparams=impc_order.keys()
	allparams.sort()

	## We will populate all past IMPC data into dictionary for QC purposes
	## nx.PastParameterData (e.g. nx.PastParameterData['IMPC_IMM_015_001']=[32322,23131,23132,43243,23311...]


	cnx,cur=dbins.connect(db_env='PROD',local_db='musmusculims')


	##initialize new log file
	f=open("./_logFiles_/ParsedFiles.log",'r').read()

	os.system("cp ./_logFiles_/ParsedFiles.log ./_logFiles_/ParsedFiles.bak")

	wlog=open("./_logFiles_/TempLog.txt",'w')
	wlog.write(f)
	##

	#IMData=defaultdict(list)
	allruns=defaultdict(list)
	ordered=nx.ExperimentDirs.keys()
	ordered.sort()

	nx.get_IMPCData(allparams)
	mice=MouseData()	
	impcQuery=False
	logline=[]	


	for run in ordered:
		print "Parsing folder...",run
		commonpath=nx.ExperimentDirs[run]
		dx=FlowData(nx)
	
		if run in nx.ExperimentExcels:
			#print nx.ExperimentExcels
			dx.open_xls_as_xlsx(run,"A",nx)
			dx.open_xls_as_xlsx(run,"B",nx)
		#wlog.write(time.strftime("%c")+"\t"+Excel_paths[run][0]+"\t"+Excel_runs[run][0]+"\n")
		#wlog.write(time.strftime("%c")+"\t"+Excel_paths[run][1]+"\t"+Excel_runs[run][1]+"\n")
		#logline.append(time.strftime("%c")+"\t"+Excel_paths[run][0]+"\t"+Excel_runs[run][0]+"\n")
		#logline.append(time.strftime("%c")+"\t"+Excel_paths[run][1]+"\t"+Excel_runs[run][1]+"\n")

		dx.currentExperiment=run

		dx.FindFCSFiles(commonpath)

		ExperimentMice=list(set(dx.MouseIDS.values()[0]))
		#print ExperimentMice
		#sys.exit()
		fcsMice=dx.MouseIDS.keys()
		ExperimentMice.sort()
		CMPf=set(dx.CompensationFiles.values()[0])
		FMOf=set(dx.FMOControlFiles.values()[0])
		EXPf=set(dx.ExperimentFiles.values()[0])
		MissingFMOpanelA,MissingFMOpanelB=dx.FindFMOfiles()
		if len(MissingFMOpanelA):
			dx.ErrorEmailText+='\t\tThe experiment is missing a file from Panel A for control(s):\t'
			dx.ErrorEmailText+=",".join(MissingFMOpanelA)+"\n\n"
			dx.FatalError=True
		if len(MissingFMOpanelB):
			dx.ErrorEmailText+='\t\tThe experiment is missing a file from Panel B for control(s):\t'
			dx.ErrorEmailText+=",".join(MissingFMOpanelB)+"\n\n"
			dx.FatalError=True
		for f in FMOf:	dx.fcsextract(f)	
		for f in EXPf:	dx.fcsextract(f)	

		if dx.ControlMissing:
			dx.ErrorEmailText+="\n\n"
			dx.ErrorEmailText+="\t\tThe following files are missing named controls:\n"
			for k,l in dx.ControlMissing.iteritems():
				dx.ErrorEmailText+="\t\t\tFile \'%s\' is missing \'%s\'.\n" % (k,",".join(l))
				dx.FatalError=True
			dx.ErrorEmailText+="\n"
		if dx.ControlAdded:
			dx.ErrorEmailText+="\n\n"
			dx.ErrorEmailText+="\t\tThe following files have an anomalous control:\n"
			for k,l in dx.ControlAdded.iteritems():
				dx.ErrorEmailText+="\t\t\tFile \'%s\' has added marker(s) \'%s\'.\n" % (k,",".join(l))
				dx.FatalError=True
			dx.ErrorEmailText+="\n"
		NamingErrors=dx.ErrorProne.values()
		if len(NamingErrors):
			NamingErrors=NamingErrors[0]
		
		mice_text=""
		#if oIM:
		if dx.IMData:
			oIM=collections.OrderedDict(sorted(dx.IMData.items()))
			if not impcQuery:
				impcQuery=oIM.keys()

			ExcelMice=["_".join(f[1].split("_")[1:]) for f in oIM[oIM.keys()[0]]]
			Esetorder=list(set(ExcelMice))
			Expsetorder=list(set(ExperimentMice))
			Esetorder.sort()
			Expsetorder.sort()
			if set(ExcelMice) == set(ExperimentMice):
				mice_text=u'\u2460'+" Mouse Strain Codes and Ear Tags were confirmed in FCS files and Excel Files.\n\n"
			else:
				mice_text="\n\n\n"+u'\u2460'+" "+u'\u26A0'+""" Mouse IDS DISAGREE between FCS files and Excel Files!"""+u'\u26A0'+"\n\n\n"
				print "Error with MICE NAMES!"
				print "Excel Sheet Mice: %s" % ",".join(Esetorder)
				print "FCS file Mice: %s" % ",".join(Expsetorder)
			dx.FindMouseOutliers(nx.PastParameterData,oIM)
			for k in oIM:
				mice.paramOrder.append(k)
				ldat=zip(*oIM[k])
				try:
					for c,v in zip(ldat[0],ldat[1]):
						allruns[k].append([v,c])
						mice.data[v].append(c)
				except IndexError:
					dx.FatalError=True
					dx.ErrorEmail+="\t\tMissing data %s and %s\n\t\tCheck the names of the Mice in the spreadsheets.\n" % (k,ldat)
	
		donotreply="\t\t"+u'\u26A0'+" Do not reply to this email. "+u'\u26A0'+"\n\n"
		donotreply=donotreply.encode('utf-8')
		
		dx.EmailText+=donotreply
		if dx.FatalError:
			initE='\t\t'+u'\u26A0'+'\tFatal Error!\t'+u'\u26A0'+'\n\n\n.'
			initE=initE.encode('utf-8')
			dx.ErrorEmailText=initE+dx.ErrorEmailText
			dx.EmailText+=dx.ErrorEmailText.encode('utf-8')
		else:
			dx.EmailText+=dx.ErrorEmailText.encode('utf-8')

		mice_text+=u'\u2461'+""" The following samples were found in this experiment:\n"""#+ u'\u229b' +",".join(ExperimentMice+ u'\u229b'+"\n\n"
		for j in ExperimentMice:
			#mice_text+="\t"+u'\u229b' +j+"\n"
			mice_text+="\t"+u'\u229b' +j+"\n"
		mice_text+="\n\n"
		mice_text=mice_text.encode('utf-8')

		comp_text=u'\u2462'+""" We find %s Compensation Files.\n""" % len(CMPf)
		comp_text=comp_text.encode('utf-8')


		fmo_text=u'\u2463'+""" We find %s FMO Files.\n""" % len(FMOf)
		fmo_text=fmo_text.encode('utf-8')

		dx.EmailText+=mice_text

		if len(NamingErrors):
			#print NamingErrors
			for x in range(0,len(NamingErrors)):
				filenamed,composite,fullname=NamingErrors[x]
				dx.EmailText+="\n\nFilename and FCS data discrepancy:\n"
				dx.EmailText+="\tFilename: %s.\n" % filenamed
				dx.EmailText+="\t\tComposite Name in FCS file: %s\n" % composite
				dx.EmailText+="\t\tFull Name: %s \n\n" % fullname

		dx.EmailText+=comp_text
		dx.EmailText+=fmo_text
		###

		try:
			#print dx.MatrixFiles.values()[0]
			MATf=set(dx.MatrixFiles.values()[0])
		
			if len(MATf):
				matrix_text="\n\n"+u'\u26AB'+""" We found these matrix files associated with the experiment: %s.\n\n""" % ", ".join(list(MATf))
				matrix_text=matrix_text.encode('utf-8')
				dx.EmailText+=matrix_text
		except:
			pass

		encodedEmail=dx.EmailText.encode('utf-8')
	#	dx.emailUsers(encodedEmail)

		if not dx.FatalError:
			allMice=mice.data.keys()
			allMice.sort()
			for m in allMice: 	mice.qDataBase(cur,m)
			#wlog.write(time.strftime("%c")+"\t"+Excel_paths[run][0]+"\t"+Excel_runs[run][0]+"\n")
			#wlog.write(time.strftime("%c")+"\t"+Excel_paths[run][1]+"\t"+Excel_runs[run][1]+"\n")

	wlog.close()	
	os.system("mv -f ./_logFiles_/TempLog.txt ./_logFiles_/ParsedFiles.log")
	cur.close()
	cnx.close()	
