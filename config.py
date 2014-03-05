## GLOBALS ##
import sys,os

OSS = '/'
if sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
	OSS = '\\'

VP = 'P02'
RUN = 'first'
RESULTS_FI_PATH = os.path.abspath('/'.join(['.',VP,RUN]))
REWORKED_FI_PATH = os.path.join(RESULTS_FI_PATH,'reworked')
SOURCE_FI_PATH = os.path.abspath('./source_data')
THEMES_FI_PATH = os.path.abspath('./themes')

# name of the themes for each block
f01 =  '012,006,038,021,032,\
		029,024,022,037,002,\
		004,015,009,041,049,\
		011,035,042,023,016'.replace('\t','')

f02 =  '034,014,017,048,027,\
		019,007,030,010,043,\
		020,039,018,025,045,\
		001,031,036,050,044'.replace('\t','')

# because VP 02 just did the first Block...
if VP not in ['P02']:
	EX_DICT = (f01+','+f02).split(',')
else:
	EX_DICT = f01.split(',')

# added for a minimal working example with fewer slides
EX_DICT = EX_DICT[:4]

MAX_REG_X = 300
MAX_REG_Y = 20
Y_FIX = 4
MIN_DUR = 100.0

COLOR = {'white': (255,255,255),
		'black': (0,0,0),
		'blue': (0,0,255),
		'red': (255,0,0),
		'green': (0,128,0)}

LINES = {1:(46,90),
		2:(103,147),
		3:(160,204),
		4:(217,261),
		5:(274,318),
		6:(331,375),
		7:(388,432),
		8:(445,489),
		9:(502,546),
		10:(559,603),
		11:(616,660),
		12:(673,717)}
