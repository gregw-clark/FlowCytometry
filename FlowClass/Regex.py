#!/usr/bin/env python

import string,re

class rgx:

	fcs_path_re = re.compile(r"/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES/(IMPC RUNS/){0,1}201[4567][\-_][0-9]{2}[\-_][0-9]{2}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/IMPC[\W\-_]{1,3}96[\W]+well[\W]+U[\W\-_]{1,3}bottom$",re.IGNORECASE)
	xl_path_re = re.compile(r"/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES/(IMPC RUNS/){0,1}201[4567][\-_][0-9]{2}[\-_][0-9]{2}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/Analysis[\-_]201[4567][\-_][0-9]{2}[\-_][0-9]{2}/IMPC[\W\-_]*[12]$",re.IGNORECASE)


	### These were used for a special case --- "Submit_automated" 
	#fcs_path_re = re.compile(r"/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES/Submit_automated[\W+]+analysis/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/IMPC[\W\-_]{1,3}96[\W]+well[\W]+U[\W\-_]{1,3}bottom$",re.IGNORECASE)
	#xl_path_re = re.compile(r"/mnt/cmmr/BD Fortessa Backup/BDExport/FCS/201[4567][\W]+IMPC[\W]+FCS[\W]+FILES/Submit_automated[\W+]+analysis/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/201[4567][\-_][0-9]{2}[\-_][0-9]{2}/Analysis[\-_]201[4567][\-_][0-9]{2}[\-_][0-9]{2}/IMPC[\W\-_]*[12]$",re.IGNORECASE)


	FluoroMatch=re.compile("""Compensation(\W|-|_){1,3}Controls(\W|-|_){0,3}(
		(CD25(\s|-|_){0,2}PE(\s|-|_){0,2}CY7)|
		(BV421)|
		(BV510)|
		(BV786)|
		(FITC)|
		(PE)|
		(APC)|
		(CD8a(\s|-|_){0,2}PE(\s|-|_){0,2}CF594)|
		(CD11b(\s|-|_){0,2}PE(\s|-|_){0,2}CF594)|
		(CD11C(\s|-|_){0,2}PE(\s|-|_){0,2}CY7)|
		(CD62L(\s|-|_){0,2}APC(\s|-|_){0,2}CY7)|
		(MHCII(\s|-|_){0,2}APC(\s|-|_){0,2}CY7)
		)""",flags=re.X | re.I)

	##These are the particular file types we are interested in
	FMOfiles=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}(A|B)""",flags=re.X|re.I)
	MatrixF=re.compile("""[A-z0-9\s_\-,]*MATRIX[A-z0-9\s_\-,]+[\.]mtx""",flags=re.X|re.I)
	PanelFiles=re.compile("PANEL[\W_]{0,3}[AB][\W_]{1,2}[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}_[A-z0-9]{2,12}.fcs", flags = re.X | re.I)
	wspFiles=re.compile("IMPC[12]_201[4567]\-[012][0-9]\-[0123][0-9](_PANEL[AB]){0,1}\.(wspt|wsp)$", flags = re.X | re.I)
	UnstainedFiles=re.compile("^UNSTAINED[A-z0-9_\-\+]+\.fcs$",flags=re.X | re.I)	
	UnstainedSytox=re.compile("^UNSTAINED[A-z0-9_\-\+]+SYTOXBLUE[A-Z0-9]+\.fcs$",flags=re.X | re.I)	

	compDir=re.compile("IMPC[\W_]+96[\W_]+Well[\W_]+U[\W_]+bottom",flags=re.X | re.I)


	compFileNameA=re.compile("[A-z_]*PANELA$",flags=re.X|re.I)
	compFileNameB=re.compile("[A-z_]*PANELB$",flags=re.X|re.I)
	compFiles=re.compile("Compensation",flags=re.X|re.I)

	controlonly=re.compile("[B][6][N][C]_[0-9]{1,4}")
	omitcontrol=re.compile("(^STAINED)|(Control)|(FMO)|(^UNSTAINED)|(^Specimen)|(,3a,)",flags=re.X | re.I)


	correctPanel=re.compile("PANEL_[AB]_[AB][A-Z6][A-Z][A-Z]_[0-9]{1,5}_[A-z_0-9]+.fcs",flags=re.X)
	headerfilter=re.compile("[A-z0-9\,\-\+]+[\s]{0,3}\|[\s]{0,3}Count$",flags=re.X | re.I)
	percentB=re.compile("CLOG-\/Live[\s]{0,3}\|[\s]{0,3}Freq.[\s]{0,3}of[\s]+Parent",flags=re.X | re.I)
	clogcount=re.compile("CLOG-[\s]{0,3}\|[\s]{0,3}Count$",flags= re.X | re.I)	

	file_re = re.compile(r'.+\.(xlsx|xls|fcs)$', re.IGNORECASE)

	validname=re.compile("Panel[_\s][AB]_[A-Z][A-Z6][A-Z][A-Z]_[0-9]{1,4}_",flags=re.X | re.I)
	datex=re.compile("[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]")
	dateonly=re.compile("^[2][0][1][0-9][-_][0-1]{0,1}[0-9][_-][0-3]{0,1}[0-9]$")

	impx=re.compile("IMPC[\W\-_]+[12]")
	impcA=re.compile("IMPC[\W\-_]*1$")
	panelA=re.compile("PANEL[\W\-_]*A")
	panelB=re.compile("PANEL[\W\-_]*B")
	impcB=re.compile("IMPC[\W\-_]*2$")
	xlsex=re.compile("xls$|xlsx$")

	#Should be harmonized in scripts
	straintag=re.compile("_[A-Z][A-Z6][A-Z][A-Z]_[0-9]{1,4}_",flags=re.X|re.I)
	ProperCode=re.compile("[AB][A-Z6][A-Z][A-Z]_[0-9]{1,6}", flags = re.X | re.I)

	#PANEL_A
	cd5_A=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD5[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd161_A=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD161[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd44=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD44[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd8a=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD8A[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd62l=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD62L[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd25=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}A_CD25[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)

	#PANEL_B
	cd5_B=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD5[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd161_B=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD161[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd11B=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD11B[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd11C=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD11C[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	mhc=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_MHCII[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd21_35=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD21(,2f,){0,1}[,\-\\/]{0,1}35[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	cd23=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_CD23[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)
	ly6c=re.compile("""FMO(\s|-|_){1,3}PANEL(\s|-|_){0,3}B_LY6C[_]{0,1}[A-Z0-9]+\.fcs""",flags=re.X|re.I)



		######### END OF REGEX SECTION
