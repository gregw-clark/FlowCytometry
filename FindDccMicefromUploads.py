#!/usr/bin/env python

import string, re, sys
import glob
import os
import MySQLdb as mdb
import datetime
rightnow=datetime.datetime.now()
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw


con,cur=dbins.connect(db_env='PROD')
## Just a general connection to the database server - must specify scehma


#filematch=re.compile(PANEL_A_ACJL_221_005.fcs   PANEL_A_ACWS_60_009.fcs   PANEL_B_ACVU_95_020.fcs
filematch=re.compile("^PANEL_[AB]_[AB][6A-Z][A-Z][A-Z]_[0-9]{2,4}_[A-Z0-9_]+.fcs$")

dirs=glob.glob("./UPLOAD_DUMP/*")
dirs.sort()

colfiles=[]
cd={}
expDates={}
for dir in dirs:
	allfiles=glob.glob(os.path.join(dir,"PANEL*.fcs"))
	samples=filter(lambda l: filematch.match(l.split("/")[-1]),allfiles)
	if len(allfiles) != len(samples):
		
		break
	colfiles+=map(lambda k: k.split("/")[-1],allfiles)
	for f,d in zip(samples,map(lambda k: k.split("/")[-1],allfiles)):
		expDates[d]=f.split("/")[2]
colfiles.sort()
bead1='60125'
bead2='62927'
QCfile="QC_FlowCyto_2017_03_21.py"
for f in colfiles:
	a,panel,wStrain,wTag,c=f.split("_")
	expDate=expDates[f]	
	try:
		cur.execute("""Select i.MouseBCode,i.DOD from musmusculims.Mice2 m join impc.impc_Mice i 
				on m.zmUID = i.zmUID 
				where m.mStrainCode = %s and m.mEarTag=%s""", (wStrain,wTag))
		retmus=cur.fetchall()[0]
	except (mdb.Error,IndexError),e:
		retmus=False
	if retmus:
		if expDate >= "2017-02-02":
			beadlot=bead2
		else:
			beadlot=bead1
		barcode,dod=retmus
		##SELECT * FROM musmusculims.impc_flowCytometry_fcs_files
		try:
			cur.execute("""INSERT INTO musmusculims.impc_FlowCytometry
				(expDate,metadata_id,MouseBCode,strainCode,earTag,DOD,CST_Beadlot,QC_By,QC_Date) 
				VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (expDate,1,barcode,wStrain,wTag,dod,beadlot,QCfile,rightnow))
			con.commit()
		except mdb.Error,e:
			print e.args[0],e.args[1]
			sys.exit()
