#!/usr/bin/env python

import string, re, sys
#from fuzzywuzzy import fuzz
sys.path.append("/home/clarkg/anaconda2/lib/python2.7/site-packages")
sys.path.append("/home/clarkg/PythonSite/")
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
from DBwrap import MDB as dbw
import MySQLdb as mdb

dbins=dbw()
sys.exit()

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

	connA,impcdb=dbins.connect(db_env='PROD',local_db='impc')
	connB,musculusdb=dbins.connect(db_env='PROD',local_db='musmusculims')
	cnx,cur=mdb.connect(db_env='DEV',local_db='musmusculims')


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
	curDate=datetime.datetime.today().strftime("%Y_%m_%d")
	fileIO=open(curDate+"_"+"Flow_data.csv",'w')	

	fileIO.write("Experiment_Date,Strain_Code,Colony_ID,Ear_Tag,Genotype,Sex,Mouse_Number,FCS_Files_A,FCS_Files_B"+","+",".join(allparams)+"\n")
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
		
		for mouse in ExperimentMice:
			print run,mouse
			if mouse in ["B6NC_002","B6NC_017","B6NC_010","B6NC_026"]:
				pass
			else:
				FCSfiles=filter(lambda k: re.search(mouse,k),EXPf)
				PfileA=filter(lambda p: re.match("PANEL[\W_]A",p,flags=re.X|re.I),FCSfiles)
				PfileB=filter(lambda p: re.match("PANEL[\W_]B",p,flags=re.X|re.I),FCSfiles)
		#		print PfileA,PfileB
				if len(PfileA) != 1:
					print "NOOONE A",mouse,FCSfiles
				if len(PfileB) != 1:
					print "NOOONE B",mouse,FCSfiles
				PfileA=PfileA[0]
				PfileB=PfileB[0]

				wStrain,wTag=mouse.strip().split("_")
				wDate=run
				if wStrain == "B6NC":
					genotype="WT"
					colony=["NA"]
				else:
					impcdb.execute("""select COLONYNAME from impc_Mouseline where straincode = %s""" ,(wStrain,))
					colony=impcdb.fetchall()[0]

				try:			
					impcdb.execute("""select ml.GENESYMBOL,e.zygosity,e.Gender,e.IMPC_specimen_Id from impc_Mice e join impc_Mouseline ml
					 on e.mouseline = ml.mouseline_id 
					 where straincode = %s and sampleid = %s""", (wStrain,wTag)) 
					retimpc=impcdb.fetchall()[0]
					retmus=False
				except (mdb.Error,IndexError),e:
					retimpc=False
					try:
						musculusdb.execute("""Select mg.gtGenotype_text from Mice2 m join Mice_genotype mg 
								on m.zmUID = mg.zmUID 
								where m.mStrainCode = %s and m.mEarTag=%s""", (wStrain,wTag))
						retmus=musculusdb.fetchall()[0]
					except (mdb.Error,IndexError),e:
						retmus=False	
				if retimpc:
					geneSymbol,zygosity,gender,dcc_id=retimpc
				else:
					geneSymbol,zygosity,gender,dcc_id="NA","NA","NA","NA"
				if geneSymbol is None:
					genotype='WT'
				else:
					genotype=geneSymbol+zygosity
				writeLine=""#map(lambda s: str(s),doOrder[mouse])
				if dcc_id is None:
					dcc_id=""
				if colony[0] is None:
					colony=[""]	
				try:
					stringdata=",".join([wDate,wStrain,colony[0],wTag,genotype,gender,dcc_id,PfileA,PfileB])
				except:
					print wDate,wStrain,colony[0],wTag,genotype,gender,dcc_id,PfileA,PfileB

				fileIO.write(stringdata+","+",".join(writeLine)+"\n")

	
#	
	fileIO.close()
	

	wlog.close()	
	os.system("mv -f ./_logFiles_/TempLog.txt ./_logFiles_/ParsedFiles.log")
	cur.close()
	cnx.close()	
