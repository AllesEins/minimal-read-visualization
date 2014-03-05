# scaling

#~ import pylab as pl
#~ import matplotlib as mpl
import numpy as np

from sklearn import preprocessing

def rescaleY(Y,min_,max_):
	min_max_scaler = preprocessing.MinMaxScaler((min_,max_))
	X = np.array([[float(y)] for y in Y])
	return min_max_scaler.fit_transform(X)
