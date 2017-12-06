#!/usr/bin/env python

import string, re, sys
from FlowClass.LiteUtils import FlowUtilities
import glob
import os
import re
import time


func=FlowUtilities()

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

UnstainedFiles=re.compile("^UNSTAINED[A-z0-9_\-\+]+\.fcs$",flags=re.X | re.I)	
UnstainedSytox=re.compile("^UNSTAINED[A-z0-9_\-\+]+SYTOXBLUE[A-Z0-9_]+\.fcs$",flags=re.X | re.I)	


#PANEL_A
cd5_A=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD5[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd161_A=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD161[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd44=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD44[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd8a=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD8A[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd62l=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD62L[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd25=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD25[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)

#PANEL_B
cd5_B=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD5[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd161_B=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD161[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd11B=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD11B[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd11C=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD11C[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
mhc=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_MHCII[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd21_35=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD21(,2f,){0,1}[,\-\\/]{0,1}35[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
cd23=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD23[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
ly6c=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_LY6C[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)


FMOfiles=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}(A|B)""",flags=re.X|re.I)


##IMPC_96 Well - U bottom'
compDir=re.compile("IMPC[\W_]+96[\W_]+Well[\W_]+U[\W_]+bottom",flags=re.X | re.I)
PanelFiles=re.compile("PANEL[\W_]{0,3}[AB][\W_]{1,2}[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}_[A-z0-9]{5,8}.fcs", flags = re.X | re.I)
ProperCode=re.compile("[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}", flags = re.X | re.I)


def FindFMOfiles(files,dDate):
	CD62Ldate = time.strptime("2016-08-01", "%Y-%m-%d")
	matchA={'CD5_A':False,
		 'CD161_A':False,
		 'CD44':False,
		 'CD8A':False,
		 'CD62L':False,
		 'CD25':False}

	#print  dDate > CDL62Ldate
	matchB={'CD5_B':False,
		 'CD161_B':False,
		 'CD11B':False,
		 'CD11C':False,
		 'MHCII':False,
		 'CD23':False,
		 'LY6C':False,
		 'CD21_35':False}
	##Control for CD62L started use August 2016 2016-08-01
	
	cd62lcut=dDate < CD62Ldate
	## We can take the full path here
	for filename in files:
		f=filename.split("/")[-1]
		if cd5_A.match(f):
			matchA['CD5_A']=True		
		elif mhc.match(f):
			matchB['MHCII']=True
		elif cd161_A.match(f):
			matchA['CD161_A']=True		
		elif cd44.match(f):
			matchA['CD44']=True
		elif cd8a.match(f):
			matchA['CD8A']=True
		elif cd62l.match(f):
			matchA['CD62L']=True
		elif cd25.match(f):
			matchA['CD25']=True
		elif cd5_B.match(f):
			matchB['CD5_B']=True
		elif cd161_B.match(f):
			matchB['CD161_B']=True
		elif cd11B.match(f):
			matchB['CD11B']=True
		elif cd11C.match(f):
			matchB['CD11C']=True
		elif cd23.match(f):
			matchB['CD23']=True
		elif ly6c.match(f):
			matchB['LY6C']=True
		elif cd21_35.match(f):
			matchB['CD21_35']=True
	
	FailedA={k: v for k, v in matchA.iteritems() if v == False}
	if cd62lcut:
		del FailedA['CD62L']
	FailedB={k: v for k, v in matchB.iteritems() if v == False}
	return FailedA,FailedB	

def unstainedCheck(files):
	##Assume missing until otherwise
	unstained=True
	sytox=True
	for filename in files:
		f=filename.split("/")[-1]
		if UnstainedFiles.match(f):
			unstained=False
		if UnstainedSytox.match(f):
			sytox=False
	return unstained,sytox			

dirs=glob.glob("./UPLOAD_DUMP/*")
dirs.sort()


CDL62Ldate = time.strptime("2016-08-01", "%Y-%m-%d")

for dir in dirs:
	ExpDate=dir.split("/")[-1]
	dDate= time.strptime(ExpDate, "%Y-%m-%d")
	print ExpDate

	allfiles=glob.glob(os.path.join(dir,"*"))



	fcsfiles=filter(lambda f: PanelFiles.match(f.split("/")[-1]),allfiles)
	xlfiles=filter(lambda f: f.endswith("xls"),allfiles)
	fmoControls=filter(lambda f: f.split("/")[-1].startswith("FMO"),allfiles)
	unstained,sytox=unstainedCheck(allfiles)
	failA,failB=FindFMOfiles(fmoControls,dDate)
	if unstained == True:
		print "Unstained FMO file missing"
	elif sytox == True:
		print "Unstained Sytox file missing"

	if failA:
		print ExpDate,failA
	if failB:
		print ExpDate,failB

	allXL_=map(lambda k: func.open_xls_as_xlsx(k,ExpDate),xlfiles)
	allFCS_=map(lambda k: func.FCScheck(k)[0],fcsfiles)
	uqFCS_=map(lambda s : "_".join(str(s).split("_")[:2]),allFCS_)

	flatXL_=list(set([item for sublist in allXL_ for item in sublist]))	
	flatFCS_=list(set(uqFCS_))	
	XLnames = map(lambda s: ProperCode.findall(s)[0], flatXL_)
	XLnames.sort()

	diffFile=list(set(flatFCS_).difference(set(XLnames)))
	diffFile+=list(set(XLnames).difference(set(flatFCS_))) 

	if failA or failB or len(diffFile):
		fileio=open(os.path.join(dir,"_logfile.txt"),'w')
		fileio.write("Log file for Experiment: %s.\n\n" % ExpDate)
		fileio.write("The following anomalies were found:\n")
		if len(failA):
			for k,l in failA.items():
				misstxt=u'\n\t\u29BF We are missing %s control from Panel A in the experiment folder.\n' % k
                                fileio.write(misstxt.encode("UTF-8"))
				#fileio.write("\tWe are missing %s control from Panel A in the expeiment folder.\n" % k) 
		if len(failB):
			for k,l in failB.items():
				misstxt=u'\n\t\u29BF We are missing %s control from Panel B in the experiment folder.\n' % k
                                fileio.write(misstxt.encode("UTF-8"))
				#fileio.write("\tWe are missing %s control from Panel B in the expeiment folder.\n" % k)
	
		if unstained:
			misstxt=u'\n\t\u29BF We are missing the UNSTAINED control.\n' 
			fileio.write(misstxt.encode("UTF-8"))
		if sytox:
			misstxt=u'\n\t\u29BF We are missing the UNSTAINED SYTOX control.\n' 
			print misstxt
			fileio.write(misstxt.encode("UTF-8"))
	
		if len(diffFile):
			missingXL=[]
			missingFCS=[]

			for sn in diffFile:
				if sn in XLnames:
					missingFCS.append(sn)
				elif sn in flatFCS_:
					missingXL.append(sn)
			if missingFCS:
				print "Samples missing from FCS files: %s" % ",".join(missingFCS)
				stringio=u'\t\u29BF Samples missing from FCS files\n'
				fileio.write(stringio.encode("UTF-8"))
				for k in missingFCS:
					missF=u'\t\t\u2981 '+k+'\n'
					fileio.write(missF.encode("UTF-8"))
			if missingXL:
	#			print "Samples missing from Excel files: %s" % ",".join(missingXL)
				stringio=u'\t\u29BF Samples missing from Excel files\n'
				fileio.write(stringio.encode("UTF-8"))
				for k in missingXL:
					k=str(k.lstrip("(u\'"))
					#print k
					missF=u'\t\t\u2981 '+k+'\n'
					fileio.write(missF.encode("UTF-8"))

	fileio.close()
