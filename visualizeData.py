## using Tkinter to visualize the data
from __future__ import division
#~ import pdb
import os,sys,glob
lib_path = os.path.abspath(os.path.join('.','scripts'))
sys.path.append(lib_path)
import Tkinter as tk
#import tkFileDialog as tkf
from PIL import Image, ImageTk#, ImageDraw
#from PIL.Image import core as _imagingtk
from config import *
from collections import defaultdict
from getData import ArticleEval,Fixation
from helper import *
from scaling import rescaleY

MAIN = None
BF = None
FF = None

ENCLOSED = [0,0,0,0]
ENCL_FIX = list()
MARK = list()
RM = tuple((0,0))

class SlideWindow(tk.Canvas):
	def __init__(self,master,width=1024,height=768,reworked=False):
		tk.Canvas.__init__(self,master,width=width,height=height)
		self.width = width
		self.height = height
		self.grid(rowspan=2,column=0)
		self.grid_propagate(0)
		self.v_speed = 500
		self.offsets = [0,0]
		self.y_offset = tk.StringVar()
		self.image = self.create_text((self.width/2,self.height/2),text='Choose a slide folder')
		self.border_check = tk.IntVar()
		self.speed_dict = dict()
		self.show_connection = tk.IntVar()
		self.rescaled = tk.BooleanVar(value=False)
		self.themeID = tk.StringVar()
		self.fixation_frame = None
		self.first_init = True
		self.edit_mode = tk.BooleanVar(value=False)
		self.reworked = reworked

		# dummies for the first initialization
		self.fixpointR_dict = dict()
		self.connect_dict = dict()
		self.border_visual = list()

		# speed steps
		s1 = [x for x in range(5,105,5)]
		s2 = [x*10 for x in s1]
		for i in range(20):
			self.speed_dict[s1[i]] = s2[(-1)-i]

		self.cleanArticle()

	def cleanArticle(self):
		# save the laste slide
		if not self.first_init:
			if self.edit_mode.get():
				self.saveNewFixations()

		# delete all the visuals
		for dict_ in [self.fixpointR_dict,self.connect_dict]:
			for visual in dict_.values():
				self.delete(visual[0])
		for visual in self.border_visual:
			self.delete(visual)

		# article dependent values
		self.continious = True
		self.theme = None
		self.article = None
		self.events = None
		self.current_slide = None
		self.slide_count = None
		self.act_ev_count = None
		self.fixpointR_dict = dict()
		self.connect_dict = dict()
		self.border_visual = list()
		self.border_dict = defaultdict(list)
		self.slide_dict = dict()
		self.slide_dict_path = dict()
		self.y_offset.set('0')
		self.offsets = [0,0]

	def loadData(self,tid):
		'''
		just a wrapper function for initialization
		'''
		tpath = os.path.join(SOURCE_FI_PATH,tid)
		self.theme = tid
		self.themeID.set(tid)
		self.current_slide = 0

		self.loadSlides(tpath)
		self.loadBorder(tpath)
		self.loadFixations()
		self.showSlide()

		self.slide_count = len(self.article.fixation_dict)

		if self.border_check.get():
			self.showBorder(True)

	def loadSlides(self,tpath,ext='*.png'):
		'''
		load the picture files, convert it to a Tkinter image object
		and store it
		'''
		# crawls the slide folder
		for im in glob.glob(str(os.path.abspath(tpath))+OSS+ext):
			fi = im.split(OSS)[-1]
			sid = int(fi.split('_')[-1][:-(len(ext)-1)])
			self.slide_dict_path[sid] = im

			# get the image and its size
			image = ImageTk.PhotoImage(Image.open(im))
			w = image.width()
			h = image.height()

			# check whether size is appropriate ??
			if w > self.width or h > self.height:
				pass

			# add to the dictionary
			self.slide_dict[sid] = image

	def showSlide(self,sid=0):
		'''
		shows a new slide
		'''
		if self.first_init:
			bindMouse(self)
			self.first_init = False

		image = self.slide_dict[sid]
		self.act_ev_count = 0

		self.delete(tk.ALL)
		self.image = self.create_image((0,0),anchor='nw',image=image)
		self.markRect = self.create_rectangle((0,0,0,0))#,fill="blue",stipple="gray25")
		self.getEvents(sid)
		self.fixation_frame.insertFix()

	def loadFixations(self):
		rlist = fi_dict[self.theme]
		self.article = ArticleEval(self,self.theme,gdict,rlist,reworked=self.reworked)

	def getEvents(self,sid=0):
		event_dict = self.article.fixation_dict[sid]
		self.events = [x[1] for x in sorted(event_dict.items())]
		self.rescaleFixations(sid)

	def getFolder(self,tid):
		self.cleanArticle()
		self.loadData(tid)

	def turnSlide(self,back=False):
		self.continious = False
		if not back:
			next_slide = self.current_slide+1
			if next_slide < self.slide_count:
				if self.edit_mode.get():
					self.saveNewFixations()
				self.showSlide(next_slide)
				self.current_slide += 1
		else:
			prev_slide = self.current_slide-1
			if prev_slide >= 0:
				self.showSlide(prev_slide)
				self.current_slide -= 1

		if self.border_check.get():
			self.showBorder(True)

		self.y_offset.set('0')
		self.offsets = [0,0]
		clearMarks()
		MAIN.coords(MAIN.markRect,0,0,0,0)

	def visualizeScanPath(self):
		if not self.act_ev_count >= len(self.events):
			event = self.events[self.act_ev_count]

			for eye in ['R']:
				x = event.x[eye]
				y = event.y[eye]
				if self.rescaled.get():
					y = self.scaled_y[self.act_ev_count]
				duration = event.duration[eye]

				self.drawFixPoint((x,y),eye,duration)
			self.act_ev_count += 1

			if self.act_ev_count > 1:
				ev1 = self.events[self.act_ev_count-2]
				ev2 = self.events[self.act_ev_count-1]
				self.connectPoints(ev1,ev2)

			if self.act_ev_count < len(self.events):
				if self.continious:
					self.after(self.v_speed,self.visualizeScanPath)

	def startVisualisation(self,step=None):
		acount = self.act_ev_count
		if step == 'prev':
			if acount > 0:
				for dict_ in [self.fixpointR_dict,self.connect_dict]:
					if len(dict_) != 0:
						visual = dict_[acount-1][0]
						self.delete(visual)
						del dict_[acount-1]
				self.act_ev_count -= 1
			self.continious = False
		else:
			if acount < len(self.events):
				if not step:
					self.continious = True
				elif step == 'next':
					self.continious = False
				self.visualizeScanPath()

	def pauseVisualisation(self):
		self.continious = False

	def drawFixPoint(self,coord,eye,duration):
		x,y = coord[0]+self.offsets[0],coord[1]+self.offsets[1]
		dur = round(duration/100000)
		color = 'red'
		if duration/1000 <= MIN_DUR:
			color = 'green'

		if eye == 'R':
			x1,x2 = x-(2+dur),x+(2+dur)
			y1,y2 = y-(2+dur),y+(2+dur)
			self.fixpointR_dict[self.act_ev_count] = (self.create_oval((x1,y1,x2,y2),fill=color,tags=self.act_ev_count),(x1,y1,x2,y2))

	def connectPoints(self,ev1,ev2):
		x1,y1 = ev1.x['R']+self.offsets[0], ev1.y['R']+self.offsets[1]
		x2,y2 = ev2.x['R']+self.offsets[0], ev2.y['R']+self.offsets[1]
		if self.rescaled.get():
			y1 = self.scaled_y[self.act_ev_count-2]
			y2 = self.scaled_y[self.act_ev_count-1]

		dash = None
		color = 'black'
		if x2 < x1:
			if ev2.eid in self.article.linesweep_dict[self.current_slide]:
				dash = (4,4)
				color = 'red'
			else:
				dash = (4,4)
		self.connect_dict[self.act_ev_count-2] = (self.create_line(x1,y1,x2,y2,dash=dash,fill=color,tags=ev1.eid),(x1,y1,x2,y2))

		if not self.show_connection.get():
			self.itemconfig(self.connect_dict[ev1.eid-1][0],state='hidden')

	def loadBorder(self,tpath):
		snr = 0
		for line in open(os.path.join(tpath,'border.txt')):
			line = line.rstrip('\n')
			if line[:3] == '>>>':
				snr = int(line.split()[-1])
			else:
				tlist = [eval(x) for x in line.split('\t')]
				self.border_dict[snr].extend(tlist)

	def showBorder(self,state):
		snr = self.current_slide
		if state:
			for rect in self.border_dict[snr]:
				x1,y1 = rect[0],rect[1]-Y_FIX
				x2,y2 = rect[0]+rect[2],rect[1]+rect[3]+Y_FIX
				self.border_visual.append(self.create_rectangle(x1,y1,x2,y2))
		else:
			for border in self.border_visual:
				self.delete(border)

	def adjustSpeed(self,speed):
		self.v_speed = self.speed_dict[speed]

	def showCompletePath(self,end='none'):
		self.continious = False
		act_ev = self.act_ev_count
		if end == 'none':
			end = len(self.events)
		for i in range(act_ev,end):
			event = self.events[i]

			for eye in ['R']:
				x = event.x[eye]
				y = event.y[eye]
				if self.rescaled.get():
					y = self.scaled_y[i]
				duration = event.duration[eye]

				self.drawFixPoint((x,y),eye,duration)

			self.act_ev_count += 1

			if self.act_ev_count > 1:
				ev1 = self.events[self.act_ev_count-2]
				ev2 = self.events[self.act_ev_count-1]
				self.connectPoints(ev1,ev2)

	def clearCompletePath(self):
		self.continious = False
		self.act_ev_count = 0
		for dict_ in [self.fixpointR_dict,self.connect_dict]:
			for visual in dict_.values():
				self.delete(visual[0])
			dict_.clear()

	def toggleCon(self,state):
		if state:
			for connect in self.connect_dict.values():
				self.itemconfig(connect[0],state='normal')
		else:
			for connect in self.connect_dict.values():
				self.itemconfig(connect[0],state='hidden')

	def saveCurrentImage(self):
		self.postscript(file="tmp.ps", colormode='color')

	def rescaleFixations(self,sid):
		for eye in ['R']:
			X = [event.y[eye] for event in self.events]

			fl = checkLine(X)
			ll = checkLine(X,True)
			#~ fl = 1
			#~ ll = self.article.line_count[sid]

			min_= LINES[fl][0]-Y_FIX
			max_= LINES[ll][1]+Y_FIX

			self.scaled_y = [y[0] for y in rescaleY(X,min_,max_)]

	def toggleScale(self):
		act_count = self.act_ev_count
		self.clearCompletePath()
		self.showCompletePath(end=act_count)
		clearMarks()

	def saveNewFixations(self):
		finame = fi_dict[self.theme][self.current_slide]
		opath = REWORKED_FI_PATH
		try: 
			os.makedirs(opath)
		except OSError:
			if not os.path.isdir(opath):
				raise
		ofile = open(os.path.join(opath,finame),'w')

		events = self.events
		fdraw_dict = self.fixpointR_dict
		# events is a sorted list of all possible fixations on this slide
		# fdraw_dict contains only fixations that are drawn on the slide
		# keys in fdraw_dict start from 0 and have a tuple as value
		# -> first item in tuple is the 'oval-item' of the canvas-widget
		# -> second item is the original draw-coordinate

		print>>ofile, 'Number\tStart\tEnd\tDuration\tLocation X\tLocation Y\n'
		for id_ in range(len(fdraw_dict)):
			to_print = []
			fixp = fdraw_dict[id_][0]
			ty = self.coords(fixp)
			try:
				new_y = round(((ty[1]+ty[3])/2),2)
			except IndexError:
				print 'empty coords; line 405'
				pass

			try:
				to_print.append(events[id_].eid)			# id
				to_print.append(events[id_].start['R'])		# start
				to_print.append(events[id_].end['R'])		# end
				to_print.append(events[id_].duration['R'])	# duration
				to_print.append(events[id_].x['R'])			# x-value right eye
				to_print.append(new_y)						# fixed y value

				print>>ofile, '\t'.join([str(x) for x in to_print])
			except IndexError:
				print 'error in events and fixpointR_dict length'
				pass

class FixationFrame(tk.Frame):
	def __init__(self,master,slide_win,width=150):#,height=768):
		tk.Frame.__init__(self,master,width=width)#,height=height)#,bd=1,relief=tk.SUNKEN)
		self.grid_propagate(0)
		self.grid(row=1,column=1)
		self.fix_list = []
		self.master = master
		self.slide_win = slide_win
		slide_win.fixation_frame = self

		self.createListBox()

	def createListBox(self):
		self.lbox = tk.Listbox(self)
		self.lbox.pack(side=tk.LEFT)
		self.lbox.bind('<Button-1>',self.chooseFix)

		self.scrollbar = tk.Scrollbar(self)
		self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.scrollbar.config(command=self.lbox.yview)
		self.lbox.config(yscrollcommand=self.scrollbar.set)

	def insertFix(self):
		self.lbox.delete(0,tk.END)
		for i in self.slide_win.events:
			self.lbox.insert(tk.END,str(i.eid))

	def chooseFix(self,event):
		index = self.lbox.nearest(event.y)
		print self.lbox.get(index)

class ButtonFrame(tk.Frame):
	'''
	the class for creating and visualizing the frame with all the
	buttons and stuff
	'''
	def __init__(self,master,slide_win):
		tk.Frame.__init__(self,master,width=150,height=500)
		self.grid_propagate(0)
		self.grid(row=0,column=1)
		self.master = master
		self.slide_win = slide_win

		self.addButtons()

	def addButtons(self):
		#~ # Place holder
		place_holder0 = tk.Frame(self,height=30)
		place_holder0.grid(row=0)

		# Slide Control
		self.slide_control = tk.Frame(self,bd=1,relief=tk.SUNKEN)
		self.slide_control.grid(row=1,sticky=tk.W)

		self.label_theme = tk.Label(self.slide_control,text='Theme ID')
		self.label_theme.grid(row=0,column=0)

		self.entry_theme = tk.Entry(self.slide_control,width=10,justify='right',state='readonly',textvariable=self.slide_win.themeID)
		self.entry_theme.grid(row=0,column=1,sticky=tk.E)

		self.createThemeMenu(self.slide_control)

		self.button_turnSlideBack = tk.Button(self.slide_control,text='< Page',command=lambda: self.slide_win.turnSlide(back=True))
		self.button_turnSlideBack.grid(row=2,column=0,sticky=tk.E)

		self.button_turnSlide = tk.Button(self.slide_control,text='Page >',command=lambda: self.slide_win.turnSlide())
		self.button_turnSlide.grid(row=2,column=1,sticky=tk.W)

		self.button_quit = tk.Button(self.slide_control,text='Quit', fg='red', command=self.master.quit)
		self.button_quit.grid(row=3,columnspan=2)

		# Place holder
		place_holder1 = tk.Frame(self,height=30)
		place_holder1.grid(row=2)

		# Visualization Control
		self.visualization_control = tk.Frame(self,bd=1,relief=tk.SUNKEN)
		self.visualization_control.grid(row=3,sticky=tk.W)

		self.button_start = tk.Button(self.visualization_control,text='Play',command=lambda: self.slide_win.startVisualisation())
		self.button_start.grid(row=0,column=0,sticky=tk.E)

		self.button_pause = tk.Button(self.visualization_control,text='Pause',command=lambda: self.slide_win.pauseVisualisation())
		self.button_pause.grid(row=0,column=1,sticky=tk.W)

		self.button_pStep = tk.Button(self.visualization_control, text='<<<', command=lambda: self.slide_win.startVisualisation(step='prev'))
		self.button_pStep.grid(row=1,column=0,sticky=tk.E)

		self.button_nStep = tk.Button(self.visualization_control, text='>>>', command=lambda: self.slide_win.startVisualisation(step='next'))
		self.button_nStep.grid(row=1,column=1,sticky=tk.W)

		self.button_clearAll = tk.Button(self.visualization_control, text='< Start', command=lambda: self.slide_win.clearCompletePath())
		self.button_clearAll.grid(row=2,column=0,sticky=tk.E)

		self.button_showAll = tk.Button(self.visualization_control, text='End >', command=lambda: self.slide_win.showCompletePath())
		self.button_showAll.grid(row=2,column=1,sticky=tk.W)

		place_holder3 = tk.Frame(self.visualization_control,height=10)	# gap between speed
		place_holder3.grid(row=3,columnspan=2)							# and stuff above

		self.scale_speed = tk.Scale(self.visualization_control,from_=5, to=100, resolution=5, label='Speed', orient='horizontal', command=self.changeSpeed)
		self.scale_speed.set(50)
		self.scale_speed.grid(row=4,columnspan=2)

		# Place holder
		place_holder2 = tk.Frame(self,height=30)
		place_holder2.grid(row=4)

		# Show Options
		self.show_options = tk.Frame(self,bd=1,relief=tk.SUNKEN)
		self.show_options.grid(row=5,sticky=tk.W)

		self.check_border = tk.Checkbutton(self.show_options, text='Show Border', command=lambda: self.slide_win.showBorder(self.slide_win.border_check.get()), variable=self.slide_win.border_check)
		self.check_border.grid(row=0,column=0,sticky=tk.W)

		self.check_path = tk.Checkbutton(self.show_options, text='Show Connection', command=lambda: self.slide_win.toggleCon(self.slide_win.show_connection.get()), variable=self.slide_win.show_connection)
		self.check_path.select()
		self.check_path.grid(row=1,column=0,sticky=tk.W)

		self.check_left = tk.Checkbutton(self.show_options, text='Rescale Y-Values', command=lambda: self.slide_win.toggleScale(), variable=self.slide_win.rescaled)
		self.check_left.grid(row=2,column=0,sticky=tk.W)

		self.check_left = tk.Checkbutton(self.show_options, text='Edit Mode', variable=self.slide_win.edit_mode)
		self.check_left.grid(row=3,column=0,sticky=tk.W)

		# Place holder
		place_holder3 = tk.Frame(self,height=30)
		place_holder3.grid(row=6)

		# Save Options
		self.save_options = tk.Frame(self,bd=1,relief=tk.SUNKEN)
		self.save_options.grid(row=7,sticky=tk.W)

		self.button_save = tk.Button(self.save_options,text='Save Image',command=self.slide_win.saveCurrentImage)
		self.button_save.grid(row=0,column=0)
		#~ self.button_save.config(state=tk.DISABLED)

	def createThemeMenu(self,master,text='Get Article',relief=tk.RAISED,row=1,column=None,cspan=2):
		self.button_getFolder = tk.Menubutton(master,text=text,relief=relief)
		self.button_getFolder.grid(row=row,column=column,columnspan=cspan)
		self.button_getFolder.menu = tk.Menu(self.button_getFolder,tearoff=0)
		self.button_getFolder['menu'] = self.button_getFolder.menu

		self.themeID = tk.StringVar()
		idtotheme = open('id_to_theme.txt').readlines()
		tdict = {}
		for line in idtotheme:
			line = line.rstrip('\n').split('\t')
			tdict[line[0]] = line[1]
		for i in EX_DICT:
			self.button_getFolder.menu.add_radiobutton(label=tdict[i],value=i,variable=self.themeID,command=self.getTheme)

	def getTheme(self):
		tid = str(self.themeID.get())
		self.slide_win.getFolder(tid)

	def changeSpeed(self,speed):
		self.slide_win.adjustSpeed(int(speed))

### ~~~ ###

def markInFixList(mlist):
	for i in mlist:
		FF.lbox.selection_set(i[0])
	if len(mlist):
		FF.lbox.see(mlist[0][0])

def toggleMarkOnSlide(mark):
	global MARK
	tlist = []
	ldict = {}
	if mark:
		if len(ENCL_FIX):
			for i in ENCL_FIX:
				i = i[1]
				MAIN.itemconfig(i,outline='blue',width=2.)

				tag = int(MAIN.gettags(i)[0])
				tlist.append(tag)

			for tag in tlist:
				if not tag >= len(MAIN.connect_dict):
					ldict[tag] = 'l'
					if tag+1 in tlist:
						ldict[tag] = 'b'
					if tag > 0 and tag-1 not in tlist:
						ldict[tag-1] = 'r'
				else:
					if tag > 0 and tag-1 not in tlist:
						ldict[tag-1] = 'r'
		MARK.extend([tlist,ldict])
	else:
		if len(MARK):
			for tag in MARK[0]:
				item = MAIN.fixpointR_dict[tag][0]
				MAIN.itemconfig(item,outline='black',width=1.)
			MARK = []
	# debug #
	#~ print 'mark:', MARK
	#~ print 'encl_fix:', ENCL_FIX
	#~ print 'enclosed:', ENCLOSED
	#~ print '-----'

def checkLine(X,max_=False):
	m = 9999
	for x in X:
		if x < m:
			m = x
	if max_:
		for x in X:
			if x > m:
				m = x

	l = 1
	for i,mm in LINES.iteritems():
		if m > mm[0]-Y_FIX:
			l = i

		if max_:
			# change to check for a span, because it doesnt care whether its just three (or so) lines
			if m < mm[1]+Y_FIX:
				if m > mm[0]-Y_FIX:
					l = i

	return l

def getMarkedFixations():
	global ENCL_FIX
	for item in MAIN.find_enclosed(ENCLOSED[0],ENCLOSED[1],ENCLOSED[2],ENCLOSED[3]):
		if item and MAIN.type(item) == 'oval':
			for tag in MAIN.gettags(item):
				ENCL_FIX.append((int(tag),item))

def storeMouseDown(event):
	global ENCLOSED
	clearMarks()

	ENCLOSED[0]=event.x
	ENCLOSED[1]=event.y

def storeMouseUp(event):
	global ENCLOSED
	ENCLOSED[2]=event.x
	ENCLOSED[3]=event.y

	getMarkedFixations()
	MAIN.coords(MAIN.markRect,0,0,0,0)

	markInFixList(ENCL_FIX)
	toggleMarkOnSlide(True)

def storeRightMouse(event):
	global RM
	RM = (event.x,event.y)

def drawRect(event):
	MAIN.coords(MAIN.markRect,ENCLOSED[0],ENCLOSED[1],event.x,event.y)

def moveFixedPoints(event):
	global RM
	dx = 0
	dy = event.y-RM[1]

	#~ pdb.set_trace()
	if len(MARK):
		# move point
		for tag in MARK[0]:
			fpoint = MAIN.fixpointR_dict[tag][0]
			MAIN.move(fpoint,dx,dy)

		# move line
		for tag,side in MARK[1].iteritems():
			cline = MAIN.connect_dict[tag][0]
			ccoords = MAIN.coords(cline)
			cside = side
			if cside == 'b':
				MAIN.move(cline,dx,dy)
			else:
				try:
					if cside == 'l':
						x1,y1 = ccoords[0]+dx, ccoords[1]+dy
						x2,y2 = ccoords[2], ccoords[3]
					elif cside == 'r':
						x1,y1 = ccoords[0], ccoords[1]
						x2,y2 = ccoords[2]+dx, ccoords[3]+dy
				except IndexError:
					pass
				MAIN.coords(cline,x1,y1,x2,y2)

	RM = (event.x,event.y)

def clearMarks():
	global ENCLOSED,ENCL_FIX
	FF.lbox.selection_clear(0,tk.END)
	toggleMarkOnSlide(False)

	del ENCLOSED[:]
	ENCLOSED = [0,0,0,0]
	del ENCL_FIX[:]

def pressKey(key):
	global MAIN,BF
	# for slide and theme control
	if key in ['left','right','up','down','a','w','s','d']:
		if MAIN.theme:
			if key == 'left' or key == 'a':
				MAIN.turnSlide(True)
			elif key == 'right' or key == 'd':
				MAIN.turnSlide()
			else:
				tid = MAIN.theme
				tpos = EX_DICT.index(tid)
				if key == 'up' or key == 'w':
					if tpos != 0:
						# previous theme
						tid = EX_DICT[tpos-1]
				elif key == 'down' or key == 's':
					if tpos < len(EX_DICT)-1:
						# next theme
						tid = EX_DICT[tpos+1]
				MAIN.getFolder(tid)
				BF.themeID.set(tid)

	# for visualization control
	elif key in ['space']:
		if MAIN.theme:
			if key == 'space':
				MAIN.showCompletePath()
	# one of the other keys
	else:
		pass

def bindMouse(f):
	f.bind('<Button-1>', storeMouseDown)
	f.bind('<ButtonRelease-1>', storeMouseUp)
	f.bind('<B1-Motion>', drawRect)
	f.bind('<Button-3>', storeRightMouse)
	f.bind('<B3-Motion>', moveFixedPoints)

def bindKeys(main):
	main.bind('<Left>', lambda x: pressKey('left'))
	main.bind('<Right>', lambda x: pressKey('right'))
	main.bind('<Up>', lambda x: pressKey('up'))
	main.bind('<Down>', lambda x: pressKey('down'))
	main.bind('<a>', lambda x: pressKey('a'))
	main.bind('<w>', lambda x: pressKey('w'))
	main.bind('<s>', lambda x: pressKey('s'))
	main.bind('<d>', lambda x: pressKey('d'))

	main.bind('<space>', lambda x: pressKey('space'))

	main.bind('<Key>', lambda x: pressKey(x))

def runVisualize(reworked=False):
	global MAIN,BF,FF
	root = tk.Tk()
	root.title('Eyetracking Visualization')
	root.resizable(width='false', height='false')

	slideWindow = SlideWindow(root,reworked=reworked)
	MAIN = slideWindow

	bindKeys(root)

	fixationList = FixationFrame(root,slideWindow)
	FF = fixationList

	buttons = ButtonFrame(root,slideWindow)
	BF = buttons

	root.mainloop()

if __name__ == '__main__':
	gdict = buildGooglePOS(os.path.abspath('./de-tiger.map'))

	fi_dict = createFileDictionary(RESULTS_FI_PATH,SOURCE_FI_PATH,EX_DICT)
	#~ fi_dict = createFileDictionary(RESULTS_FI_PATH,SOURCE_FI_PATH,EX_DICT,['012','006','038','021'])

	#~ pdb.run('runVisualize()')	# call for debugging
	runVisualize(reworked=REWORKED)

'''
 need to find some solution for moving the connect-line that isn't visible
 when just one point is drawn... (poss. solution below)

 it might be even better to modify the whole 'drawing' stuff,
 as you can easily draw everything on start-up and then hide/show it
 on demand. so it's no deleting and new drawing anymore...
'''
