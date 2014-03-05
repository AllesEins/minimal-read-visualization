# evaluates the eyetracking data
from __future__ import division
import sys,os,glob,re
import sklearn.cluster as skcluster
import numpy as np
from config import *
lib_path = os.path.abspath(os.path.join('..','scripts'))
sys.path.append(lib_path)
lib_path = os.path.abspath(os.path.join('..','corpora'))
sys.path.append(lib_path)
from collections import defaultdict,OrderedDict
from operator import itemgetter,attrgetter
from helper import *


## FUNCTIONS ##
def createFixDict(article):
	'''
	creates a fixation dictionary, that has the IDs (given in the corpus) as keys
	and whether this token was fixated (number of fixations), skipped (0) or not regarded ('NA')
	'''
	art = article
	slide_turn = art.slide_turn_dict
	slide = 0
	sorted_fix_dict = sorted(art.fixation_dict[slide].values(),key=attrgetter('eid'))
	conll = os.path.join(THEMES_FI_PATH,art.theme,'tree.conll')
	count = 0
	fix_dict = defaultdict(int)
	fix_count = 0

	for line in open(conll).readlines():
		line = line.rstrip('\n')
		if not  re.match(r'^\s*$', line):
			tindex = None
			line = line.split('\t')
			tid = line[0]

			# gets the slide number on which tid is located
			if tid in slide_turn:
				slide = slide_turn[tid]
				sorted_fix_dict = sorted(art.fixation_dict[slide].values(),key=attrgetter('eid'))
			# gets the index of tid to be mapped in border_dict
			if tid in art.conllID_dict[slide]: tindex = art.conllID_dict[slide].index(tid)

			if tindex >= 0:
				tborder = art.border_dict[slide][tindex]
				fix_dict[tid] = 0
				# check whether token was fixated or not
				for event in sorted_fix_dict:
					x = event.x['R']
					y = event.y['R']
					if x >= tborder[0] and x <= tborder[0]+tborder[2]:
						if y >= tborder[1]-Y_FIX and y <= tborder[1]+tborder[3]+Y_FIX:
							fix_dict[tid] +=1
							fix_count += 1
			else:
				# token gets NA marker
				fix_dict[tid] = 'NA'

			count += 1
	return fix_dict

def createIOB(art_class,theme):
	crf = open(os.path.join(RESULTS_FI_PATH,'iob','tree_'+theme+'.iob'),'w')
	fix = createFixDict(art_class)
	conll = os.path.join(THEMES_FI_PATH,theme,'tree.conll')

	for line in open(conll).readlines():
		line = line.rstrip('\n')
		if not  re.match(r'^\s*$', line):
			line = line.split('\t')
			tid = line[0]
			tword = line[1]
			print>>crf, '\t'.join([tid, tword, str(fix[tid])])
		else:
			print>>crf, ''

## CLASSES ##

	### desc for an evaluated ArticleEval() class ###
	# article_class.fixation_dict[slide_id][event_id]
	# 	--> ~.eid
	# 	--> ~.eyes
	# 	--> ~.start
	# 	--> ~.end
	# 	--> ~.duration
	# 	--> ~.x
	# 	--> ~.y
	#		--> ~['R'] or ~['L']
	### end desc ###

class Fixation():
	'''
	class that is called by ArticleEval() and manages the events in the eyetracking output
	'''
	def __init__(self,owner,eid):
		self.owner = owner
		self.eid = eid
		self.est_line = 0
		self.eyes = {'R':False,'L':False}
		self.start = {'R':0,'L':0}
		self.end = {'R':0,'L':0}
		self.duration = {'R':0,'L':0}
		self.x = {'R':0,'L':0}
		self.y = {'R':0,'L':0}

	def update(self,eye,start,end,dur,x,y):
		self.eyes[eye] = True
		self.start[eye] = int(start)
		self.end[eye] = int(end)
		self.duration[eye] = int(dur)
		self.x[eye] = float(x)
		self.y[eye] = float(y)

class ArticleEval():
	def __init__(self,owner,theme,gdict,rlist,reworked=False):
		self.owner = owner
		self.theme = theme
		self.gdict = gdict
		self.result_list = rlist
		self.tree_path = os.path.join(THEMES_FI_PATH,theme,'tree.conll')
		self.iob_path = os.path.join(THEMES_FI_PATH,theme,'crf.iob')
		self.rect_path = os.path.join(SOURCE_FI_PATH,theme,'border.txt')
		self.fixation_dict = defaultdict(dict)
		self.border_dict = defaultdict(list)
		self.conllID_dict = defaultdict(list)
		self.tcount_dict = dict()
		self.slide_turn_dict = dict()
		self.mean_y_dict = defaultdict(dict)
		self.linesweep_dict = defaultdict(list)
		self.line_count = dict()
		self.reworked = reworked

		self.readBorder()
		self.getTokenCount()
		self.getSlideTokens()
		self.readFixation()
		self.getEstimatedLine()

	def readBorder(self):
		'''
		creates a dictionary that gives the word-fixation-border tuples
		that were positioned on each slide
		'''
		snr = 0
		lc = 0

		for line in open(self.rect_path):
			line = line.rstrip('\n')
			if line[:3] == '>>>':
				snr = int(line.split()[-1])
				if snr > 0:
					self.line_count[snr-1] = lc
					lc = 0
			else:
				lc += 1
				tlist = [eval(x) for x in line.split('\t')]
				self.border_dict[snr].extend(tlist)
		self.line_count[snr] = lc

	def getTokenCount(self):
		'''
		gets the number of tokens that were positioned on each slide
		'''
		for i,j in self.border_dict.iteritems():
			self.tcount_dict[i] = len(j)

	def getSlideTokens(self):
		'''
		creates a dictionary that gives the token IDs for each slide
		the lists in this slide-dictionary are mappable with the lists
		in the border-dictionary
		'''
		slide = 0
		count = 0
		slide_turn = True

		for line in open(self.tree_path).readlines():
			line = line.rstrip('\n')
			if not  re.match(r'^\s*$', line):
				line = line.split('\t')
				tid = line[0]
				token = line[1]
				pos = line[4]

				if token in ['-']:
					count += 1
					self.conllID_dict[slide].append(tid)
				elif self.gdict[pos] == '.' or token == '%':
					# only counts if the token is not attached to another
					# token because it's punctuation or a percentage sign
					pass
				else:
					count += 1
					self.conllID_dict[slide].append(tid)

				if slide < len(self.tcount_dict):
					if slide_turn:
						self.slide_turn_dict[tid]=slide
						slide_turn = False
					if count == self.tcount_dict[slide]:
						slide += 1
						count = 0
						slide_turn = True

	def readFixation(self):
		'''
		reads the stimuli result files
		'''

		slide = 0
		for result in self.result_list:
			start = False

			if not self.reworked:
				fi = os.path.join(RESULTS_FI_PATH,result)
				for line in open(fi).readlines():
					line = line.rstrip('\n')
					if start:
						if not re.match(r'^\s*$', line):
							if line[:10] == 'Fixation R':
								self.getFixValues(line,slide)
					else:
						if line[:10] == 'Fixation R':
							self.getFixValues(line,slide)
							start = True
			else:
				fi = os.path.join(REWORKED_FI_PATH,result)
				for line in open(fi).readlines()[2:]:
					line = line.rstrip('\n')
					if not re.match(r'^\s*$', line):
						self.getFixValues(line,slide,reworked=True)
			slide += 1

	def getFixValues(self,line,slide,reworked=False):
		'''
		creates a dicitonary with slides and event numbers that has the
		according Fixation class as values
		'''
		skip = False
		line = line.split('\t')
		if not reworked:
			ev_eye = line[0].split()[1]
			ev_nr = int(line[2])
			ev_start = int(line[3])
			ev_end = int(line[4])
			ev_dur = int(line[5])
			ev_x = float(line[6])#.split('.')[0])
			ev_y = float(line[7])#.split('.')[0])
		else:
			ev_eye = 'R'
			ev_nr = int(line[0])
			ev_start = int(line[1])
			ev_end = int(line[2])
			ev_dur = int(line[3])
			ev_x = float(line[4])
			ev_y = float(line[5])

		# skips any first fixationpoints that are in the lower screen
		if ev_nr < 4:
			if ev_y > 250.0:
				skip = True

		if not skip:
			if ev_nr not in self.fixation_dict[slide]:
				self.fixation_dict[slide][ev_nr] = Fixation(self,ev_nr)
			self.fixation_dict[slide][ev_nr].update(ev_eye,ev_start,ev_end,ev_dur,ev_x,ev_y)

	def getEstimatedLine(self):
		ldict = dict()
		for i in range(1,13):
			ldict[i] = []

		for sid in range(len(self.fixation_dict)):
			mean_y = defaultdict(list)
			sline = 1
			events = sorted(self.fixation_dict[sid].items())
			ev_count = 0
			for event in events:
				event = event[1]
				if ev_count > 0:
					if (events[ev_count-1][1].x['R'] - event.x['R']) >= MAX_REG_X:
						if (event.y['R'] - events[ev_count-1][1].y['R']) >= MAX_REG_Y:
							self.linesweep_dict[sid].append(event.eid)
							sline += 1

				mean_y[sline].append(event.y['R'])
				event.est_line = sline
				ev_count += 1

			for i in range(1,sline+1):
				self.mean_y_dict[sid][i] = sum(mean_y[i])/len(mean_y[i])

		#~ for i in range(len(self.fixation_dict)):
			#~ print self.mean_y_dict[i].keys()
		#~ sys.exit()


if __name__ == '__main__':
	fi_dict = createFileDictionary(RESULTS_FI_PATH,SOURCE_FI_PATH,EX_DICT)
	gdict = buildGooglePOS(os.path.abspath('../Corpora/de-tiger.map'))

	### testing area ###
	for theme in EX_DICT[:3]:
		rlist = fi_dict[theme]
		art = ArticleEval(None,theme,gdict,rlist)

		#~ x = []
		#~ y = []
		#~ for slide in art.fixation_dict.values():
			#~ for event in sorted(slide.values()):
				#~ x.append(event.x['R'])
				#~ y.append(event.y['R'])
		#~ X = np.array([x,y])
	### testing end ###


### To Do ###
"""
how to handle the two eyes? right now I just regard the right one (in createFixDict)?!
"""
