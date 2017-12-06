#!/usr/bin/env python

import string,re, sys
import MySQLdb as mdb
sys.path.append("/home/clarkg/anaconda2/lib/python2.7/site-packages/")
import datetime
sys.path.append("/home/clarkg/PythonSite/")
from DBwrap import MDB as dbw
dbins=dbw()


#lp=open("FlowData_1479860384.csv",'r').readlines()
lp=open("FlowData_1479915470.csv",'r').readlines()
header=lp[0].split(",")
lp.pop(0)

IMPC60="IMPC_IMM_060_001"
IMPC56="IMPC_IMM_056_001"
IMPC57="IMPC_IMM_057_001"
I60=header.index(IMPC60)
I56=header.index(IMPC56)
I57=header.index(IMPC57)


cnx,cur=dbins.connect(db_env='PROD',local_db='musmusculims')


print lp
print I60,I57,I56
#sys.exit()


scriptName="QC_FlowCyto_2017-03-21.py"
current=str(datetime.datetime.now())
print len(lp)
for l in range(len(lp)):
	rowdata=lp[l].split(",")
	expDate,strainCode,earTag=rowdata[:3]
	I60data=rowdata[I60]
	I56data=rowdata[I56]
	I57data=rowdata[I57]

	print expDate,strainCode,earTag,"\t",I56data,I57data,I60data
	try:
		comm="""UPDATE impc_FlowCytometry set IMPC_IMM_060_001 = %s,QC_Date =%s, QC_By =%s  where expDate = %s and strainCode = %s and earTag = %s""" % (I60data,"\""+current+"\"","\""+scriptName+"\"","\""+expDate+"\"","\""+strainCode+"\"",earTag)
		cur.execute(comm)
		#impc60=cur.fetchall()[0][0]
	except mdb.Error,e:
		print e.args[0],e.args[1]
#		sys.exit()

sys.exit()

try:
	comm="""SELECT expDate,strainCode,earTag,IMPC_IMM_056_001 from impc_FlowCytometry"""
	cur.execute(comm)
	impc56=cur.fetchall()
except mdb.Error,e:
	print e.args[0],e.args[1]
	sys.exit()



try:
	comm="""SELECT expDate,strainCode,earTag,IMPC_IMM_057_001 from impc_FlowCytometry"""
	cur.execute(comm)
	impc57=cur.fetchall()
except mdb.Error,e:
	print e.args[0],e.args[1]
	sys.exit()

for d in impc56:
	date=str(d[0])
#	print date,d[1],d[2],d[3],
	swtch="""UPDATE impc_FlowCytometry set IMPC_IMM_057_001 = %s where expDate = %s and strainCode = %s and earTag = %s""" % (d[3],"\""+date+"\"","\""+d[1]+"\"","\""+d[2]+"\"")
	cur.execute(swtch)
for g in impc57:
	date=str(g[0])
	swatch="""UPDATE impc_FlowCytometry set IMPC_IMM_056_001 = %s where expDate = %s and strainCode = %s and earTag = %s""" % (g[3],"\""+date+"\"","\""+g[1]+"\"","\""+g[2]+"\"")
	cur.execute(swatch)

cur.close()
cnx.close()
#con
