#!/usr/bin/env python

import string, re, sys
import numpy as np
import scipy.stats as ss
import MySQLdb as mdb
from collections import defaultdict
sys.path.append("/home/clarkg/anaconda2/lib/python2.7/site-packages")
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
from Regex import rgx
from cPickle import load, dump
from sklearn import mixture
from StringIO import StringIO
import struct
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw
dbins=dbw()


class FlowUtilities(object):

	def __init__(self):
		self.impcData=[]
		self.localData=[]
		self.count_expect=[]
		self.kde_expect=[]
		self.ordMice=[]
		self.MiceQCPass=[]
		self.PastParameterData=defaultdict(list)
		self.IMData=[]


		####Information related to previous runs and current
		self.ExperimentDirs=defaultdict(list)
		self.ExperimentErrors=defaultdict(list)
		self.ExperimentExcels=defaultdict(dict)

		###Pre-calculated statistical parameters loaded for all accepted experiments
		self.DensityProfile=defaultdict(float)
		self.DensityMax=defaultdict(float)
		self.GMM=defaultdict(float)


	def analyzeParts(self,impcData,localData):
		astat=ss.ks_2samp(impcData,localData)	
		#roundedP='%.3f' % round(astat.pvalue,3)
		return astat.pvalue

	def statDetect(self,count_expect,kde_expect):
		absScore=1
		miter=0
		for z,y in zip(kde_expect,count_expect):
			if y != 0:
				absScore+=(1-z)*float(math.log(y))
		return absScore
	
	def retrieve_mouseData(self,impcQuery):

		cnx,cur=dbins.connect(db_env='DEV',local_db='musmusculims')

		try:
			mouseData="""SELECT %s FROM impc_FlowCytometry""" % (",".join(impcQuery),)
			cur.execute(mouseData)
			ordMice=cur.fetchall()
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
		ordMice=map(lambda k: list(k),ordMice)
		cur.close()
		cnx.close()
		return ordMice

	def get_IMPCData(self,parameters):

		cnx,cur=dbins.connect(db_env='DEV',local_db='musmusculims')


		parameters.sort()
		queryparams=",".join(parameters)
		try:
			mouseData="""SELECT %s FROM impc_FlowCytometry""" % (queryparams,)
			cur.execute(mouseData)
			allData=cur.fetchall()
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
		prmData=zip(*allData)
		for p,d in zip(parameters,prmData):
			self.PastParameterData[p]=d
		cur.close()
		cnx.close()

	def _gmmFinder(self,parameters):
		for param in parameters:
			currentIMPC=np.matrix([[int(i)] for i in self.PastParameterData[param] if str(i) not in ['None','nan']])
			bestAIC=1e+8
			bestBIC=1e+8
			components=0
			_bestmixture=[[],[],[],components,bestAIC,bestBIC]
			allbic=[]
			allaic=[]
			if np.mean(currentIMPC) > 10:
				for comps in range(1,8):
					g=mixture.GMM(n_components=comps)
					fitting=g.fit(currentIMPC)
					currBIC=g.bic(currentIMPC)
					currAIC=g.aic(currentIMPC)
					currweights=list(np.round(g.weights_,3))
					currmeans=list(np.round(g.means_,3))
					currvars=list(np.round(g.covars_,3))
					if currBIC <= _bestmixture[5]:
						_bestmixture=[currweights,currmeans,currvars,comps,currAIC,currBIC]
					allbic.append(currBIC)
					allaic.append(currAIC)
				models=zip(*[_bestmixture[0],_bestmixture[1],_bestmixture[2]])
				sigmodel=[]
				for l in models:
					x,y,z=l
					if x > 0.05:
						sigmodel.append([x,y[0],math.sqrt(z[0])])
				self.GMM[param]=sigmodel
			else:
				self.GMM[param]=[]

			
	def _getDensity(self,parameters):
		for param in parameters:
			currentIMPC=self.PastParameterData[param]
			currentIMPC=filter(lambda a: a not in ["None", None], currentIMPC)
			#setIMPC=list(set(currentIMPC))
			#setIMPC.sort()
			#minCut=setIMPC[2]
			#maxCut=setIMPC[-2]
			#cutsize=int(.05*len(currentIMPC))
			#CutIMPC=[cutsize:(len(currentIMPC)-cutsize)]
			#print param,minCut,maxCut,
			#print np.mean(currentIMPC)
			#CutIMPC=[p for p in currentIMPC if p >= minCut and p <= maxCut]#[cutsize:(len(currentIMPC)-cutsize)]
			maxCut=max(currentIMPC)
			minCut=min(currentIMPC)
			##Have we profiled parameter already?
			densfile=os.path.join("DensityEstimates",param+".pkl")
			densmaxfile=os.path.join("DensityEstimates","mDen_"+param+".pkl")
			if os.path.exists(densfile):
				self.DensityProfile[param]=load(open(densfile,'rb'))
				self.DensityMax[param]=load(open(densmaxfile,'rb'))
			else:		
				density_profile=gaussian_kde(currentIMPC)
				#density_profile=gaussian_kde(CutIMPC)
				dpr=open(densfile,'wb')
				dump(density_profile,dpr)
				dpr.close()
				maxK=max(map(lambda j: density_profile(j)[0], range(int(min(currentIMPC)),int(max(currentIMPC)))))
				kpr=open(densmaxfile,'wb')
				dump(maxK,kpr)
				kpr.close()
				self.DensityProfile[param]=density_profile
				self.DensityMax[param]=maxK	


	def retrieveCode(self,impc_code):

		cnx,cur=dbins.connect(db_env='DEV',local_db='musmusculims')


		if len(impc_code) <=2 :
			return []
		try:
			command="""SELECT %s from impc_FlowCytometry""" % (impc_code)
			cur.execute(command)
			allcode=cur.fetchall()
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
		cur.close()
		cnx.close()
		filtered=[m[0] for m in allcode]
		return filtered
		

	def panelsToimpc(self,filenameA):
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
#		headerfilter=re.compile("[A-z0-9\,\-\+]+[\s]+\|[\s]+Count$")
#		plusminus=re.compile("[+-]")
#		markers=re.compile("CD[0-9]{1,2}|NKT|NK|DN|DP|BCELLS|TCELLS", flags=re.X | re.I)

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


	#def open_xls_as_xlsx(self,run,panel,IMdata,nx):
	def open_xls_as_xlsx(self,run,panel,nx):
		##for whatever reason I cannot access data in the parent class :/
		## for now just doing it this way then
		
		filename="/".join(nx.ExperimentExcels[run][panel])
		print filename,
		print run,
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



		_markers=defaultdict(str)
		if panel == "A":
			tr=open("./log_COLUMNS_PULLED/_PANEL_A_standard.txt",'r').readlines()
		else:
			tr=open("./log_COLUMNS_PULLED/_PANEL_B_standard.txt",'r').readlines()

		for line in tr:
			imA,fullName=line.strip().split("\t")
			if len(fullName):
				_markers[fullName]=imA

									

		### LOG FILES
		writeName=filename.split("/")[-1].strip().rstrip(".xlsx")
		logMarker=open("./log_COLUMNS_PULLED/"+writeName+"_PANEL_"+panel+".txt",'w')
		writemarkers=sorted(_markers.items(), key=operator.itemgetter(1))
		for lk in writemarkers:
			logMarker.write(lk[1]+"\t"+lk[0]+"\n")
		logMarker.close()
		##SELIF GOL

		
		try:
			###IN SOME CASES the "TCELLS" part of the annotion is not present in the excel data sheets
			lnd=_markers["CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-TCELLS|COUNT"]
			_markers.pop("CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-TCELLS|COUNT",None)
			_markers["CLOG-/LIVE/SIZE/FSCSINGLETS/SSCSINGLETS/CD5+,CD161-/CD8TCELLS/CD8+CD44+CD62L-|COUNT"]=lnd
		except KeyError:	pass

		sortmarkers=sorted(_markers.items(), key=operator.itemgetter(1))

		
		#datex=re.compile("[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]")
		splitDate=re.compile("[\-_\s]")
		allDates=map(lambda d: "-".join(re.split("[_\-\s]",d)),rgx.datex.findall(filename))
		
		if not all(x==allDates[0] for x in allDates):
			print "\n\n"
			print "Error with some dates in the file path: %s" % (filename)
			print "The dates in question:"," ".join(allDates)
			print "Please fix this before continuing."
			print "\n\n"
			#pass
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


		list_ids=[rgx.straintag.findall(name) for i,name in enumerate(names) if i in valid_indices]
		
		if any(filter(lambda p: len(p) != 1,list_ids)):
			print "\n\n"
			print "Error with filtering the names in this data set: %s\nPanel: %s\nSample Names: %s" % (filename,panel,names)
			print "\n\n"
			sys.exit()
		else:
			
			actual_ids=map(lambda p: str("_".join([IDdate]+p[0].split("_")[1:3])), list_ids)	

	#	headerfilter=re.compile("[A-z0-9\,\-\+]+[\s]{0,3}\|[\s]{0,3}Count$",flags=re.X | re.I)
	#	percentB=re.compile("CLOG-\/Live[\s]{0,3}\|[\s]{0,3}Freq.[\s]{0,3}of[\s]+Parent",flags=re.X | re.I)
	#	clogcount=re.compile("CLOG-[\s]{0,3}\|[\s]{0,3}Count$",flags= re.X | re.I)	

		col_index=0	
		print len(_columns)
		for column in _columns:
			header=column[0]
			foundbit="".join(header.split()).upper()	
			try:
				_markers[foundbit]
				#if len(_markers[foundbit]) < 2:
					#print "\n\n\n\nJERE OT OS"
					#print "markers_foundbit",_markers[foundbit],foundbit,"\n\n\n\n"
				self.IMData[_markers[foundbit]]=[(column[i],a) for i,a in zip(valid_indices,actual_ids)]
				_foundIMPC.append(_markers[foundbit])
			except KeyError:
				pass
			col_index+=1


		_foundIMPC.sort()

		try:	del self.IMData['']
		except ValueError: pass
	
		#return self.IMData


	def filterLogFile(self,indata):
		previousruns={}
		for k in indata.split("\n"):
			runlog=k.strip().split("\t")	
			filename=runlog[1:]
			jfile="_".join(map(lambda q: "_".join(q.split()),filename))
			previousruns[jfile]=runlog[0]
		return previousruns

	def filterErrorFile(self,indata):
		previousruns={}
		for k in indata.split("\n"):
			runlog=k.strip().split("\t")	
			filename=runlog[2:]
			jfile="_".join(map(lambda q: "_".join(q.split()),filename))
			previousruns[jfile]=runlog[0]
		return previousruns


	def FindNewExperiments(self,path):

		if not len(path):
			path="."
		
		#f=open("./_logFiles_/ParsedFiles.log",'r').read()
		f=open("./_logFiles_/DccParsedFiles.log",'r').read()
	
		###LogData contains all filenames and paths as a dictionary, we check against it while looping
		logdata=self.filterLogFile(f)
		prevrun=[]
		for k in logdata:
			try:
				rundate=k.split("/")[8].strip()
				prevrun.append(rundate)
			except IndexError:
				pass
		prevrun=list(set(prevrun))
		for root, dirs, files in os.walk(path):
			path = root.split('/')
			rawdates=list(set(filter(lambda q: rgx.dateonly.match(q.strip()),path)))
			if len(rawdates) == 0:
				pass
			elif len(rawdates) > 1:
				print "AUDIBLE ERROR"
				print rawdates
				self.ExperimentErrors['DATES']+=rawdates	
			else:
				datedir=rawdates[0].strip()
				if rgx.fcs_path_re.match(root) and datedir not in prevrun:# and rgx.datex.search(datedir) and rgx.datex.search(nesteddata):
					commonpath="/".join(path[:-1])
					#if not self.CommonPath[datedir]:
					#	self.ExperimentDirs[datedir]=commonpath
					self.ExperimentDirs[datedir]=commonpath
		print commonpath


	def findXLfiles(self,path):

		f=open("./_logFiles_/ParsedFiles.log",'r').read()
		elog=open("./_logFiles_/ErrorLog.txt",'w')

		###LogData contains all filenames and paths as a dictionary, we check against it while looping
		logdata=self.filterLogFile(f)

		Excel_runs=defaultdict(list)
		Excel_paths=defaultdict(list)
		for exp,commonpath in self.ExperimentDirs.iteritems():
			for root, dirs, files in os.walk(commonpath):
				path = root.split('/')
				base=path[-1]
				#if len(files):
				#	print root,files,rgx.xl_path_re.match(root)

				if rgx.xl_path_re.match(root):# and rgx.datex.search(datedir) and rgx.datex.search(nesteddata):
					datedir=path[-3]
					self.currentExperiment=datedir
					xls=filter(lambda f: rgx.xlsex.search(f),files)
					if len(xls) > 1:
						self.ExperimentErrors['EXCEL']
						elog.write(time.strftime("%c")+"\tE1\t"+root+"\t"+",".join(xls)+"\n")
						print "\n\n"
						sys.exit()
						
					if re.search("1",base):
						self.ExperimentExcels[datedir].update({"A":[root,xls[0]]})
					else:
						self.ExperimentExcels[datedir].update({"B":[root,xls[0]]})
	
		elog.close()
		#return Excel_runs,Excel_paths



	def findXLfiles_old(self,path):

		f=open("./_logFiles_/ParsedFiles.log",'r').read()
		elog=open("./_logFiles_/ErrorLog.txt",'w')

		###LogData contains all filenames and paths as a dictionary, we check against it while looping
		logdata=self.filterLogFile(f)

		Excel_runs=defaultdict(list)
		Excel_paths=defaultdict(list)
		for exp,commonpath in self.ExperimentDirs.iteritems():
			for root, dirs, files in os.walk(commonpath):
				path = root.split('/')
				base=path[-1]
				#if len(filter(lambda p: re.search(p,"xls"),files)):
				#if len(files) and rgx.xl_path_re.match(root):
				#	print root,files
				try:
					analysisdir=path[-2]
					datedir=path[-3]
					rawdates=rgx.datex.findall(datedir)
					nesteddata=path[-4]
					if rgx.xl_path_re.match(root):# and rgx.datex.search(datedir) and rgx.datex.search(nesteddata):
						self.currentExperiment=datedir
						xls=filter(lambda f: rgx.xlsex.search(f),files)
						try:
							###Has this path and filename already been logged?	
							joint="_".join(root.split())+"_"+"_".join(xls[0].strip().split())
							logdata[joint]
							###If not, a KeyError will occur and we will process it
						except KeyError:
							if len(xls) > 1:
								
								self.ExperimentErrors['EXCEL']
								elog.write(time.strftime("%c")+"\tE1\t"+root+"\t"+",".join(xls)+"\n")
								print "\n\n"
								sys.exit()
							if re.search("1",base):
								self.ExperimentExcels[datedir].update({"A":[root,xls[0]]})
							else:
								self.ExperimentExcels[datedir].update({"B":[root,xls[0]]})
				except IndexError:
					pass
	
		elog.close()
		#return Excel_runs,Excel_paths

	def CompositeMouse(self,aProfile,allProfiles):
		pearsons=[]
		for j in allProfiles:
			pvs=ss.pearsonr(aProfile,j)
			pearsons.append(pvs[0])
		return pearsons

	def FindMouseOutliers(self,fullIMPC,oIM):
		if len(oIM) < 1:
			self.EmailText+="\n\nOur scipt is not finding data for this experiment!.\n\n"
			return
		checkParams=defaultdict(int)
		lclMice=defaultdict(int)
		genMice=defaultdict(int)
		for datapoint in oIM:
			currentIMPC=fullIMPC[datapoint]
			for value,mouse in oIM[datapoint]:
				lclMice[mouse]+=1
				#print mouse,value,datapoint
				currentIMPC=filter(lambda a: a not in ["None", None], currentIMPC)
				#currentIMPC=map(lambda i: int(i), currentIMPC)
				cutsize=int(.25*len(currentIMPC))
				#print cutsize
				CutIMPC=currentIMPC[cutsize:(len(currentIMPC)-cutsize)]
				maxCut=max(CutIMPC)
				minCut=min(CutIMPC)
				if value > maxCut or value < minCut:
					density_profile=gaussian_kde(currentIMPC)
					maxK=max(map(lambda j: density_profile(j)[0], range(int(min(currentIMPC)),int(max(currentIMPC)))))
					Gdens=map(lambda q: density_profile(q)[0]/float(maxK),[value])
					checkParams[datapoint]+=1
					prob=round(Gdens[0]*100,2)
					print mouse,datapoint,"\t",prob,"\t",value,maxCut,minCut
					#lclMice[mouse]+=1
					mouseID="_".join(mouse.split("_")[1:])
					genMice[mouseID]+=1
					#density_profile=gaussian_kde(currentIMPC)
					#maxK=max(map(lambda j: density_profile(j)[0], range(int(min(currentIMPC)),int(max(currentIMPC)))))
					#Gdens=map(lambda q: density_profile(q)[0]/float(maxK),[value])
					##dens is the density profile, Pdens is the same normalized by the maximum density for the profile
					if not self.mouseOutliers:
						mouse_outliers="\n\n"+u'\u26A0'+" All outliers are itemized below\n"
						#mouse_outlier=mouse_outlier.encode('utf-8')
						#self.EmailText+=mouse_outlier
						self.mouseOutliers=True
					#self.EmailText
					mouse_outliers+="\n\n\t Mouse:  %s \t Parameter : %s" % (mouseID,datapoint)
					mouse_outliers+=u'\n\t\t\t\u25B6 We expect value between %s and %s, but have %s' % (maxCut,minCut,value) 
					mouse_outliers+=u'\n\t\t\t\u25B6 Expected probability of a value here is approximately %s' % (prob)
					mouse_outliers+=u'\u0025'

		
		if not self.mouseOutliers:
			outlier_text="\n\n"+u'\u2464'+" All data is within expected range(s).\n\n"
			outlier_text=outlier_text.encode('utf-8')
			self.EmailText+=outlier_text
		else:
			sorted_mice=sorted(genMice.items(), key=operator.itemgetter(1))
			mnit=True
			phen_outliers=""
			sorted_mice.reverse()
			for mo,cnt in sorted_mice:
				#print mo,cnt
				if cnt > 5:
					if mnit==True:
						phen_outliers="\n\n"+u'\u26A0'+" The following mice are outliers often\n"
						mnit=False

					phen_outliers+="\n\t Mouse:  %s has outliers in %s parameters" % (mo,cnt)
				else:
					break	
			
			sorted_Params = sorted(checkParams.items(), key=operator.itemgetter(1))
			totalMice=len(lclMice)


			param_outliers="\n\n"+u'\u26A0'+" The following parameters are suspicious.\n"
			numMice=len(lclMice)
			sorted_Params.reverse()
			for paramID,count in sorted_Params:	
				if count == numMice:
					param_outliers+="\n\t Parameter:  %s is suspect in for ALL %s mice" % (paramID,numMice)
				else:
					param_outliers+="\n\t Parameter:  %s is suspect in %s of %s mice" % (paramID,count,numMice)
			param_outliers+="\n"			
			param_outliers=param_outliers.encode('utf-8')
			mouse_outliers=mouse_outliers.encode('utf-8')
			phen_outliers=phen_outliers.encode('utf-8')
			self.EmailText+=param_outliers
			self.EmailText+=phen_outliers
			self.EmailText+=mouse_outliers
	def FindOutliers(self,oIM):
		##Check the output line by line to see if there are any outlying data	
		self.noOutliers=True
		if len(oIM) < 1:
			self.EmailText+="\n\nOur scipt is not finding data for this experiment!.\n\n"
			return
		firstOutlier=True

		#return ordMice


		for k  in oIM:
			localIM=[f[0] for f in oIM[k]]
			try:
				float(localIM[0])
				currentIMPC=self.retrieveCode(k)
			except (TypeError,IndexError) as e:
				currentIMPC=[]
				pass
			if len(currentIMPC):
				currentIMPC.sort()

				cutsize=int(.08*len(currentIMPC))
				CutIMPC=currentIMPC[cutsize:(len(currentIMPC)-cutsize)]
				maxCut=max(CutIMPC)
				minCut=min(CutIMPC)
				astat=self.analyzeParts(CutIMPC,localIM)	
				if len(set(currentIMPC)) > 5:	
					density_profile=gaussian_kde(currentIMPC)
					maxK=max(map(lambda j: density_profile(j)[0], range(int(min(currentIMPC)),int(max(currentIMPC)))))
					dens=map(lambda q: density_profile(q)[0],localIM)
					Pdens=map(lambda q: density_profile(q)[0]/float(maxK),localIM)
					##dens is the density profile, Pdens is the same normalized by the maximum density for the profile
					undermine=self.statDetect(localIM,Pdens)				
					logScore=math.log(undermine)
					
					outlay=filter(lambda q: q > maxCut or q < minCut, localIM)	

					print localIM,logScore
					if logScore > 3.5 and logScore <= 4.0:
						pass
						#print "\t\t\tColumn Warning*"
						#print np.mean(currentIMPC)-np.std(currentIMPC),"<--->",np.mean(currentIMPC)+np.std(currentIMPC)
						#print np.mean(localIM),"\t",localIM
						#print math.log(undermine),abs(np.mean(localIM)-np.mean(currentIMPC))/float(np.std(currentIMPC))	
						#print "\n\n"
					elif logScore > 4.0 and astat <= 1e-04:
					#	print "\t\t****COLUMN ALERT****" 
					#	print np.mean(currentIMPC)-np.std(currentIMPC),"<--->",np.mean(currentIMPC)+np.std(currentIMPC)
					#	print np.mean(localIM),"\t",localIM
					#	print math.log(undermine),abs(np.mean(localIM)-np.mean(currentIMPC))/float(np.std(currentIMPC))	
						roundedP='%.3g' % astat
						wMdens='%.3g' % math.log(undermine)
						roundedAvg='%.1f' % np.mean(localIM)
						if firstOutlier:
							first_outlier="\n\n"+u'\u2464'+" Our statistics indicate the following parameters are suspect!"
							first_outlier=first_outlier.encode('utf-8')
							self.EmailText+=first_outlier
							firstOutlier=False
						self.noOutliers=False
					#	print "\n\n"
						self.EmailText+="\n\n\t Parameter : %s" % (k,)
						self.EmailText+="\n\t\t\t-> Our weighted stat, wMdens = %s" % (wMdens,) 
						self.EmailText+="\n\t\t\t-> Values for mice : %s" % (", ".join(map(lambda p: str(int(p)),localIM)))
						self.EmailText+="\n\t\t\t-> Values for mice have an average of : %s" % (roundedAvg)
						self.EmailText+="\n\t\t\t-> Range of our database is from %s <--> %s " % (min(CutIMPC),max(CutIMPC))	
						self.EmailText+="\n\t\t\t-> This provides an uncorrected 2 sample Kolmogorov-Smirnov p-value of  %s" % (roundedP)
		if self.noOutliers:
			outlier_text="\n\n"+u'\u2464'+" Our statistics show that all IMPC parameters are within expected ranges.\n\n"
			outlier_text=outlier_text.encode('utf-8')
			self.EmailText+=outlier_text
		#self.emailUsers(self.EmailText)

	def emailUsers(self,textfile):
		from email.mime.text import MIMEText
		# Open a plain text file for reading.  For this example, assume that
		# the text file contains only ASCII characters.
		# Create a text/plain message
		msg = MIMEText(textfile)

		# me == the sender's email address
		# you == the recipient's email address
		msg['Subject'] = """Experiment %s identified on the CMMR shared drive""" % (self.currentExperiment,)
		msg['From'] = 'FLOWQCscript@cmmr'
		#msg['To'] = 'gregw.clark@utoronto.ca'
		#msg['cc'] = 'thisisgreg@hotmail.com'
		# Send the message via our own SMTP server, but don't include the
		# envelope header.
		s = smtplib.SMTP('localhost')
		#s.sendmail('gregw.clark@utoronto.ca', ['elsa.jacob@sickkids.ca','greg.clark@sickkids.ca'], msg.as_string())
		s.sendmail('gregw.clark@utoronto.ca', ['greg.clark@sickkids.ca'], msg.as_string())

	def IndexDir(self,path_dirs):
		#datex=re.compile("[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]")
		for k in range(len(path_dirs)):
			##Descend directory, looking for pattern like "2016-06-23/ANALYSIS"
			##We can search for fcs files within this dir
			if k >= 1 and path_dirs[k].startswith("ANALYSIS") and rgx.datex.match(path_dirs[k-1]):
				return k
		return False	




	def FindFMOfiles(self):
		dDate=time.strptime(self.currentExperiment,"%Y-%m-%d")
		#dDate is the experimental Date in datetime format
		##Control for CD62L started use August 2016 2016-08-01
		
		cd62lcut=dDate < self.CD62Ldate
		## We can take the full path here
		files=list(set(self.FMOControlFiles.values()[0]))
		for filename in files:
			f=filename.split("/")[-1]
			if rgx.cd5_A.match(f):
				self.FileMatchA['CD5']=True		
			elif rgx.mhc.match(f):
				self.FileMatchB['MHCII']=True
			elif rgx.cd161_A.match(f):
				self.FileMatchA['CD161']=True		
			elif rgx.cd44.match(f):
				self.FileMatchA['CD44']=True
			elif rgx.cd8a.match(f):
				self.FileMatchA['CD8A']=True
			elif rgx.cd62l.match(f):
				self.FileMatchA['CD62L']=True
			elif rgx.cd25.match(f):
				self.FileMatchA['CD25']=True
			elif rgx.cd5_B.match(f):
				self.FileMatchB['CD5']=True
				self.FileMatchB['CD5_LY6G']=True
			elif rgx.cd161_B.match(f):
				self.FileMatchB['CD161']=True
			elif rgx.cd11B.match(f):
				self.FileMatchB['CD11B']=True
			elif rgx.cd11C.match(f):
				self.FileMatchB['CD11C']=True
			elif rgx.cd23.match(f):
				self.FileMatchB['CD23']=True
			elif rgx.ly6c.match(f):
				self.FileMatchB['LY6C']=True
			elif rgx.cd21_35.match(f):
				self.FileMatchB['CD21_35']=True
		
		FailedA={k: v for k, v in self.FileMatchA.iteritems() if v == False}
		if cd62lcut:
			del FailedA['CD62L']

		FailedB={k: v for k, v in self.FileMatchB.iteritems() if v == False}
		
		return FailedA,FailedB	


	def fcsextract(self,filename):
	    fcs_file_name = filename

	    fcs = open(os.path.join(self.FCSPath,fcs_file_name),'rb')
	    header = fcs.read(58)
	    version = header[0:6].strip()
	    text_start = int(header[10:18].strip())
	    text_end = int(header[18:26].strip())
	    data_start = int(header[26:34].strip())
	    data_end = int(header[34:42].strip())
	    analysis_start = int(header[42:50].strip())
	    analysis_end = int(header[50:58].strip())

	    fcs.seek(text_start)
	    delimeter = fcs.read(1)
	    text = fcs.read(text_end-text_start+1)
	    #Variables in TEXT poriton are stored "key/value/key/value/key/value"
	    keyvalarray = text.split(delimeter)
	    fcs_vars = {}
	    fcs_var_list = []
	    # Iterate over every 2 consecutive elements of the array
	    for k,v in zip(keyvalarray[::2],keyvalarray[1::2]):
		fcs_vars[k] = v
		fcs_var_list.append((k,v)) # Keep a list around so we can print them in order
	    tube=re.compile("^\$P[0-9]{1,3}S")
	    lclMarks=[]
	    lclPanelA=self.FileMatchA
	    lclPanelB=self.FileMatchB
            if 'CD5' in lclPanelB:	del lclPanelB['CD5']###CD5 is used as CD5_LY6G for Panel B
	    for k,l in fcs_vars.iteritems():
		if tube.match(k):
			l = re.sub(r"/", "_", l).upper()
			lclMarks.append(l)
		elif k =="$SRC":
			if rgx.impcA.match(l) or rgx.panelA.search(l):
				controls=lclPanelA
				panel="A"
			elif rgx.impcB.match(l) or rgx.panelB.search(l):
				controls=lclPanelB
				panel="B"
			else:
				self.ErrorEmailText+='\t\tSource File %s has an unidentified panel \"%s\".' %s (filename,l)
				self.FatalError=True
	    
	    if panel == "B":
		_M_B=list(set(lclMarks).difference(set(self.FMOpanelB)))
		_M_A=[]
	    elif panel == "A":
		_M_A=list(set(lclMarks).difference(set(self.FMOpanelA)))
		_M_B=[]
	    UsedControls=[f for f,l in controls.iteritems() if l == True]
            MissingL=list(set(UsedControls).difference(set(lclMarks)))
	    MissingP=list(set(lclMarks).difference(set(UsedControls)))
	    if _M_B:
		self.ControlAdded[filename]+=_M_B
            if _M_A:
		self.ControlAdded[filename]+=_M_A
	    if len(MissingL):
		self.ControlMissing[filename]+=MissingL
		self.FatalError=True

	def FindFCSFiles(self,commonpath):
		if commonpath == "":
			print "Must provide a path"
			sys.exit()
		filematch=re.compile("PANEL[\s_][AB][\s_][A][A-Z][A-Z][A-Z][\s_][0-9]{1,12}",flags=re.X | re.I)
		FMOfiles=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}(A|B)""",flags=re.X|re.I)
		MatrixF=re.compile("""[A-z0-9\s_\-,]+MATRIX[A-z0-9\s_\-,]+[\.]mtx""",flags=re.X|re.I)

		fullError=re.compile("PANEL[\s][AB][A][A-Z][A-Z][A-Z]_[0-9]{1,12}")
		fullIMPC=re.compile("IMPC[12][\s_-]")
				
		ErrorProne=defaultdict(list)
		for root, dirs, files in os.walk(commonpath):
		    path = root.split('/')
		    for file in files:
			
			if rgx.fcs_path_re.match(root) and file.endswith("fcs") and not (rgx.compFiles.search(file) or rgx.omitcontrol.search(file)):
				filecode=rgx.ProperCode.findall(file)#+rgx.controlonly.findall(file)
				self.FCSPath=root
				if len(filecode) > 1:
					filecode
					print file
					print filecode
					print "THERE IS SOMETHING WRONG HERE"
					self.FatalError=True
				elif len(filecode) == 1:
					filecode=filecode[0]
					self.MouseIDS[self.currentExperiment].append(filecode)
					self.ExperimentFiles[self.currentExperiment].append(file)
				else:
					filecode=file

				datafile=os.path.join("/".join(path),file)
				sample=FCMeasurement(ID="Tops",datafile=datafile)
				mdata=sample.meta.keys()
				sampleID=sample.meta["TUBE NAME"]
				FullName=sample.meta["$FIL"]
				panel=sample.meta["$SRC"]
				if not panel.endswith("_"):
					panel="_".join(panel.split())+"_"
				else:
					panel="_".join(panel.split())

				composite=panel+sampleID

				if fullError.match(FullName):
					tempStart,tempEnd=FullName.split()
					tempStart=tempStart+"_"+tempEnd[0]
					tempEnd=tempEnd[1:]
					FullName=tempStart+"_"+tempEnd
				memaw=[re.search(filecode,FullName),re.search(filecode,composite)]
				if not all(memaw) and filematch.match(file):
					self.ErrorProne[path[6]].append([file,composite,FullName])
			elif rgx.fcs_path_re.match(root) and file.endswith("fcs") and re.match("Specimen",file):
				pass
			elif rgx.fcs_path_re.match(root) and file.endswith("fcs") and rgx.FluoroMatch.match(file):
				#print "Comp Control",file
				self.CompensationFiles[self.currentExperiment].append(file)
			elif rgx.fcs_path_re.match(root) and file.endswith("fcs") and rgx.FMOfiles.match(file):
				#print "Comp Control",file
				self.FMOControlFiles[self.currentExperiment].append(file)
			elif file.endswith("mtx") and rgx.MatrixF.match(file):
				self.MatrixFiles[self.currentExperiment].append(file)

class FlowData(FlowUtilities):
	##This will help keep the data separate from the functions.
	##Every experiment will have a newly initialized 
	##subclass (inherited from FlowUtilities)
	#def __init__(self,FlowUtilities):
	def __init__(self,FlowUtilities):
		self.currentExperiment=""
		self.IMData=defaultdict(list)
		self.EmailText=""
		self.ErrorEmailText=""
		self.noOutliers=False
		self.mouseOutliers=False
		self.FCSPath=""
		self.ExcelPath=""
		self.CommonPath=defaultdict(str)
		self.ExcelMice=defaultdict(list)
		self.MouseIDS=defaultdict(list)	
		self.CompensationFiles=defaultdict(list)
		self.ExperimentFiles=defaultdict(list)
		self.MatrixFiles=defaultdict(list)
		self.FMOControlFiles=defaultdict(list)
		self.ErrorProne=defaultdict(list)
		self.CD62Ldate = time.strptime("2016-08-01", "%Y-%m-%d")
		self.ControlErrors=defaultdict(list)
		self.ControlMissing=defaultdict(list)
		self.ControlAdded=defaultdict(list)
		self.FatalError=False
		self.FMOpanelB=['CD5_LY6G', 'CD19', 'CD161', 'LY6C', 'CD11C', 'MHCII', 'CD11B', 'CD23', 'CD21_35']
		self.FMOpanelA=['CD5', 'CD161', 'CD4', 'CD25', 'CD62L', 'CD8A', 'CD44']
		self.FileMatchA={'CD5':False,
			 'CD161':False,
			 'CD44':False,
			 'CD8A':False,
			 'CD62L':False,
			 'CD25':False}
		self.FileMatchB={'CD5':False,
			 'CD161':False,
			 'CD11B':False,
			 'CD11C':False,
			 'MHCII':False,
			 'CD23':False,
			 'LY6C':False,
			 'CD21_35':False}

class MouseData(FlowUtilities):
	##This will help keep the data separate from the functions.
	#def __init__(self,FlowUtilities):
	def __init__(self):
		self.data=defaultdict(list)
		self.paramOrder=[]
		self.ExperimentDate=defaultdict(str)
		self.FCSfiles=defaultdict(list)	
		self.Excelfiles=defaultdict(list)
	def qDataBase(self,cur,StrainTag):
		return
		if not cur:
			print "No database connection"
			sys.exit()
		date,straincode,eartag=map(lambda p: p.strip(),StrainTag.split("_"))
		query=",".join(self.paramOrder)
		theQ=""""SELECT %s from impc_FlowCytometry where strainCode = %s and earTag = %s"""% (query,straincode,eartag)
		#print theQ
		cur.execute("""SELECT %s from impc_FlowCytometry where strainCode = %s and earTag = %s""" % (query,"\""+straincode+"\"","\""+eartag+"\""))
		data=cur.fetchall()
		#if not data:
		#	print "NO DATA FOR MOUSE",straincode,eartag
		#else:
		#	print straincode,eartag,data[0][:5]#,self.data[StrainTag][:5]
			
