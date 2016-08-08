from PyQt4 import QtGui as gui, QtCore as core
import PyQt4 as qt
import labrad.units as units

from components.excluded_settings import getExcludedSettings

print(getExcludedSettings())

def get_color(pieces):
	s = ''
	for piece in pieces:
		if len(piece) == 2:
			s += "<font style='color: "+piece[1]+";'>"+piece[0]+"</font>"
		else:s += piece[0]
	return s

def input_partition(input_string):
	"""
	 Returns the list of inpuits from Labrad
	"""
	input_string=input_string.replace('(','')   # remove parenthesese
	input_string=input_string.replace(')','')   # surrounding terms
	input_string=input_string.replace(',','\n') # replace commas with line breaks
	input_string=input_string.replace(' ','')   # remove spaces
	inputs = input_string.splitlines()          # split at lines, which were commas

	input_sep = [] # separated inputs
	for inp in inputs:
		unit = inp.partition('{')[0]      # separate units (they come before {name}
		name = inp.partition('{')[2][:-1] # extract name from {name}
		input_sep.append([name,unit])     # add entry: [name, unit]

	return input_sep # return the separated inputs

def bool_(val):
	if val in ['False','false','F','f']:return False
	return bool(val)

def get_type(lt):
	if type(lt)==type([]):lt=lt[0]
	if lt.startswith('v'):return float
	if lt.startswith('w'):return int
	if lt.startswith('i'):return int
	if lt.startswith('s'):return str
	if lt.startswith('b'):return bool_
	else:return str

def get_entries(setting):
	accepts = [entry for entry in setting.accepts if not ':' in entry] # exclude defaults
	if len(accepts) == 0:return False # accepts nothing -> automatically not sweepable
	accepts = [input_partition(line) for line in accepts]
	entries = []
	for pos in range(len(accepts[0])):
		name = accepts[0][pos][0]
		types = []
		for option in accepts:
			if option[pos][1] not in types:types.append(option[pos][1])
		entries.append([name,types])
	last = setting.accepts[-1]
	if 'defaults' in last:
		defaults = last.partition('defaults')[2][2:][:-1].replace(', ','\n').splitlines()
		for default in defaults:
			parts = default.partition('=')
			name = parts[0]
			value = parts[2]
			if len(entries)==1:
				if value == 'None':entries[0].append(None)
				else:entries[0].append(get_type(entries[0][1])(value))
			else:
				for entry in entries:
					if entry[0]==name:
						if value=='None':entry.append(None)
						else:entry.append(get_type(entry[1])(value))
	return entries
	

def doNothing(self):
	pass

def get_is_sweepable(setting):
	# Exclude settings defined in excluded_settings.py
	if setting.name in getExcludedSettings():return False

	entries = get_entries(setting)
	if not entries:return False
	
	# An entry is sweepable if any of its possible unit types start with 'v' (are float-like.)
	# If the function is not sweepable, this returns False.
	# If it is, it returns <entries>
	is_sweepable = any(
		[ any([unit.startswith('v') for unit in entry[1]]) for entry in entries]
		)
	if is_sweepable:return entries
	else:return False
	
		
def get_is_recordable(setting):
	# Exclude settings defined in excluded_settings.py
	if setting.name in getExcludedSettings():return False

	entries = get_entries(setting)
	if not entries:entries = [] # (zero entries) can still be valid.

	returns = setting.returns

	# An entry is recordable if at least one of the possible returns is an integer-like or float-like.
	is_recordable = any([unit in ['i','w'] or unit.startswith('v') for unit in returns])
	return is_recordable
		
def plist(l,delimeter=', '):
	s = ''
	for entry in l:
		s += str(entry) + delimeter
	if len(s) and len(delimeter):
		s = s[:-len(delimeter)]
	return s




global nobound;nobound = [-float("INFINITY"),float("INFINITY")]
from widgets import selector, simpleText, floatInput, intInput, queryButton, simpleList, checkBox, textInput, rotText
from excluded_servers import excluded_servers


class settingInputWidget(gui.QWidget):
	def __init__(self,parent,pos,inputs,sweeping=True,ls=23,lu=96,ln=128,lv=64):
		super(settingInputWidget,self).__init__(parent)
		self.parent = parent
		self.ls=ls # line spacing
		self.l_units = lu # length of "units" label
		self.l_name  = ln # length of "name" label
		self.l_value = lv # length of "value" input

		self.inputs = inputs # list of [ [name, units], [name, units], ... ]

		self.co = [6,6] # checkbox offset (to center it)

		self.sweeping = sweeping # whether or not this is a selector for a swept setting
		self.move(pos[0],pos[1])
		self.resize(self.ls + self.l_units + self.l_name + self.l_value, self.ls * (1+len(inputs)))
		self.size = [self.ls + self.l_units + self.l_name + self.l_value, self.ls * (1+len(inputs))]
		self.setMinimumSize(self.ls + self.l_units + self.l_name + self.l_value, self.ls * (1+len(inputs)))

		self.doUI()

	def doUI(self):
		self.label_units = simpleText(self,"Units",[self.ls, 0, self.l_units, self.ls])
		self.label_name  = simpleText(self,"Name", [self.ls + self.l_units, 0, self.l_name, self.ls])
		self.label_value = simpleText(self,"Value",[self.ls + self.l_units + self.l_name, 0, self.l_value, self.ls])

		self.check_boxes  = [] # list of checkboxes. Greyed out for non-floatlike inputs
		self.labels_units = [] # list of unit labels
		self.labels_names = [] # list of name labels
		self.inp_values   = [] # list of value inputs

		if self.sweeping:
			self.cb_group = gui.QButtonGroup(self)
			self.cb_group.setExclusive(True)
			first_floatlike = True # The first float-like input found wills start checked.
		num = 0
		for inp in self.inputs:
			lu_ = simpleText(self,plist(inp[1]),[self.ls,self.ls*(1+num),self.l_units,self.ls])
			ln_ = simpleText(self,inp[0],[self.ls+self.l_units,self.ls*(1+num),self.l_name,self.ls])
			self.labels_units.append(lu_)
			self.labels_names.append(ln_)

			# input bar. Type depends on units of input.
			if any([u.startswith('v') for u in inp[1]]): # float-like takes priority
				iv_ = floatInput(self,nobound,4,'',[self.ls+self.l_units+self.l_name,self.ls*(1+num),self.l_value,self.ls])
			elif ('i' in inp[1]) or ('w' in inp[1]): # int-like takes second priority
				iv_ = intInput(self,[-999999,999999],'',[self.ls+self.l_units+self.l_name,self.ls*(1+num),self.l_value,self.ls])
			else: # otherwise, interpret it as a string.
				iv_ = textInput(self,'',[self.ls+self.l_units+self.l_name,self.ls*(1+num),self.l_value,self.ls])
			self.inp_values.append(iv_)

			if self.sweeping:
				cb_ = checkBox(self,"",[0 + self.co[0], self.ls*(1+num) + self.co[1]])
				cb_.stateChanged.connect(self.update_boxes)
				self.cb_group.addButton(cb_)
				self.check_boxes.append(cb_)
				
				if not any([u.startswith('v') for u in inp[1]]): # Checks for absence of any float-like inputs
					cb_.setEnabled(False) # No float-like -> disabled
				else:                                      # If it's float-like
					if first_floatlike:                    # If it's the first floatlike
						cb_.setCheckState(core.Qt.Checked) # It starts checked
						first_floatlike=False              # We have now found a float-like.

			num += 1

	def update_boxes(self):
		if self.sweeping:
			for num in range(len(self.check_boxes)):
				if self.check_boxes[num].isChecked():
					self.inp_values[num].setEnabled(False)
				else:
					self.inp_values[num].setEnabled(True)

	def get_to_sweep(self):
		if self.sweeping:
			for num in range(len(self.check_boxes)):
				if self.check_boxes[num].isChecked():return num
			print("No check box has been checked. This should never happen.")
			raise
		return -1 # -1 means it's not for sweeping; there are no check boxes

	def check_complete(self):
		for num in range(len(self.inputs)):
			if not self.get_to_sweep() == num:
				unit    = get_type(self.inputs[num][1])
				literal = self.inp_values[num].getValue()
				if unit in [int,float]:
					if str(literal) == 'nan':return False
		return True
			





class widgetWarningBox(gui.QWidget):
	def __init__(self,parent,pos,topline="Issues:",status="not ready",entries=[],ls=23,bl=384,el=6):
		super(widgetWarningBox,self).__init__(parent)
		self.parent = parent
		self.move(pos[0],pos[1])
		self.ls=ls # line spacing
		self.bl=bl # box length
		self.bh=el*ls # box height = entry count * line spacing
		self.entries = entries
		self.topline = topline
		self.status  = status
		self.doUI()
	def doUI(self):
		self.label = simpleText(self,"Status: %s"%self.status,[0,0,self.bl,self.ls])
		self.box   = simpleText(self,"You should not see this",[0,self.ls,self.bl,self.bh])
		self.update_contents()

	def update_contents(self):
		text = self.topline
		for issue in self.entries:
			text += "\n> %s"%issue
		self.box.setText(text)

	def add_issue(self,issue):
		if not (issue in self.entries):
			self.entries.append(issue)
			self.update_contents()

	def remove_issue(self,issue):
		if issue in self.entries:
			self.entries.remove(issue)
			self.update_contents()

	def set_issue(self,issue,is_active):
		if is_active:
			self.add_issue(issue)
		else:
			self.remove_issue(issue)

	def update_status(self,status):
		self.label.setText("Status: %s"%status)
		self.status = status

global globalID; globalID = 0

class settingInfo(object): # just a holder class for the data associated with a setting
	def __init__(self,server,device,setting,inputs,status,is_good,name=None,unit='unitless'):
		self.server  = server  # 
		self.device  = device  # 
		self.setting = setting #
		self.inputs  = inputs  # what inputs to pass when recorded. These get saved as parameters/comments
		self.status  = status  # 
		self.is_good = is_good #
		self.unit    = unit
		if name == None:
			self.name    = setting # this can be changed for a custom logging name
		else:
			self.name = name
		self.setID()
	def setID(self):
		global globalID
		self.ID = globalID
		globalID += 1
	def copy(self):
		return settingInfo(
			str(  self.server ),
			str(  self.device ),
			str(  self.setting),
			list( self.inputs ),
			str(  self.status ),
			bool( self.is_good),
			str(  self.name   ),
			str(  self.unit   ),
			)
			
		

class widgetSweepMonitor(gui.QWidget):
	def __init__(self,parent,pos,kind,ls=23,bl=100,pl=208):
		super(widgetSweepMonitor,self).__init__(parent)
		self.parent = parent
		self.move(pos[0],pos[1])
		self.kind = kind # is it '1d' or '2d' ?
		self.ls=ls # line spacing
		self.bl=bl # button length
		self.pl=pl # progressbar length
		self.doUI()
	def doUI(self):
		self.button_start  = queryButton("Start sweep" ,self,'',[0      , self.ls*0],self.parent.sweep_start )
		self.button_start.setEnabled(False)
	def set_steps(self,steps):
		self.progress_bar.setRange(0,steps+1)
	def set_progress(self,prog):
		self.progress_bar.setValue(prog)

class widgetLoggedSettingDetails(gui.QDialog):
	def __init__(self,parent,entries,which,ls=23,ns=96,il=192):
		super(widgetLoggedSettingDetails,self).__init__(parent)
		self.parent  = parent
		self.entries = entries
		self.which   = which
		self.details = self.parent.setting_details[which]
		self.ns=ns # name spacing
		self.il=il # input length
		self.ls=ls # line spacing
		self.bl=75 # button length
		self.doUI()
	def doUI(self):
		self.setWindowTitle("Logged setting details")
		self.button_accept = queryButton("Accept",self,'',[self.ns+self.il+self.ls,0],self.acc)
		self.label_name = simpleText(self,"name / label:",[0,0,self.ns,self.ls])
		self.input_name = textInput(self,'',[self.ns,0,self.il,self.ls])
		self.input_name.setText(self.details.name)
		
		self.setting_input = settingInputWidget(self,[-self.ls,self.ls],self.entries,False)
		self.resize(self.ns+self.il+self.ls+self.bl,self.ls+self.setting_input.size[1])

		for num in range(len(self.details.inputs)):
			if self.details.inputs[num] != None:
				self.setting_input.inp_values[num].setText(str(self.details.inputs[num]))
		
		self.setModal(True)
		self.show()
	def acc(self):
		"""
			Called when the "accept" button is pressed.
			Accepts and performs changes to logged setting.
		"""
		name = str(self.input_name.getValue())
		if name != "":self.parent.setting_details[self.which].name = name

		for num in range(len(self.details.inputs)):
			value = self.setting_input.inp_values[num].getValue()#;print(value,type(value))
			if (str(value) == 'nan') and (type(value) == float):
				value = None # avoid unset numbers (empty strings OK) by setting them to None
				#print("None'd")
			if value == None:self.parent.setting_details[self.which].inputs[num] = None
			else            :self.parent.setting_details[self.which].inputs[num] = get_type(self.entries[num][1])(value)
			#print(num,value,type(value),'\n')
		#print self.parent.setting_details[self.which].inputs
		if len(self.entries) == 0:
			suffix  = "READY     : No inputs required"
			is_good = True
		elif not any([inp == None for inp in self.parent.setting_details[self.which].inputs]):
			suffix  = "READY     : All inputs are set"
			is_good = True
		else:
			suffix  = "NOT READY : Inputs required"
			is_good = False
		self.parent.setting_details[self.which].is_good = is_good
		self.parent.list_to_be_logged.items[self.which] = self.parent.list_to_be_logged.items[self.which][:self.parent.sl] + suffix
		self.parent.list_to_be_logged.change_items(self.parent.list_to_be_logged.items)
		self.accept()

class widgetLoggedSelector(gui.QWidget):
	def __init__(self,parent,pos,data,cs=208,ls=23,sh=96):
		super(widgetLoggedSelector,self).__init__(parent)
		self.parent = parent
		self.move(pos[0],pos[1])
		self.data = data
		self.cs=cs # column spacing
		self.ls=ls # line spacing
		self.sh=sh # selector height
		
		self.ll=123 # logbox length, in characters
		self.sl=83  # setting length, in characters. After this point the status begins.
		
		self.doUI()
	def doUI(self):
		self.label_main    = simpleText(self,"logged settings",[0        , 0      , self.cs, self.ls])
		self.label_server  = simpleText(self,"Server"         ,[0        , self.ls, self.cs, self.ls])
		self.label_device  = simpleText(self,"Device"         ,[self.cs  , self.ls, self.cs, self.ls])
		self.label_setting = simpleText(self,"Setting"        ,[self.cs*2, self.ls, self.cs, self.ls])
		self.selector_logged    = selector(self               ,[0        , self.ls*2],self.sh,self.cs,self.data)   # selector
		self.button_add_setting = queryButton("Add setting",self,"",[self.cs*3,self.ls+self.sh],self.add_setting)

		self.label_to_be_logged = simpleText(self,"To be logged (double click a setting to edit details)",[0,self.sh+self.ls*3,self.cs*2,self.ls])
		self.list_to_be_logged  = simpleList(self,[0,self.sh+self.ls*4,self.cs*3,self.sh],[])
		self.list_to_be_logged.setFont(gui.QFont("Lucida Console",7))
		self.label_status = simpleText(self,"Status",[self.cs*2,self.sh+self.ls*3,self.cs,self.ls])
		self.list_to_be_logged.itemDoubleClicked.connect(self.choose_logged_details)

		self.setting_details = [] # gets populated with settingInfo objects

		self.button_remove_selected = queryButton("Remove selected",self,"",[self.cs*3,self.sh+self.ls*4],self.remove_selected)
		self.button_clear_settings  = queryButton("Clear",self,"",[self.cs*3,self.sh*2+self.ls*3],self.clear_settings)

	def choose_logged_details(self):
		connection = self.parent.parent.parent.connection()
		which  = self.list_to_be_logged.currentRow()
		inputs = get_entries(connection[self.setting_details[which].server].settings[self.setting_details[which].setting])
		go = widgetLoggedSettingDetails(self,inputs,which)
		self.parent.check_warnings()

	def add_setting(self):
		selected_server  = self.selector_logged.get_selection(0)
		selected_device  = self.selector_logged.get_selection(1)
		selected_setting = self.selector_logged.get_selection(2)
		is_valid = self.parent.validate_setting([selected_server,selected_device,selected_setting])
		if is_valid:
			setting = "%s//%s//%s"%(selected_server,selected_device,selected_setting)
			if not (setting in self.list_to_be_logged.items):
				
				entries = get_entries(self.parent.parent.parent.connection.servers[selected_server].settings[selected_setting])
				inputs  = [None if len(entry)==2 else entry[2] for entry in entries]
				is_good = all([inp!=None for inp in inputs])
				if not is_good:
					status = "NOT READY - Inputs required"
				else:
					if len(inputs) == 0:status = "Ready     - No inputs required"
					else:status = "Ready     - All inputs have defaults"

				setting_string = setting + ' '*max(1,self.sl-len(setting)) + status
				self.list_to_be_logged.add_item(setting_string)
				
				self.setting_details.append(settingInfo(
					selected_server,
					selected_device,
					selected_setting,
					inputs,
					status,
					is_good,
					unit=None, # starts out undefined. (None != unitless)
					))
					
			
		else:
			rep = gui.QErrorMessage(self)
			rep.showMessage("The setting you have selected is incomplete or invalid. Changing selections too fast (or clicking and dragging across selections) can fail to update the contents of lists to the right of the one selected.")
		self.parent.check_warnings()

	def remove_selected(self):
		#item = self.list_to_be_logged.get_selected()
		row  = self.list_to_be_logged.currentRow()
		#print(item,row)
		if row >= 0:
			self.list_to_be_logged.items.pop(row)
			self.list_to_be_logged.change_items(self.list_to_be_logged.items)
			self.setting_details.pop(row)
			self.parent.check_warnings()
##        if item in self.list_to_be_logged.items:
##            self.setting_details.pop(self.list_to_be_logged.items.index(item))
##        self.list_to_be_logged.remove_item(item)
##        self.parent.check_warnings()
	def clear_settings(self):
		self.setting_details = []
		self.list_to_be_logged.change_items([])
		self.parent.check_warnings()

class widgetSweptSelector(gui.QWidget):
	def __init__(self,parent,pos,data,label="Swept setting",set_type=None,cs=208,ls=23,sh=96,ll=38,il=64,do_cat_labels=True,label_color=None):
		super(widgetSweptSelector,self).__init__(parent)
		self.parent = parent
		self.data   = data
		self.label  = label
		self.do_cat_labels = do_cat_labels
		self.label_color = label_color
		self.set_type = set_type # what type of setting this is for; None = 1D, 'fast' / 'slow' for 2D
		self.cs = cs # column spacing
		self.ls = ls # line spacing
		self.sh = sh # selector height
		self.ll = ll # label length
		self.il = il # input length
		self.move(pos[0],pos[1])

		self.is_setting_selected = False
		self.setting_selected    = None
		self.row                 = -1

		self.doUI()
	def doUI(self):
		self.label_main     = simpleText(self,self.label,[self.cs*3,0,self.il+self.ll,self.ls])
		if self.do_cat_labels:
			self.label_server   = simpleText(self,"Server" ,[0,0,self.cs,self.ls],color=self.label_color)
			self.label_device   = simpleText(self,"Device" ,[self.cs,0,self.cs,self.ls],color=self.label_color)
			self.label_setting  = simpleText(self,"Setting",[self.cs*2,0,self.cs,self.ls],color=self.label_color)
			
		self.selector_swept = selector(  self,[0,self.ls*1],self.sh,self.cs,self.data)
		
		self.label_start  = simpleText(self,"Start"  ,[self.cs*3,self.ls*1,self.ll+2,self.ls])
		self.label_stop   = simpleText(self,"Stop"   ,[self.cs*3,self.ls*2,self.ll+2,self.ls])
		self.label_points = simpleText(self,"Points" ,[self.cs*3,self.ls*3,self.ll+2,self.ls])
		self.label_delay  = simpleText(self,"Delay"  ,[self.cs*3,self.ls*4,self.ll+2,self.ls])
		self.input_start  = floatInput(self,nobound  ,4,None,[self.cs*3+self.ll,self.ls*1,self.il,self.ls])
		self.input_stop   = floatInput(self,nobound  ,4,None,[self.cs*3+self.ll,self.ls*2,self.il,self.ls])
		self.input_points = intInput( self,[1,999999]  ,None,[self.cs*3+self.ll,self.ls*3,self.il,self.ls])
		self.input_delay  = floatInput(self,nobound  ,4,None,[self.cs*3+self.ll,self.ls*4,self.il,self.ls])

		# custom name
		self.input_custom_name = textInput(self,"",[self.cs*3+self.il+self.ll+self.ls,0,self.il+self.ll*2,self.ls])
		self.input_custom_name.setPlaceholderText("Custom name")

		# ramp rate
		self.limit_ramp_rate = checkBox(self,"limit ramp rate",[self.cs*3 + self.il+self.ll + self.ls,self.ls*1])
		self.label_limit     = simpleText(self,"limit",[self.cs*3+self.il+self.ll+self.ls,self.ls*2,self.ll,self.ls])
		self.ramp_rate_limit = floatInput(self,[0,999999],4,"Limits the rate of change (in absolute value.)\nUnits are <units of setting> per second",[self.cs*3+self.il+self.ll*2+self.ls,self.ls*2,self.il,self.ls])
		self.label_error_box = simpleText(self,"status: no limit",[self.cs*3+self.il+self.ll+self.ls,self.ls*3,(self.ll*2+self.il),self.ls])
		self.label_sweep_rate= simpleText(self,"Sweep rate: nan",[self.cs*3+self.il+self.ll+self.ls,self.ls*4,(self.ll*2+self.il),self.ls])

		self.limit_ramp_rate.stateChanged.connect(self.check_ramp_rate)
		self.ramp_rate_limit.editingFinished.connect(self.check_ramp_rate)
		self.input_start.editingFinished.connect(self.check_ramp_rate)
		self.input_stop.editingFinished.connect(self.check_ramp_rate)
		self.input_points.editingFinished.connect(self.check_ramp_rate)
		self.input_delay.editingFinished.connect(self.check_ramp_rate)

		# setting input widget
		self.setting_input = None
		self.setting_input_pos = [self.cs*3 + self.il + self.ll + self.ls + self.ll*2 + self.il + self.ls,0]


	def check_control_complete(self):
		start = self.input_start.getValue()
		stop  = self.input_stop.getValue()
		steps = self.input_points.getValue() - 1
		delay = self.input_delay.getValue()
		return all([str(val) != 'nan' for val in [start,stop,steps,delay]])

	def check_ramp_rate(self,call_check_warnings = True):
		if call_check_warnings:
			self.parent.check_warnings()
			return
		
		start = self.input_start.getValue()
		stop  = self.input_stop.getValue()
		steps = self.input_points.getValue() - 1
		delay = self.input_delay.getValue()

		# check for invalid step count
		if self.set_type == None:
			if steps < 1:
				self.parent.warning_box.set_issue("Point count is invalid: it must be at least 2",True)
				return False
			self.parent.warning_box.set_issue("Point count is invalid: it must be at least 2",False)
		else:
			if steps<1:
				self.parent.warning_box.set_issue("Point cound for %s setting is invalid: it must be at least 2"%self.set_type,True)
				return False
			self.parent.warning_box.set_issue("Point cound for %s setting is invalid: it must be at least 2"%self.set_type,False)
			
		try:
			natrate = 1000.0*(((stop-start)/(steps))/delay)
		except:
			natrate = float("infinity")
		maxrate = self.ramp_rate_limit.getValue()
		self.label_sweep_rate.clear();self.label_sweep_rate.insertPlainText("Sweep rate: %s"%str(round(natrate,4)))
		if not self.limit_ramp_rate.isChecked():
			self.label_error_box.setToolTip("Ramp rate limit is not currently enforced.")
			self.label_error_box.clear();self.label_error_box.insertPlainText("status: no limit")
			return False
		if (str(natrate)=='nan') or (str(maxrate)=='nan'):
			self.label_error_box.setToolTip("Invalid or incomplete settings for this parameter")
			self.label_error_box.clear();self.label_error_box.insertPlainText("status: incomplete")
			return False
		if natrate > maxrate:
			self.label_error_box.setToolTip("The rate that would be achieved by the current settings\n(start,stop,points,delay) exceeds the enterred rate limit.")
			self.label_error_box.clear();self.label_error_box.insertPlainText("Warning: rate too high")
			return True
		self.label_error_box.setToolTip("Rate is OK. (rate limit exceeds sweep rate)")
		self.label_error_box.clear();self.label_error_box.insertPlainText("Rate OK.")
		return False

	def get_selected_setting(self):
		return [self.selector_swept.get_selection(n) for n in [0,1,2]]

	def update_setting_input(self):
		row = self.selector_swept.lists[2].currentRow()

		if row != self.row:

			if row == -1: # no setting selected
				if self.is_setting_selected:
					self.is_setting_selected = False # setting is no longer selected
					self.setting_selected    = None  # No setting is selected

					self.setting_input.setVisible(False) # this block destroys the old widget
					self.setting_input.setParent(None)
					self.setting_input.destroy()
					del self.setting_input
					self.setting_input=None

			else:
				if self.is_setting_selected:
					self.setting_input.setVisible(False) # this block destroys the old widget
					self.setting_input.setParent(None)
					self.setting_input.destroy()
					del self.setting_input
					self.setting_input = None

				selections = self.selector_swept.get_selections()
				setting    = self.parent.parent.parent.connection.servers[selections[0]].settings[selections[2]]
				self.setting_selected = setting
				self.is_setting_selected = True

				entries = get_entries(setting)
				self.setting_input = settingInputWidget(self,[0,0],entries)
				self.resize(self.setting_input_pos[0] + self.setting_input.size[0],self.ls+self.sh)
				self.setting_input.setParent(self)
				self.setting_input.setVisible(True)
				self.setting_input.move(self.setting_input_pos[0],self.setting_input_pos[1])

			self.row = row
			self.input_custom_name.setText("")
				
class dvSaveOptionsWidget(gui.QWidget):
	def __init__(self,parent,pos,ls=23,loc_width=192,name_width=64):
		super(dvSaveOptionsWidget,self).__init__(parent)
		self.parent=parent
		self.pos=pos
		self.ls=ls
		self.lw=loc_width
		self.nw=name_width
		self.doUI()

	def doUI(self):
		self.input_location = textInput(self,"location for data vault file in data vault directory",[0,0,self.lw,self.ls],"File location")
		self.input_name     = textInput(self,"file name for data vault file"                       ,[self.lw,0,self.nw,self.ls],"File name")
		self.cb_autosave    = checkBox(self, "Save data while recording",[0,self.ls])
		self.input_location.setText("\\data\\")
		self.cb_autosave.setChecked(True)
		self.move(self.pos[0],self.pos[1])
		self.resize(self.lw+self.nw,self.ls*2)
			

class sweep1D(gui.QWidget):
	def __init__(self,parent,cs=208,ls=23,sh=96,ll=38,il=64):
		super(sweep1D,self).__init__(parent)
		self.parent = parent
		self.cs=cs # column spacing (width of column)
		self.ls=ls # line spacing (height of line)
		self.sh=sh # selector height
		self.il=il
		self.ll=ll
		self.doUI()
		self.check_warnings()

	def doUI(self):
		inf = float("INFINITY")

		# swept setting selector
		self.swept_settings = widgetSweptSelector(self,[0,0],self.parent.contents_sweepable,label_color=[232,232,232])

		# recorded settings selector
		self.recorded_settings = widgetLoggedSelector(self,[0,self.sh + self.ls*2],self.parent.contents_recordable)

		# location for dv thing
		# [self.cs*3+self.il+self.ll+self.ls,self.ls*3+self.sh]
		self.dv_options = dvSaveOptionsWidget(self,[self.cs*3+self.il+self.ll+self.ls,self.ls*3+self.sh])

		# sweep controller
		self.sweep_monitor = widgetSweepMonitor(self,[self.cs*3+self.il+self.ll+self.ls,self.ls*6+self.sh],'1d')

		# warning box
		en = list([])[:]
		self.warning_box = widgetWarningBox(self,[self.cs*3+self.il+self.ll+self.ls,self.ls*7+self.sh],entries = en)

	def sweep_start(self):
		self.parent.parent.sweep_start('1d')
##    def sweep_cancel(self):
##        self.parent.parent.sweep_cancel('1d')
##    def sweep_pause(self):
##        self.parent.parent.sweep_pause('1d')
##    def sweep_resume(self):
##        self.parent.parent.sweep_resume('1d')

	def check_warnings(self):
		# Has a setting been selected to sweep?
		has_swept_been_selected = not (None in self.swept_settings.selector_swept.get_selections())
		self.warning_box.set_issue("No setting has been selected for sweeping",not has_swept_been_selected)

		# Is selected setting valid?
		is_valid = self.validate_setting(self.swept_settings.selector_swept.get_selections())
		if not has_swept_been_selected:is_valid = True # no_selection is valid.
		self.warning_box.set_issue("Invalid setting selected for swept parameter",not is_valid)

		# Sweep controls complete?
		self.warning_box.set_issue("Controls for swept setting (start/stop/step/delay) are incomplete",not self.swept_settings.check_control_complete())

		# Ramp rate is limited, but no rate has been set
		ramp_rate_is_on  = self.swept_settings.limit_ramp_rate.isChecked()
		ramp_rate_is_set = not (str(self.swept_settings.ramp_rate_limit.getValue())=='nan')
		self.warning_box.set_issue("Ramp rate is on, but has not been set",ramp_rate_is_on and not ramp_rate_is_set)

		# sweep rate exceeds ramp rate
		sweep_too_fast = self.swept_settings.check_ramp_rate(call_check_warnings = False)
		self.warning_box.set_issue("Sweep rate is faster than maximum ramp rate",sweep_too_fast)

		# no settings added to record
		no_settings_to_log = len(self.recorded_settings.list_to_be_logged.items)==0
		self.warning_box.set_issue("No setting(s) have been selected to record",no_settings_to_log)

		# incomplete inputs for logged setting(s)
		inp_req = False
		for set_detail in self.recorded_settings.setting_details:
			if not set_detail.is_good:inp_req = True
		self.warning_box.set_issue("Logged setting(s) missing required input field(s)",inp_req)

		# incomplete inputs for swept setting
		inp_req_swept = False
		if self.swept_settings.setting_input != None:
			incomplete = not self.swept_settings.setting_input.check_complete()
			self.warning_box.set_issue("Swept setting is missing input(s)",incomplete)
			

		# update status
		no_warnings = len(self.warning_box.entries)==0
		if no_warnings:
			self.warning_box.update_status("ready")
			self.sweep_monitor.button_start.setEnabled(True)
		else:
			self.warning_box.update_status("not ready")
			self.sweep_monitor.button_start.setEnabled(False)
		
	def validate_setting(self,setting):
		# setting should be list [server,device,setting]
		if not (setting[0] in str(self.parent.parent.connection.servers).splitlines()):
			return False
		if not (setting[1] in [c[1] for c in self.parent.parent.connection.servers[setting[0]].list_devices()]):
			return False
		if not (setting[2] in str(self.parent.parent.connection.servers[setting[0]].settings).splitlines()):
			return False
		return True

	def update_setting_input(self):
		self.swept_settings.update_setting_input()

		


class sweep2D(gui.QWidget):
	def __init__(self,parent,cs=208,ls=23,sh=96,ll=38,il=64):
		super(sweep2D,self).__init__(parent)
		self.parent = parent
		self.cs=cs # column spacing (width of column)
		self.ls=ls # line spacing (height of line)
		self.sh=sh # selector height
		self.il=il
		self.ll=ll
		self.doUI()

	def doUI(self):
		inf = float("INFINITY")
		
		# swept settings selector(s)
		self.sweep_fast = widgetSweptSelector(self,[0,0]              ,self.parent.contents_sweepable,label="Fast sweep",label_color=[232,232,232],set_type='fast')
		self.sweep_slow = widgetSweptSelector(self,[0,self.ls+self.sh],self.parent.contents_sweepable,label="Slow sweep",label_color=[232,232,232],set_type='slow')
		
		# logged settings
		self.recorded_settings = widgetLoggedSelector(self,[0,self.ls*2 + self.sh*2],self.parent.contents_recordable)

		# location for dv thing
		# [self.cs*3+self.il+self.ll+self.ls,self.ls*3+self.sh*2]
		self.dv_options=dvSaveOptionsWidget(self,[self.cs*3+self.il+self.ll+self.ls,self.ls*3+self.sh*2])

		# sweep controller
		self.sweep_monitor = widgetSweepMonitor(self,[self.cs*3+self.il+self.ll+self.ls,self.ls*6+self.sh*2],'2d')

		# warning box
		en = list([])[:]
		self.warning_box = widgetWarningBox(self,[self.cs*3+self.il+self.ll+self.ls,self.ls*7+self.sh*2],entries = en)

	def sweep_start(self):
		self.parent.parent.sweep_start('2d')
##    def sweep_cancel(self):
##        self.parent.parent.sweep_cancel('2d')
##    def sweep_pause(self):
##        self.parent.parent.sweep_pause('2d')
##    def sweep_resume(self):
##        self.parent.parent.sweep_resume('2d')

	def check_warnings(self):

		########################
		## Fast swept setting ##
		########################
		# Has a setting been selected to sweep?
		fast_selected = not (None in self.sweep_fast.selector_swept.get_selections())
		self.warning_box.set_issue("No setting selected for fast swept setting",not fast_selected)
		# Is selected setting valid?
		is_fast_valid = self.validate_setting(self.sweep_fast.selector_swept.get_selections())
		if not fast_selected:is_fast_valid = True # no_selection is valid.
		self.warning_box.set_issue("Invalid setting selected for fast swept parameter",not is_fast_valid)
		# Sweep controls complete?
		self.warning_box.set_issue("Controls for fast swept setting (start/stop/step/delay) are incomplete",not self.sweep_fast.check_control_complete())
		# Ramp rate is limited, but no rate has been set
		fast_ramp_rate_is_on  = self.sweep_fast.limit_ramp_rate.isChecked()
		fast_ramp_rate_is_set = not (str(self.sweep_fast.ramp_rate_limit.getValue())=='nan')
		self.warning_box.set_issue("Ramp rate is on for fast swept setting, but has not been set",fast_ramp_rate_is_on and not fast_ramp_rate_is_set)
		# sweep rate exceeds ramp rate
		fast_sweep_too_fast = self.sweep_fast.check_ramp_rate(call_check_warnings = False)
		self.warning_box.set_issue("Sweep rate for fast swept setting is faster than maximum ramp rate",fast_sweep_too_fast)
		
		########################
		## slow swept setting ##
		########################
		# Has a setting been selected to sweep?
		slow_selected = not (None in self.sweep_slow.selector_swept.get_selections())
		self.warning_box.set_issue("No setting selected for slow swept setting",not slow_selected)
		# Is selected setting valid?
		is_slow_valid = self.validate_setting(self.sweep_slow.selector_swept.get_selections())
		if not slow_selected:is_slow_valid = True # no_selection is valid.
		self.warning_box.set_issue("Invalid setting selected for slow swept parameter",not is_slow_valid)
		# Sweep controls complete?
		self.warning_box.set_issue("Controls for slow swept setting (start/stop/step/delay) are incomplete",not self.sweep_slow.check_control_complete())
		# Ramp rate is limited, but no rate has been set
		slow_ramp_rate_is_on  = self.sweep_slow.limit_ramp_rate.isChecked()
		slow_ramp_rate_is_set = not (str(self.sweep_slow.ramp_rate_limit.getValue())=='nan')
		self.warning_box.set_issue("Ramp rate is on for slow swept setting, but has not been set",slow_ramp_rate_is_on and not slow_ramp_rate_is_set)
		# sweep rate exceeds ramp rate
		slow_sweep_too_slow = self.sweep_slow.check_ramp_rate(call_check_warnings = False)
		self.warning_box.set_issue("Sweep rate for slow swept setting is slower than maximum ramp rate",slow_sweep_too_slow)

		# no settings added to record
		no_settings_to_log = len(self.recorded_settings.list_to_be_logged.items)==0
		self.warning_box.set_issue("No setting(s) have been selected to record",no_settings_to_log)

		# incomplete inputs for logged setting(s)
		inp_req = False
		for set_detail in self.recorded_settings.setting_details:
			if not set_detail.is_good:inp_req = True
		self.warning_box.set_issue("Logged setting(s) missing required input field(s)",inp_req)

		# update status
		no_warnings = len(self.warning_box.entries)==0
		if no_warnings:
			self.warning_box.update_status("ready")
			self.sweep_monitor.button_start.setEnabled(True)
		else:
			self.warning_box.update_status("not ready")
			self.sweep_monitor.button_start.setEnabled(False)

	def validate_setting(self,setting):
		# setting should be list [server,device,setting]
		if not (setting[0] in str(self.parent.parent.connection.servers).splitlines()):
			return False
		if not (setting[1] in [c[1] for c in self.parent.parent.connection.servers[setting[0]].list_devices()]):
			return False
		if not (setting[2] in str(self.parent.parent.connection.servers[setting[0]].settings).splitlines()):
			return False
		return True

	def update_setting_input(self):
		self.sweep_fast.update_setting_input()
		self.sweep_slow.update_setting_input()
	

class sweeperWidget(gui.QMainWindow):
	def __init__(self,parent,test_mode=False):
		super(sweeperWidget,self).__init__()
		self.parent = parent
		self.test_mode = test_mode

		self.timer = core.QTimer(self)
		self.timer.setInterval(25)
		self.timer.timeout.connect(self.timer_event)

		self.doUI()
		self.timer.start()

	def timer_event(self):
		self.s1d.update_setting_input()
		self.s2d.update_setting_input()

	def doUI(self):
		
		self.setMinimumSize(64,64)
		gui.QToolTip.setFont(gui.QFont('lucida console',8))

		servers = str(self.parent.connection.servers).splitlines() # get a list of detected servers

		self.contents_sweepable  = {} # settings that are valid for sweeping
		self.contents_recordable = {} # settings that are valid for recording
		self.contents = {}            # all settings (in contents form)

##        # Servers that aren't devic servers.
##        excluded_servers = [
##            'gpib_device_manager',
##            'majorana_gpib_bus',
##            'majorana_serial_server',
##            'manager',
##            'registry',
##            'data_vault',
##            ]

		active_servers = []

		for server in str(self.parent.connection.servers).splitlines():
			if server not in excluded_servers:
				
				try:
					settings = self.parent.connection.servers[server].settings
					devices  = [dev[1] for dev in self.parent.connection.servers[server].list_devices()]

					if len(devices) == 0: # skip deviceless servers
						print("Device server {server} has no active devices, and will be ignored".format(server=server))
						continue

					self.contents.update([[
						server,{dev:str(settings).splitlines() for dev in devices}
						]])
					self.contents_sweepable.update([[
						server,{dev:[setting for setting in str(settings).splitlines() if get_is_sweepable(self.parent.connection.servers[server].settings[setting])] for dev in devices}
						]])
					self.contents_recordable.update([[
						server,{dev:[setting for setting in str(settings).splitlines() if get_is_recordable(self.parent.connection.servers[server].settings[setting])] for dev in devices}
						]])
					active_servers.append(server)
				except:
					print("Server {server} is not a functioning device server. It should either be fixed, or added to the excluded_servers list.".format(server=server))

		if len(active_servers) == 0:
			print("Did not find any device servers with active devices. Please make sure that there are valid device servers running (with devices active,) then restart the sweeper.")
			self.found_servers = False
		else:
			print("Found active device servers: {active_servers}".format(active_servers=active_servers))
			self.found_servers = True

		if self.found_servers:
			self.tabs = gui.QTabWidget(self)
			self.setCentralWidget(self.tabs)
			self.s1d=sweep1D(self)
			self.s2d=sweep2D(self)
			self.tabs.addTab(self.s1d,"1-D sweep")
			self.tabs.addTab(self.s2d,"2-D sweep")

		#[!!!!] test label        #[!!!!] rot test
		#self.rl1 = rotText(self,"test #1",[128,128,128,23],0)
		#self.rl2 = rotText(self,"test #2",[128,128,23,128],90)
		#self.rl3 = rotText(self,"test #3",[128,128,23,128],-90)
		#self.tabs.addTab(self.rl1,'r1')
		#self.tabs.addTab(self.rl2,'r2')
		#self.tabs.addTab(self.rl3,'r3')

	def get_details(self,kind='1d'):
		if kind=='1d':
			details = {
				'dv_loc'       : self.s1d.dv_options.input_location.text(),
				'dv_name'      : self.s1d.dv_options.input_name.text(),
				'dv_autosave'  : self.s1d.dv_options.cb_autosave.isChecked(),

				'setting_swept': self.s1d.swept_settings.get_selected_setting(),
				'settings_read': list(self.s1d.recorded_settings.list_to_be_logged.items),
				'start'        : self.s1d.swept_settings.input_start.getValue(),
				'stop'         : self.s1d.swept_settings.input_stop.getValue(),
				'steps'        : self.s1d.swept_settings.input_points.getValue()-1,
				'delay'        : self.s1d.swept_settings.input_delay.getValue(),
				'do_maxrate'   : self.s1d.swept_settings.limit_ramp_rate.isChecked(),
				'maxrate'      : self.s1d.swept_settings.ramp_rate_limit.getValue(),

				'inputs'       : [inp.getValue() for inp in self.s1d.swept_settings.setting_input.inp_values], # User defined value for inputs
				'to_sweep'     : self.s1d.swept_settings.setting_input.get_to_sweep(), # which one should be swept. Corresponding term in 'inputs' is ignored.

				'setting_details': [info.copy() for info in self.s1d.recorded_settings.setting_details],

				'custom_name'  : self.s1d.swept_settings.input_custom_name.getValue(),
				}
			#print(type(details['custom_name']))
		else:
			details = {
				'dv_loc'       : self.s2d.dv_options.input_location.text(),
				'dv_name'      : self.s2d.dv_options.input_name.text(),
				'dv_autosave'  : self.s2d.dv_options.cb_autosave.isChecked(),

				'settings_read':list(self.s2d.recorded_settings.list_to_be_logged.items),
				'fast_swept'   :self.s2d.sweep_fast.get_selected_setting(),
				'slow_swept'   :self.s2d.sweep_slow.get_selected_setting(),
				'xnum'         :self.s2d.sweep_fast.input_points.getValue(),
				'ynum'         :self.s2d.sweep_slow.input_points.getValue(),
				'xsteps'       :self.s2d.sweep_fast.input_points.getValue()-1,
				'ysteps'       :self.s2d.sweep_slow.input_points.getValue()-1,
				'xstart'       :self.s2d.sweep_fast.input_start.getValue(),
				'xstop'        :self.s2d.sweep_fast.input_stop.getValue() ,
				'ystart'       :self.s2d.sweep_slow.input_start.getValue(),
				'ystop'        :self.s2d.sweep_slow.input_stop.getValue() ,
				'xdelay'       :self.s2d.sweep_fast.input_delay.getValue(),
				'ydelay'       :self.s2d.sweep_slow.input_delay.getValue(),
				'x_do_maxrate' :self.s2d.sweep_fast.limit_ramp_rate.isChecked(),
				'y_do_maxrate' :self.s2d.sweep_slow.limit_ramp_rate.isChecked(),
				'x_maxrate'    :self.s2d.sweep_fast.ramp_rate_limit.getValue() ,
				'y_maxrate'    :self.s2d.sweep_slow.ramp_rate_limit.getValue() ,

				'inputs_fast'  :[inp.getValue() for inp in self.s2d.sweep_fast.setting_input.inp_values],
				'inputs_slow'  :[inp.getValue() for inp in self.s2d.sweep_slow.setting_input.inp_values],
				'to_sweep_fast':self.s2d.sweep_fast.setting_input.get_to_sweep(),
				'to_sweep_slow':self.s2d.sweep_slow.setting_input.get_to_sweep(),

				'setting_details': [info.copy() for info in self.s2d.recorded_settings.setting_details],

				'fast_custom_name':self.s2d.sweep_fast.input_custom_name.getValue(),
				'slow_custom_name':self.s2d.sweep_slow.input_custom_name.getValue(),
				
				}
		return details

	def check_warnings(self):
		self.s1d.check_warnings()
		self.s2d.check_warnings()


test = False
if __name__ == '__main__' and test:
	import sys
	app=gui.QApplication(sys.argv)
	i=settingInputWidget(None,[64,64],[
		['voltage',['v','v[V]']],
		['channel',['i']],
		])
	i.show()
	sys.exit(app.exec_())


