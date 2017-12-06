#!/usr/bin/env python

import numpy as np
from sklearn import mixture
import sys

np.random.seed(1)
g=mixture.GMM(n_components=2)

obs=np.concatenate((np.random.randn(100,1), 10 +np.random.randn(300,1)))

obs=np.matrix([[p] for p in range(2000,5000)+range(100,200)])
#ibs=np.concatenate(myarray)
#print myarray.shape
#print ibs.shape

#print obs.shape

#ibs=np.array(np.random.randn(100,1)+np.random.randn(300,1))
#print ibs[0]
#print obs[0],obs[0][0]
#print obs[399]
#)
#sys.exit()


for comps in range(1,6):
	g=mixture.GMM(n_components=comps)
	fitting=g.fit(obs)
	
	print comps,g.aic(obs),g.bic(obs)
	#print g.bic(obs)

	print "weights",list(np.round(g.weights_,2))
	print "means",list(np.round(g.means_,2))
	print "covars",list(np.round(g.covars_,2))
	print"\n"


