#!/usr/bin/env python

import sys
from StringIO import StringIO
import struct
import os
import re

def fcsextract(filename):
    """
    Attempts to parse an FCS (flow cytometry standard) file
    Parameters: filename
        filename: path to the FCS file
    Returns: (vars,events)
        vars: a dictionary with the KEY/VALUE pairs found in the HEADER
        this includes the standard '$ABC' style FCS variable as well as any 
        custom variables added to the header by the machine or operator
    
        events: an [N x D] matrix of the data (as a Python list of lists)
        i.e. events[99][2] would be the value at the 3rd dimension
        of the 100th event
    """
    fcs_file_name = filename

    fcs = open(fcs_file_name,'rb')
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

    for k,l in fcs_vars.iteritems():
        if tube.match(k):
		print "\t\t\t",l
	elif k == "TUBE NAME":
		print "TUBE",l
	elif k == "$SRC":
		if 
		print "SRCE",l
	elif k == "$FIL":
		print "FIL",l
filename=sys.argv[1]
fcsextract(filename)
