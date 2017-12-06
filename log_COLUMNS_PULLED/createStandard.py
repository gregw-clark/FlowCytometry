#!/usr/bin/env python

import string, re, sys
import glob
from collections import defaultdict,OrderedDict

ReP_A=re.compile(r"[0-9A-z\_\-]*_PANEL_A.txt$")
ReP_B=re.compile(r"[0-9A-z\_\-]*_PANEL_B.txt$")


allfiles=glob.glob("*.txt")
#print allfiles
#print len(allfiles)

panelA=filter(lambda l: ReP_A.match(l),allfiles)
panelB=filter(lambda l: ReP_B.match(l),allfiles)


varA=defaultdict(list)
for q in panelA:
	tr=open(q,'r').readlines()
	for ln in tr:
		dats=ln.strip().split("\t")
		varA[dats[0]].append(dats[1])
#print varA.keys()
#print "\n\n\n"

varB=defaultdict(list)
for q in panelB:
	tr=open(q,'r').readlines()
	for ln in tr:
		dats=ln.strip().split("\t")
		varB[dats[0]].append(dats[1])

Ao=OrderedDict(sorted(varA.items(), key = lambda t: t[0]))
opp=open("_PANEL_A_standard.txt",'w')
for fk in Ao:
	print fk,list(set(varA[fk]))[0],len(varA[fk])
	if len(varA[fk]) <105:
		print "AHHH",fk
		sys.exit()
	opp.write(fk+"\t"+list(set(varA[fk]))[0]+"\n")
opp.close()

Ao=OrderedDict(sorted(varB.items(), key = lambda t: t[0]))
opp=open("_PANEL_B_standard.txt",'w')
for fk in Ao:
	print fk,list(set(varB[fk]))[0],len(varB[fk])
	if len(varB[fk]) <105:
		print "AHHH",fk
		sys.exit()
	opp.write(fk+"\t"+list(set(varB[fk]))[0]+"\n")
opp.close()
