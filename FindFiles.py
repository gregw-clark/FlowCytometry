#!/usr/bin/env python

import re,sys,os
import math
#from FlowClass.FlowCytometryTools import FCMeasurement
from FlowClass.Regex import rgx
from cPickle import load, dump
import shutil

PanelFiles=re.compile("PANEL[\W_]{0,3}[AB][\W_]{1,2}[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}_[A-z0-9]{2,12}.fcs", flags = re.X | re.I)
def find_missing(path,missed_files):
	gotem=[]
	for root, dirs, files in os.walk(path):
		path = root.split('/')
		base=path[-1]
		try:
			analysisdir=path[-2]
			datedir=path[-3]
			rawdates=rgx.datex.findall(datedir)
			nesteddata=path[-4]
			if rgx.fcs_path_re.match(root):# and rgx.datex.search(datedir) and rgx.datex.search(nesteddata):
			#	print root
				currentExperiment=datedir
			#	print currentExperiment
				for mf in missed_files:
					trnc="_".join(mf.split("_")[:-1])
					#print trnc
					truncated=filter(lambda l: re.search(trnc,l),files)
					if len(truncated) == 1:
				
						if not os.path.exists(os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP/",currentExperiment)):
							os.makedirs(os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP/",currentExperiment))
						#print "\n\n\n"
						#moveit="cp "+os.path.join(root,mf)+ " "+os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP/",currentExperiment)
						
						#print truncated,len(truncated),currentExperiment,mf.split("/")[-1]
						#print moveit
						gotem.append(currentExperiment+"\t"+mf)
						shutil.copy(os.path.join(root,mf),os.path.join("/home/clarkg/FLOWcyto/UPLOAD_DUMP/",currentExperiment))
					#	os.system(moveit)
						#print currentExperiment,mf,truncated
						#print "\n\n\n"
		except IndexError:
			pass
	gotem=list(set(gotem))
	gotem.sort()
	print "\n".join(gotem)

op=map(lambda l: l.strip(),open("NewMissing.txt",'r').readlines())
#path=re.compile(r"/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES/(IMPC RUNS/){0,1}")
path="/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/"
find_missing(path,op)
