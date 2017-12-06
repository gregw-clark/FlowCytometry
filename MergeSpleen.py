#!/usr/bin/env python

import string, re, sys

op=open("SpleenWeights.csv",'r').readlines()

weights={}
po=open("Query5.csv",'r').readlines()
print po[0]
po.pop(0)
for line in po:
	data=line.strip().split(",")
	weights[data[0]]=data[1]
newfile=open("PleenWeights.csv",'w')
newfile.write(op[0])
op.pop(0)
newfile=open("SpleenWeights_gwc.csv",'w')

for line in op:
	data=line.strip().split(",")
	['2016-04-07', 'ABYD', '205', '394305', 'None']
	date,code,tag,bcode,weight=data
	if weight == "None":
		try:
			weight=weights[bcode]
		except KeyError:
			print date,code,tag,bcode,weight
	newfile.write(",".join([date,code,tag,bcode,weight])+"\n")
newfile.close()		
				#print "Missing", date,code,tag,bcode
	
