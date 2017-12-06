#!/usr/bin/env python

import string, re, sys
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import scipy.stats as ss
import re
import MySQLdb as mdb
from scipy.stats import gaussian_kde
import math
#import seaborn as sns

impx=re.compile("IMPC_IMM_[0-9][0-9][0-9]_[0][0][012]",flags=re.X|re.I)


def dist(x1,y1, x2,y2, x3,y3): # x3,y3 is the point
    px = x2-x1
    py = y2-y1

    something = px*px + py*py

    try:
       u =  ((x3 - x1) * px + (y3 - y1) * py) / float(something)
    except:
       u=0
    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    dist = math.sqrt(dx*dx + dy*dy)

    return dist


cnx=mdb.connect('cmmrdbdev.research.sickkids.ca','greg','t43tt43t','musmusculims')
cur=cnx.cursor()

annot=open("IMPC_parameters.csv",'r').readlines()
ticks={}
for l in range(len(annot)):
	data=annot[l].split(",")
	code=impx.findall(data[0])
	impccode=code[0]
	if re.search(data[5],"Tick"):
		ticks[impccode]=True
	else:
		ticks[impccode]=False

pl=open("results.txt",'r').readlines()
impc_manual=defaultdict(list)
impc_automated=defaultdict(list)
dataorder=defaultdict(list)
geneorder=defaultdict(list)


for k in range(len(pl)):
	data=pl[k].strip().split()
	impc_manual[data[4]].append(float(data[5]))
	impc_automated[data[4]].append(float(data[3]))
	dataorder[data[4]].append(data[1]+"_"+data[2])
#	geneorder[data[4]].append(data[0].split("_")[0].split("1-1-1-")[1])
#	localcode="\""+data[1].strip().upper()+"\""
	
	strC="\""+data[1]+"\""
	earT="\""+data[2]+"\""
	try:
		command="Select expDate from impc_FlowCytometry where strainCode = %s and earTag = %s" % (strC,earT)
		cur.execute(command)
		mk=cur.fetchall()
		print ",".join(data)+","+str(mk[0][0])
	except mdb.Error,e:
		print e.args[0],e.args[1]
		sys.exit()
sys.exit()
replacer=[]
for a,b in zip(impc_manual["IMPC_IMM_002_001"],impc_manual["IMPC_IMM_026_001"]):
	replacer.append(int(a/float(100)*b))
impc_manual["IMPC_IMM_002_001"]=replacer

#cur.close()
#cnx.close()

#sys.exit()

annot=open("IMPC_parameters.csv",'r').readlines()


allK=impc_manual.keys()
allK.sort()
presentTick=[]
absentTick=[]
countme=0

badcodes=map(lambda P: "IMPC_IMM_"+P.zfill(3)+"_001",["29","30","31","38","41","43"])

allCorrs=[]
medianCounts=[]
for code in allK:
	#if code == "IMPC_IMM_002_001":
	#	pass
	#else:
	lineplot=max(impc_manual[code]+impc_automated[code])
	#print code,ticks[code],np.mean(impc_manual[code]),np.mean(impc_automated[code]),
	if code in badcodes:
		print code,"BAD",#,"\n",impc_manual[code],"\n",impc_automated[code]
		print np.mean(impc_manual[code]),np.mean(impc_automated[code])
		print "\n\n\n"
	#percentDiff=abs((impc_manual[code]-impc_automated[code])/float(impc_manual[code]))
	#allDiff=[]
	dX=[]
	dY=[]
	dD=[]
	dName=[]
	for a,b,c in zip(impc_manual[code],impc_automated[code],dataorder[code]):
		distance=dist(0,lineplot,0,lineplot,a,b)
		dX.append(a)
		dY.append(b)
		dD.append(distance)
		dName.append(c)
	annotX=[]
	annotY=[]
	annotName=[]
	for a,b,c,d in zip(dX,dY,dName,dD):
		if d >= (np.mean(dD)+2.67*np.std(dD)) or d <= (np.mean(dD)-2.67*np.std(dD)): 
			annotX.append(a)
			annotY.append(b)
			annotName.append(c)
	corr=ss.pearsonr(impc_manual[code],impc_automated[code])[0]
	if ticks[code]:
		presentTick.append(corr)
		#presentTick.append(percentDiff)
	else:
		absentTick.append(corr)
	
	allCorrs.append(corr)
	medianCounts.append(math.log(np.mean(impc_manual[code])))


	lineplot=max(impc_manual[code]+impc_automated[code])
	xy=np.vstack([impc_manual[code],impc_automated[code]])
	z=gaussian_kde(xy)(xy)
	fig,ax=plt.subplots()
	ax.scatter(impc_manual[code],impc_automated[code],c=z,s=15,edgecolor='')
	#sns.lmplot(data=np.array([impc_manual[code],impc_automated[code]]))
	#sns.plt.show()
	#sys.exit()
	#
	ax.plot(np.unique(impc_manual[code]), np.poly1d(np.polyfit(impc_manual[code],impc_automated[code],1))(np.unique(impc_manual[code])),color='r',linewidth='2')
	#ax.plot((0,lineplot),(0,lineplot),linewidth=1)
	#ax.set_ylim(0,lineplot)
	#ax.set_xlim(0,lineplot)
	#ax.annotate(annotName,xy=(annotX,annotY))
	for l,m,p in zip(annotX,annotY,annotName):
		ax.annotate(p,xy=(l,m),xycoords='data',fontsize=10)
	plt.title(code)
	plt.ylabel("Automated analysis")
	plt.xlabel("Manual analysis")
	writeit="Pearson's\ r:" +str(corr)[:5]
	ax.text(0.05,0.95,"$\mathit{"+writeit+"}$", ha='left',va='center',transform=ax.transAxes)
	#plt.scatter(impc_manual[code],impc_automated[code])
	plt.savefig(code+".pdf")
	#plt.savefig(code+".pdf")
	#break

#print ss.pearsonr(allCorrs,medianCounts)
