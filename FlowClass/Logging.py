#!/usr/bin/env python

import os


class Log:

	#def __init__(self):
	log=False
	basedir="/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/"
	logdir="/home/clarkg/FLOWcyto/_logFiles_/"
	memfile=[]

	def start_log(self):
		if not self.log:
			return
		logfile=os.path.join(self.logdir,"completed.txt")
		if not os.path.exists(logfile):
			os.system("touch "+logfile)
		else:
			self.memfile=open(logfile,'r').readlines()
			tmp=open(os.path.join(self.logdir,"tempcompleted.txt"),'w')
	def end_log(self):
		if not self.log:
			return
		logfile=os.path.join(self.logdir,"completed.txt")
		if len(self.memfile):
			kl=open(logfile,'w')
			kl.write("".join(self.memfile))
			kl.close()
		tmpfile=os.path.join(self.logdir,"tempcompleted.txt")
		if os.path.exists(tmpfile):
			os.system("rm "+tmpfile)
											
