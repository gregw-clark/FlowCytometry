#!/usr/bin/env python

import string, re, sys
from FlowClass.LiteUtils import FlowUtilities
import glob
import os
import re
from FlowClass.Regex import rgx  
#sys.path.append("/home/clarkg/PythonSite/")
#from DBwrap import MDB as dbw
#import MySQLdb as mdb
func=FlowUtilities()






#print 

#infile=open("checkThese.txt",'r').readlines()
infile=open("singleCheck.txt",'r').readlines()

for exp in infile:
	experiment=exp.strip()

	try:
		#experiment=sys.argv[1].strip()
		expMatch=re.compile("201[4567]-[0-9]{2}-[0-9]{2}$")
		if not expMatch.match(experiment):
			print "\n\n\n"
			print "\t\tThis is not a suitable date\n"
			print "\t\t\t...Use format \'YYYY-MM-DD\'"
			print "\n\n\n"
			sys.exit()
		else:
			yearBase=experiment.split("-")[0]
	except IndexError:
		print "\n\n\n"
		print "\t\tPlease enter experiment date in format \'YYYY-MM-DD\'"
		print "\n\n\n"
		sys.exit()

	if yearBase == "2014":
		base_path=os.path.join("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2014 IMPC  FCS FILES/",experiment,experiment)
	elif yearBase == "2015":
		base_path=os.path.join("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2015 IMPC  FCS FILES/",experiment,experiment)
	elif yearBase =="2016":
		base_path=os.path.join("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2016 IMPC FCS FILES",experiment,experiment)
	elif yearBase =="2017":
		base_path=os.path.join("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/2017 IMPC FCS FILES",experiment,experiment)
	else:
		print "\n\n\n"
		print "\t\tSomething wrong with yearBase,\n\t\t\tplease enter experiment date in format \'YYYY-MM-DD\'"
		print "\n\n\n"


	matches=[]
	for root, dirnames, filenames in os.walk(base_path):
		matches.extend(os.path.join(root,name) for name in filenames if rgx.file_re.match(name) and (rgx.fcs_path_re.match(root) or rgx.xl_path_re.match(root)))
	matches.sort()

	print "\n\n\nSearch for experiment: %s\n\n" % experiment

	fcsfiles=filter(lambda f: rgx.PanelFiles.match(f.split("/")[-1]),matches)
	xlfiles=filter(lambda f: f.endswith("xls"),matches)

	allXL_=map(lambda k: func.open_xls_as_xlsx(k,experiment),xlfiles)
	allFCS_=map(lambda k: func.FCScheck(k),fcsfiles)


	FCS_sampleNames=map(lambda s : "_".join(str(s[0]).split("_")[:2]),allFCS_)
	FCS_fileNames=map(lambda s : s[1],allFCS_)


	if FCS_sampleNames != FCS_fileNames:
		ErrorFiles=True
		print "\t\tFCS binary sample names not matching file sample names"
		SampleNames=list(set(FCS_sampleNames))
		FileNames=list(set(FCS_fileNames))
		print "Sample",list(set(FCS_sampleNames))
		print "File:",list(set(FCS_fileNames))
	else:
		FileNames=list(set(FCS_fileNames))

	flatXL_=list(set([item for sublist in allXL_ for item in sublist]))	
	flatFCS_=list(set(FCS_sampleNames))	

	XLnames = map(lambda s: rgx.ProperCode.findall(s)[0], flatXL_)
	XLnames.sort()

	diffFile=list(set(flatFCS_).difference(set(XLnames)))
	diffFile+=list(set(XLnames).difference(set(flatFCS_))) 

	flatFCS_.sort()

	allnames=XLnames+flatFCS_+FCS_fileNames
	uqnames=list(set(allnames))

	if not len(diffFile):
		print "\nAll sample names are in agreement between FCS and manual files.\n"
		prettysample=u'Sample Names:\n\t\t\u2981'+u'\n\t\t\u2981'.join(uqnames)
		print prettysample.encode("UTF-8")
		print "\n"
	if len(diffFile):
		missingXL=[]
		missingFCS=[]
		errornames=[m for m in uqnames if allnames.count(m) < 3]
#		print experiment,errornames 
		for sn in diffFile:
			if sn in XLnames:
				missingFCS.append(sn)
			elif sn in flatFCS_:
				missingXL.append(sn)
		if missingFCS:
#			print "\n\n\n"
#			print "\t\texperiment\t\tMissing in FCS: %s" % ",".join(missingFCS)
#			print "\n\n"
			stringio=u'\t\u29BF Missing from FCS file\n'
		#	fileio.write(stringio.encode("UTF-8"))
			for k in missingFCS:
				missF=u'\t\t\u2981 '+k+'\n'
		#		fileio.write(missF.encode("UTF-8"))
			
		if missingXL:
#			print "\n\n\n"
#			print "\t\texperiment\t\tMissing in Excel: %s" % ",".join(missingXL)
#			print "\n\n"
			stringio=u'\t\u29BF Missing from Excel File\n'
			#fileio.write(stringio.encode("UTF-8"))
			#for k in missingXL:
			#	missF=u'\t\t\u2981 '+k+'\n'
			#	fileio.write(missF.encode("UTF-8"))

