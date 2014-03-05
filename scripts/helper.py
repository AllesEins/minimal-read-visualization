## helper functions
from __future__ import division
from collections import defaultdict
import sys,os,glob,re

OSS = '/'
if sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
	OSS = '\\'

SOURCE_FI_PATH = os.path.abspath('./source_data')

def createFileDictionary(results,source,exp,ch=None):
	'''
	function for creating a list of eyetracker output files that belong to a theme
	'''
	fdict = defaultdict(list)
	scdict = getSlideCount(source)
	fi_list = glob.glob(results+'/*')

	fid = 0
	theme_list = exp
	if ch == list:
		theme_list = ch

	for tkey in theme_list:
		for slide in range(scdict[tkey]):
			fdict[tkey].append(fi_list[fid+slide].split(OSS)[-1])
		fid += (slide+1)
	return fdict

def buildGooglePOS(google_map):
	'''
	builds a mapping dictionary for STTS POS to the Google POS
	'''
	google_dict = {}
	for line in open(google_map).readlines():
		line = line.rstrip('\n')
		line = line.split()

		google_dict[line[0]] = line[1]
	return google_dict

def getInt(sid):
	'''
	transforms a string digit (e.g. '024') to an integer
	'''
	digit = [int(sid[0]),int(sid[1]),int(sid[2])]
	return digit[0]*100 + digit[1]*10 + digit[2]

def increaseFID(tkey):
	'''
	increases a string digit by 1
	(maybe think about a way to increase by an arbitrary number)
	'''
	digit = [int(tkey[0]),int(tkey[1]),int(tkey[2])]

	digit[2] += 1
	if digit[2] > 9:
		digit[2] = 0
		digit[1] += 1
		if digit[1] > 9:
			digit[1] = 0
			digit[0] += 1

	return str(digit[0])+str(digit[1])+str(digit[2])

def changeToFID(x):
	'''
	transforms an integer to a string digit
	'''
	d1 = str(x)[-1]
	d2 = '0'
	d3 = '0'
	if x >= 10:
		d2 = str(x)[-2]
	if x >= 100:
		d3 = str(x)[0]

	return d3+d2+d1

def getSlideCount(source):
	'''
	function for counting the slides in a theme folder
	'''
	cdict = {}
	for foo in glob.iglob(source+'/*'):
		theme = foo.split(OSS)[-1]
		scount = len(glob.glob(foo+'/*.png'))
		cdict[theme] = scount
	return cdict

def removeFile():
	mpath = os.path.abspath('./themes')
	for p in glob.iglob(mpath+OSS+'*'):
		rsfi = os.path.join(p,'rscores.txt')
		tfi = os.path.join(p,'tree.iob')
		sfi = os.path.join(p,'tscores')

		for i in [rsfi,tfi]:
			if os.path.exists(i):
				os.remove(i)
		if os.path.exists(sfi):
			os.rename(sfi,sfi+'_koRpus')

if __name__ == '__main__':
	pass
