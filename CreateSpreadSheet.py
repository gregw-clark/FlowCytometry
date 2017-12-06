#!/usr/bin/env python

import string, re, sys
import xlrd
import collections
from collections import defaultdict
import os
import datetime
from pandas import DataFrame
import numpy as np
import operator
import fnmatch
import csv
import MySQLdb as mdb
from scipy.stats.kde import gaussian_kde
import scipy.stats as ss
import math
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw
from FlowClass.Regex import rgx
from FlowClass.FlowUtils import FlowUtilities,FlowData
import glob
dbins=dbw()

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
#	python CreateSpreadSheets.py 2014.csv        #
######################################################


def cleanRead(datavalue):
	d=str(str(datavalue).split(":")[1]).lstrip("u\'").rstrip("\'")
	return d


def changePanel(pfilename):
	#correctPanel=re.compile("PANEL_[AB]_[AB][A-Z6][A-Z][A-Z]_[0-9]{1,4}_[A-z_0-9]+.fcs",flags=re.X)
	if not rgx.correctPanel.match(pfilename):
		pfilename="_".join(filter(lambda a: len(a),pfilename.split("_")))
		if rgx.correctPanel.match(pfilename):
			return pfilename
		if re.match("PANELA",pfilename):
			newname=pfilename.split("PANELA")[0]
			pfilename="PANEL_A"+newname
		elif len(pfilename.split("_")) < 5:
			print "FIX Filename: missing \"_\"",pfilename
			sys,exit()
		else:
			print "FIX Filename: no class",pfilename
			sys.exit()
	return pfilename



def FMdata(FMspread):
	#FilenameSHould be MatchingColumns.xls
	Icode={}
	wb=xlrd.open_workbook(FMspread)
	sheetA = wb.sheet_by_index(0)
	r=sheetA.row(0)
	c=sheetA.col_values(0)
	data=[]
	for i in xrange(sheetA.nrows):
		row=sheetA.row_values(i)
		rowtypes=sheetA.row(i)
		data.append(rowtypes)
	header=map(lambda q: cleanRead(str(q)),data[0])
	headerV={}
	for k in range(len(header)):
		#print header[k],k
		headerV[header[k].strip()]=k
	data.pop(0)
	cleandata={}
	dfdata=[]
	for row in data:
		keeper=True
		position=0
		cleanrow=[]
		for k in row:
			if position in [2,4]:
				dipset=cleanRead(str(k))
				if not dipset:
					keeper=False
				lclVal=""
			if str(k).split(":")[0] =="xldate" and position >= 6:
				try:
					floatdate=float(str(k).split(":")[1])
					tupdate=list(xlrd.xldate_as_tuple(floatdate,wb.datemode))
					year=tupdate[0]
					month=tupdate[1]
					day=tupdate[2]
					stringdate=str(year)+"-"+str(month).zfill(2)+"-"+str(day).zfill(2)
					lclVal=stringdate
				except TypeError:
					print "MISSING SOMETHING"
					pass
			else:
				lclVal=cleanRead(str(k))
			cleanrow.append(lclVal)
			position+=1
		if keeper:
			identifier="_".join([cleanrow[6],cleanrow[2],cleanrow[4]])
			cleandata[identifier]=cleanrow
			dfdata.append(cleanrow)
	lcf=DataFrame(dfdata,columns=header)
	return headerV,cleandata,lcf
	
def panelsToimpc(filenameA):
	#FilenameSHould be MatchingColumns.xls
	Icode={}
	wb=xlrd.open_workbook(filenameA)
	sheetA = wb.sheet_by_name("PanelA")
	r=sheetA.row(0)
	c=sheetA.col_values(0)
	dataA=[]
	for i in xrange(sheetA.nrows):
		dataA.append(sheetA.row_values(i))
	sheetB = wb.sheet_by_name("PanelB")
	r=sheetB.row(0)
	c=sheetB.col_values(0)
	dataB=[]
	for i in xrange(sheetB.nrows):
		dataB.append(sheetB.row_values(i))
	##regex compiled
	headerfilter=re.compile("[A-z0-9\,\-\+]+[\s]+\|[\s]+Count$")
	plusminus=re.compile("[+-]")
	markers=re.compile("CD[0-9]{1,2}|NKT|NK|DN|DP|BCELLS|TCELLS", flags=re.X | re.I)
	##delipmoc xeger

	headerA=dataA[0]
	dataA.pop(0)
	for line in dataA:
		if line[4]:
			ic="IMPC_IMM_"+str(int(line[4])).zfill(3)+"_001"
			Icode[ic]=["A",line[1],line[2],line[4],line[0],line[5]]
	headerB=dataB[0]
	dataB.pop(0)
	for line in dataB:
		if line[4]:
			ic="IMPC_IMM_"+str(int(line[4])).zfill(3)+"_001"
			Icode[ic]=["B",line[1],line[2],line[4],line[0],line[5]]
	return Icode	




global col_matchA,col_matchB
col_matchA,col_matchB={},{}

def open_xls_as_xlsx(filename,panel,impc_order,IMdata):
    # first open using xlrd
	wb=xlrd.open_workbook(filename)
	sheet = wb.sheet_by_index(0)
	r=sheet.row(0)
	c=sheet.col_values(0)
	data=[]
#	validname=re.compile("Panel[_\s][AB]_[A-Z][A-Z6][A-Z][A-Z]_[0-9]{1,4}_",flags=re.X | re.I)
#	straintag=re.compile("_[A-Z][A-Z6][A-Z][A-Z]_[0-9]{1,4}_",flags=re.X|re.I)
	for i in xrange(sheet.nrows):
		data.append(sheet.row_values(i))
	_columns=zip(*data)
	_impc = dict((k,v) for k,v in impc_order.items() if v[0] == panel)
	_markers = dict((str(v[5]),k) for k,v in _impc.items())
	try:
		###IN SOME CASES the "TCELLS" part of the annotion is not present in the excel data sheets
		lnd=_markers["CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-TCELLS|COUNT"]
		_markers.pop("CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-TCELLS|COUNT",None)
		_markers["CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-|COUNT"]=lnd
		
	except KeyError:	pass

	sortmarkers=sorted(_markers.items(), key=operator.itemgetter(1))
	
#	datex=re.compile("[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]")

	#splitDate=re.compile("[\-_\s]")
	allDates=map(lambda d: "-".join(re.split("[_\-\s]",d)),rgx.datex.findall(filename))
	
	if not all(x==allDates[0] for x in allDates):
		print "\n\n"
		print "Error with some dates in the file path: %s" % (filename)
		print "The dates in question:"," ".join(allDates)
		print "Please fix this before continuing."
		print "\n\n"
		sys.exit()

	lclDate=rgx.datex.findall(filename.split("/")[-1])
	if len(lclDate) != 1:
		print "Error with the filename for: %s\nWe expect there to be 1 date, we find %s!" % (filename,len(lclDAte))
		sys.exit()
	else:
		IDdate="-".join(re.split("[-_\s]",lclDate[0]))
	names=_columns[0]
	_columns.pop(0)
	_foundIMPC=[]
	valid_indices=[i for i,name in enumerate(names) if rgx.validname.search(name)]

	#print valid_indices

	list_ids=[rgx.straintag.findall(name) for i,name in enumerate(names) if i in valid_indices]
	if any(filter(lambda p: len(p) != 1,list_ids)):
		print "\n\n"
		print "Error with filtering the names in this data set: %s\nPanel: %s\nSample Names: %s" % (filename,panel,names)
		print "\n\n"
		sys.exit()
	else:
		
		actual_ids=map(lambda p: str("_".join([IDdate]+p[0].split("_")[1:3])), list_ids)	
	FULLN=[]
	for k in range(len(names)):
		if k in valid_indices:	
		#	print k,names[k]
			FULLN.append(names[k])
	lcl=dict(zip(actual_ids,FULLN))
	if panel=="A":
		col_matchA.update(lcl)	
	elif panel=="B":
		col_matchB.update(lcl)	
	#print actual_ids
#	headerfilter=re.compile("[A-z0-9\,\-\+]+[\s]{0,3}\|[\s]{0,3}Count$",flags=re.X | re.I)
#	percentB=re.compile("CLOG-\/Live[\s]{0,3}\|[\s]{0,3}Freq.[\s]{0,3}of[\s]+Parent",flags=re.X | re.I)
#	clogcount=re.compile("CLOG-[\s]{0,3}\|[\s]{0,3}Count$",flags= re.X | re.I)	

	col_index=0	
	for column in _columns:
		header=column[0]
		if rgx.headerfilter.search(header) or rgx.clogcount.match(header) or rgx.percentB.match(header):
			foundbit="".join(header.split()).upper()	
			if foundbit == "CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-TCELLS|COUNT":
				foundbit="CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-|COUNT"
			try:
				_markers[foundbit]
				IMdata[_markers[foundbit]]=[(column[i],a) for i,a in zip(valid_indices,actual_ids)]
				_foundIMPC.append(_markers[foundbit])
			except KeyError:
				pass
		col_index+=1
	_foundIMPC.sort()
	
	return IMdata



def findXLfiles(path):
	if not len(path):
		path="."
	Excel_runs=defaultdict(list)
	Excel_paths=defaultdict(list)

	for root, dirs, files in os.walk(path):
		path = root.split('/')
		base=path[-1]
		try:
			analysisdir=path[-2]
			datedir=path[-3]
			rawdates=rgx.datex.findall(datedir)
			nesteddata=path[-4]
			if rgx.xl_path_re.match(root) and rgx.datex.search(datedir) and rgx.datex.search(nesteddata):
				xls=filter(lambda f: rgx.xlsex.search(f),files)
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
			elif re.match("IMPC",base) and re.search("ANALYSIS",analysisdir) and rgx.datex.search(datedir):
				print "SKIPPING", datedir,"\t",root
		except IndexError:
			pass
	return Excel_runs,Excel_paths


def MatchFCS(mouse):
	base="/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/"
	#IMPC_96 Well - U bottom
	expDate=mouse.split("_")[0]
	yearDate=expDate.split("-")[0]
	wDate,wStrain,wTag=mouse.strip().split("_")
	#print mouse,yearDate
	if yearDate == "2015":
		searchPath=os.path.join(base,"2015 IMPC  FCS FILES",expDate,expDate)
	elif yearDate == "2014":
		searchPath=os.path.join(base,"2014 IMPC  FCS FILES","IMPC RUNS",expDate,expDate)
	elif yearDate == "2016":
		searchPath=os.path.join(base,"2016 IMPC FCS FILES",expDate,expDate)
	elif yearDate == "2017":
		searchPath=os.path.join(base,"2017 IMPC FCS FILES",expDate,expDate)
	else:
		return []
	matches=[]
	for root, dirnames, filenames in os.walk(searchPath):
		bdir=root.split("/")[-1]
		for filename in fnmatch.filter(filenames, "*"+wStrain+"*_"+wTag+"*.fcs"):
			if re.search("IMPC",bdir):
				print expDate,filename,wStrain,wTag,bdir
				matches.append(os.path.join(root, filename))
	matches=map(lambda p: p.split("/")[-1],matches)
	correct=map(lambda f: changePanel(f),matches) 

	if len(correct) != 2:
		print "\t NO MATCHES:",expDate,"\t",mouse,"\t",matches
		sys.exit()
	return correct

def collectData(nx):


	impc_order=panelsToimpc("/home/clarkg/FLOWcyto/FlowClass/MatchingColumns.xls")
	#print self.Experiment
	Excel_runs,Excel_paths=findXLfiles("/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/")
	#Excel_runs,Excel_paths=findXLfiles("/home/clarkg/FLOWcyto/UPLOAD_DUMP/")
	ordered=collections.OrderedDict(sorted(Excel_runs.items()))
	allparams=impc_order.keys()
	allparams.sort()

	nx.get_IMPCData(allparams)
	##nx.PastParameterData['IMPC_IMM_043_001']	
	nx._getDensity(allparams)
	##_getDensity brings us 2 parameters
		##Accessed as	
		##nx.DensityProfile['IMPC_IMM_043_001']		
		##nx.DensityMax['IMPC_IMM_043_001']		

	
	nx._gmmFinder(allparams)
	##nx.GMM['IMPC_IMM_076_001'] gives gaussian models for parameter [weight,mean,std_dev]	
	
	
	IMData=defaultdict(list)	
	allruns=defaultdict(list)
	
	for run in ordered:
		if len(Excel_runs[run]) != 2:
			print "\n\n"
			print "\t\tERROR parsing run: %s\nHere are the files: %s\nHere is the path: %s" % (run,Excel_runs[run],Excel_paths[run])
			print "\n\n"
			sys.exit()
		else:
			panelA=os.path.join(os.getcwd(),Excel_paths[run][0],Excel_runs[run][0])
			panelB=os.path.join(os.getcwd(),Excel_paths[run][1],Excel_runs[run][1])
			#print IMData	
			IMData=open_xls_as_xlsx(panelA,"A",impc_order,IMData)
			IMData=open_xls_as_xlsx(panelB,"B",impc_order,IMData)
			oIM=collections.OrderedDict(sorted(IMData.items()))
			print "Parsing folder...",run
			for k  in oIM:
				ldat=zip(*oIM[k])
				try:
					ldat[0],ldat[1]
					for c,v in zip(ldat[0],ldat[1]):
						allruns[k].append([v,c])
				except IndexError:
					print 5*"\n"
					print "Missing Data",k,"\t",ldat,"\t\t",Excel_paths[run],Excel_runs[run]
					sys.exit()
	allOrdered=collections.OrderedDict(sorted(allruns.items()))
	return allOrdered


def QCmouse(mouse,theIMPC,kde=False):
	mousescore=0
	outliers={}
	#total=0
	def z_score(val,med,std):
		return abs(val-med)/float(std)
	if not kde:
		mouseZ=[]
		for mdata,param in zip(mouse,theIMPC):
			#normalized=map(lambda q: nx.DensityProfile[param](q)[0]/float(nx.DensityMax[param]),[mdata])
			if not len(nx.GMM[param]):
				noZero=[l for l in nx.PastParameterData[param] if l > 1]
				if mdata > 2*max(nx.PastParameterData[param]):
					outliers[param]=[mdata,max(nx.PastParameterData[param])]
				mouseZ.append(.1)
			else:
				distr=nx.GMM[param]
				#best bNsc
				bNsc=1e10
				for w,u,s in distr:
					Nsc=z_score(mdata,u,s)	
					if Nsc < bNsc:
						bNsc=Nsc
				if bNsc > 5:
					#print param,bNsc
					outliers[param]=[mdata,bNsc]
				mousescore+=bNsc
				mouseZ.append(bNsc)
	else:
		for mdata,param in zip(mouse,theIMPC):
			normalized=map(lambda q: nx.DensityProfile[param](q)[0]/float(nx.DensityMax[param]),[mdata])
			kde_est=normalized[0]
			if kde_est*100 < .5:
				outliers[param]=[mdata,kde_est]
			mousescore+=abs(math.log(max(0.0003,kde_est)))
	return mousescore,outliers

if __name__ == "__main__":



	connA,impcdb=dbins.connect(db_env='PROD',local_db='impc')
	connB,musculusdb=dbins.connect(db_env='PROD',local_db='musmusculims')


	nx=FlowUtilities()
	allOrdered=collectData(nx)


#	sys.exit()


	f=open(curDate+"_"+"Flow_data.csv",'w')	
	cnt=0
	orderedMice=defaultdict(list)
	theIMPC=[]
	for k in allOrdered:
		for x in range(len(allOrdered[k])):
			orderedMice[allOrdered[k][x][0]].append(allOrdered[k][x][1])
		theIMPC.append(k)
	doOrder=collections.OrderedDict(sorted(orderedMice.items()))


	f.write("Experiment_Date,Strain_Code,Colony_ID,Ear_Tag,Genotype,Sex,Mouse_Number,FCS_Files_A,FCS_Files_B"+","+",".join(theIMPC)+"\n")
	sizesM={}
	
	for mouse in doOrder:
		sizesM[mouse]=len(doOrder[mouse])		
		#print mouse
		score,outs=QCmouse(doOrder[mouse],theIMPC)
	
		if len(outs):
			expD=mouse.split("_")[0]
			mouseID="_".join(mouse.split("_")[1:])
			for k,l in outs.iteritems():
				val,kde=l
				#dsize=len(set(nx.PastParameterData[k]))
				#if dsize > 0:
				print expD,mouseID,k,val#,np.median(nx.PastParameterData[k])#,kde
#			#print "\n"


		FCSfiles=MatchFCS(mouse)
		#2015-02-26_B6NC_479
		PfileA=filter(lambda p: re.match("PANEL[\W_]A",p,flags=re.X|re.I),FCSfiles)
		PfileB=filter(lambda p: re.match("PANEL[\W_]B",p,flags=re.X|re.I),FCSfiles)
#		print PfileA,PfileB
		if len(PfileA) != 1:
			print "NOOONE A"
		if len(PfileB) != 1:
			print "NOOONE B"
		PfileA=PfileA[0]
		PfileB=PfileB[0]

		wDate,wStrain,wTag=mouse.strip().split("_")
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

		geneSymbol,zygosity,gender,dcc_id=retimpc
		if geneSymbol is None:
			genotype='WT'
		else:
			genotype=geneSymbol+zygosity
		writeLine=""#map(lambda s: str(s),doOrder[mouse])
		#f.write("Experiment_Date,Strain_Code,Colony_ID,Ear_Tag,Genotype,Sex,Mouse_Number,FCS_Files_A,FCS_Files_B"+","+",".join(theIMPC)+"\n")
		if dcc_id is None:
			dcc_id=""
		if colony[0] is None:
			colony=[""]	
		try:
			stringdata=",".join([wDate,wStrain,colony[0],wTag,genotype,gender,dcc_id,PfileA,PfileB])
		except:
			print wDate,wStrain,colony[0],wTag,genotype,gender,dcc_id,PfileA,PfileB

		f.write(stringdata+","+",".join(writeLine)+"\n")

	
	f.close()
	
