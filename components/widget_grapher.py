from PyQt4 import QtGui as gui,QtCore as core
import pyqtgraph as pg
import sys,time,numpy
from numpy import array
from math import e,pi,floor

from widgets              import queryButton,simpleText,checkBox,simpleDropdown,rotText,textInput
from colormaps            import maps
from logger               import dataLogger,datasetDetails
from widget_comment_box   import commentBoxWidget
from widget_parameter_box import parameterBoxWidget


class plotInstance(gui.QWidget):
    def __init__(self,xlabel,ylabel,xrng=None,xdata=[],ydata=[],parent=None,geometry=None):
        super(plotInstance,self).__init__(None)
        self.plot = pg.PlotWidget(parent)
        self.plot.setLabel('bottom',text=xlabel)
        self.plot.setLabel('left',text=ylabel)

        self.plot.setDownsampling(auto=True,mode='peak')
        self.plot.setClipToView(True)

        if not (xrng==None):
            self.plot.setXRange(xrng[0],xrng[1])

        if not (geometry==None):
            self.plot.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])

        self.xdat=xdata
        self.ydat=ydata
        self.data = pg.PlotCurveItem(x=self.xdat,y=self.ydat)
        self.plot.addItem(self.data)
        #self.setCentralWidget(self.plot)
    def add_datum(self,x,y):
        if "_value" in dir(x):x=x._value
        if "_value" in dir(y):y=y._value
        self.xdat = list(self.xdat + [x])
        self.ydat = list(self.ydat + [y])
    def update_plot(self):
        self.plot.clear()
        self.data = pg.PlotCurveItem(x=self.xdat,y=self.ydat)
        self.plot.addItem(self.data)

class colorplotShell(gui.QWidget):
    def __init__(self,xlabel,ylabel,xnum,ynum,xrng,yrng,parent=None,geometry=None,ls=23,pl=320,bl=12,ll=128):
        super(colorplotShell,self).__init__(parent)
        self.parent = parent

        #print('\nXLABEL,YLABEL')
        #print(xlabel,ylabel)

        self.xnum  = xnum
        self.ynum  = ynum
        self.x_ref = numpy.linspace(xrng[0],xrng[1],xnum)
        self.y_ref = numpy.linspace(yrng[0],yrng[1],ynum)

        self.x_min = str(xrng[0])[:6]
        self.x_med = str((xrng[0]+xrng[1])/2.0)[:6]
        self.x_max = str(xrng[1])[:6]
        self.y_min = str(yrng[0])[:6]
        self.y_med = str((yrng[0]+yrng[1])/2.0)[:6]
        self.y_max = str(yrng[1])[:6]

        self.colorplot = colorplotInstance(xlabel,ylabel,xnum,ynum,self,[ls,0,pl,pl])

        self.ls=ls # line spacing
        self.pl=pl # plot sidelength
        self.bl=bl # bar length & spacing
        self.ll=ll # label length
        
        # y labels
        self.label_top    = simpleText(self,self.y_max, [ls+pl, 5                  , ll//2, ls], "Y setting (%s) maximum value (%s)"%(ylabel,self.y_max))
        self.label_mid    = simpleText(self,self.y_med, [ls+pl, int(pl//2 - ls//2) , ll//2, ls], "Y setting (%s) median value (%s)"%(ylabel,self.y_med))
        self.label_bot    = simpleText(self,self.y_min, [ls+pl, pl-(1*ls+3)        , ll//2, ls], "Y setting (%s) minimum value (%s)"%(ylabel,self.y_min))
        self.label_y_axis = simpleText(self,str(ylabel),[ls+pl, pl-(2*ls+3)        , ll, ls]   , "Y setting (what's being swept along the y axis")

        # x labels
        self.label_left   = simpleText(self,self.x_min,  [ls                , pl   , ll//2, ls], "X setting (%s) minimum value (%s)"%(xlabel,self.x_min))
        self.label_center = simpleText(self,self.x_med,  [ls + (pl-ll//2)//2, pl   , ll//2, ls], "X setting (%s) median value (%s)"%(xlabel,self.x_med))
        self.label_right  = simpleText(self,self.x_max,  [ls + (pl-ll//2)   , pl   , ll//2, ls], "X setting (%s) maximum value (%s)"%(xlabel,self.x_max))
        self.label_x_axis = simpleText(self,str(xlabel), [ls                , pl+ls, ll   , ls], "X setting (what's being swept along the x axis")

        # axis labels
        ##self.label_x = rotText(self,str(xlabel),[self.ls+int(self.pl//2 - self.ll//2),self.pl,self.ll,self.ls],rot=0)
        ##self.label_y = rotText(self,str(ylabel),[
        self.label_x = rotText(self,str(xlabel),[self.ls  ,self.pl+8,self.ll,self.ls],  0)
        self.label_y = rotText(self,str(ylabel),[self.ls-8,self.pl  ,self.ls,self.ll],-90)
        self.labeltest = rotText(self,"TEST: 0",[self.ls+self.pl+23,self.bl*3,256,256],90)

        self.setMinimumSize(ls+pl+bl*3+ll,pl+2*ls)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
        

class colorplotInstance(gui.QWidget):
    def __init__(self,xlabel,ylabel,xnum,ynum,parent=None,geometry=None):
        super(colorplotInstance,self).__init__(parent)
        
        self.data    = numpy.zeros([xnum,ynum])
        self.unswept = numpy.ones([xnum,ynum],dtype=bool)

        self.gl = pg.GraphicsLayoutWidget(parent)
        self.gl.setAspectLocked(True)

        self.view = self.gl.addViewBox()
        self.img  = pg.ImageItem(border='w')
        self.view.addItem(self.img)
        self.view.setRange(core.QRectF(0,0,xnum,ynum))
        self.img.setImage(self.data)
        self.first_datum = True # whether or not the next datum added is the first. Used to populate array.
        
        if not geometry==None:
            #self.gl.setParent(parent)
            self.gl.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])

    def add_datum(self,x,y,value):
        if "_value" in dir(value):
            value = value[value.unit]
            
        if self.first_datum:
            self.min_value = value   # initialize minimum value
            self.first_datum = False # No longer on first value
            self.data[x,y]=value     # set the value in the data array
            self.unswept[x,y]=False  # Set the point to already_swept
            
            # Set all other data points to 0.9*value (black)
            self.data[self.unswept] = value - 0.1 * abs(value)
        else:
            self.data[x,y]=value    # value is either number (greyscale) or 1D array of length 3 (r,g,b)
            self.unswept[x,y]=False # set that point to already_swept
            if value < self.min_value: # If there's a new minimum value:
                self.min_value = value # set the new minimum
                self.data[self.unswept] = self.min_value # set all unswept tiles to the minimum

    def update_plot(self,colormap=maps['rb']):
        if colormap==None:
            self.img.setImage(self.data)
        else:
            self.img.setImage(colormap.map(to_unity(self.data),mode='byte'))

def to_unity(data):
    res = data.copy()
    res -= res.min()
    max_ = res.max()
    if max_ != 0:
        res /= max_
    return res
    
def conc_parameter_list(parameter_list):
    '''flattens [name, units, value] to [name (units), value]'''
    newlist = []
    for item in parameter_list:
        newlist.append(["%s (%s)"%(item[0],item[1]),item[2]])
    return newlist

def add_legend(dependents):
    '''duplicates position 0 to position 1 for each entry in the list,
pushing all further data forward'''
    newlist = []
    for item in dependents:
        newlist.append([item[0],item[0]]+item[1:])
    return newlist

class sweepInstance(gui.QMainWindow):
    def __init__(self,parent,details,ID,status,name,kind = '1d',ls=23,gw=384,gh=192,pl=320,bl=12,ll=128):
        super(sweepInstance,self).__init__()
        # info/control bar at top
        self.parent = parent
        self.det    = details
        self.status = status
        self.name   = name
        self.ID     = ID
        self.kind   = kind # '1d' or '2d'

        self.measurements_completed = 0
        self.total_time      = 0.0  # total amount of time spent sweeping.
        self.current_rate    = 0.0  # current sweep rate
        self.finished_time   = None # None = not finished
        self.was_paused      = False# Used to skip paused time when counting average rate

        self.np_swept = 0.0 # amount of setting swept while not paused
        self.np_time  = 0.0 # amount of time passed while not paused

        self.ls=ls # line spacing
        self.gw=gw # graph width
        self.gh=gh # graph height

        self.pl=pl # plot(2d) sidelength
        self.bl=bl # bar (and bar spacing) length
        self.ll=ll # label length
        
        self.setting_details = self.det['setting_details']
        self.colormap   = None
        self.custom_map = None

        # comment, paremeters
        self.comment_list    = []
        self.parameter_list  = []
        self.parameter_names = []
        self.has_written     = False

        # dataset location (None = not set yet)
        self.dataset_location = None

        o = array([0,ls*5]) # origin
        self.graphs = {}
        n = 0
        if self.kind == '1d':
            lbl=[setting.ID for setting in self.setting_details]
        elif self.kind=='2d':
            lbl=[setting.ID for setting in self.setting_details]
        for pos in range(len(lbl)):
            ylabel = self.setting_details[pos].name
            ID     = self.setting_details[pos].ID
            if kind == '1d':
                x = o[0] + (gw+ls) * (n%3)
                xlabel = self.det['custom_name'] if self.det['custom_name'] else self.det['xlabel']
                y = o[1] + (gh+ls) * int(floor(n/3.0)) # rectangular graphs for 1d
                self.graphs.update([[ ID,plotInstance(xlabel,ylabel,None,parent=self,geometry=[x,y,gw,gh]) ]])
                
            elif kind == '2d':
                xname = self.det['fast_custom_name'] if self.det['fast_custom_name'] else self.det['xlabel']
                yname = self.det['slow_custom_name'] if self.det['slow_custom_name'] else self.det['ylabel']
                print(xname,yname)
                x = o[0] + (ls*2+pl+bl*3+ll)*(n%2)
                y = o[1] + (gw+ls) * int(floor(n/2.0)) # square graphs for 2d
                self.graphs.update([[ ID,colorplotShell(
                    xname,
                    yname,
                    self.det['xnum'],
                    self.det['ynum'],
                    [self.det['xstart'],self.det['xstop']],
                    [self.det['ystart'],self.det['ystop']],
                    parent=self,
                    geometry=[x,y,ls+pl+bl*3+ll,pl+ls],
                    ls=ls,pl=pl,bl=bl,ll=ll
                    )
                                      ]])

            n+=1

        if self.kind == '2d':
            self.current_delay = self.det['xdelay']

        # User defined input handling
        if self.kind == '1d':            
            self.inputs   = self.det['inputs']
            self.to_sweep = self.det['to_sweep']
        if self.kind == '2d':
            self.inputs_fast   = self.det['inputs_fast']
            self.to_sweep_fast = self.det['to_sweep_fast']
            self.inputs_slow   = self.det['inputs_slow']
            self.to_sweep_slow = self.det['to_sweep_slow']
            

        self.first_meas = True
        self.doUI()
        self.time = time.time()
        
    def doUI(self):
        # background
        #self.setBackground(gui.QColor('black'))
        
        # use self.det
        if self.kind=='1d':
            self.stepsize = (self.det['stop']-self.det['start'])/(self.det['steps'])
            self.xsetting = self.det['start'] # current value of setting. Starts at beginning.
        elif self.kind=='2d':
            self.x_stepsize = (self.det['xstop']-self.det['xstart'])/(self.det['xsteps'])
            self.y_stepsize = (self.det['ystop']-self.det['ystart'])/(self.det['ysteps'])
            self.x_setting  = self.det['xstart']
            self.y_setting  = self.det['ystart']
            self.x_num = 0
            self.y_num = 0

        # labels / info
        t = self.det['start_timestamp']
        time_text="Sweep started at: %i/%i/%i %i:%i:%i"%(t.tm_mon,t.tm_mday,t.tm_year,t.tm_hour,t.tm_min,t.tm_sec)
        self.label_starttime  = simpleText(self,time_text,[0,0,self.gw//2+74,self.ls])
        self.label_stepsdone  = simpleText(self,"Measurements done: %i"%(self.measurements_completed),[0,self.ls*1,self.gw//2,self.ls])

        if self.kind == '1d':
            self.meas_total = self.det['steps']+1
        elif self.kind == '2d':
            self.meas_total = self.det['xnum']*self.det['ynum']

        self.label_stepstotal = simpleText(self,"Measurements total: %i"%(self.meas_total),[0,self.ls*2,self.gw//2,self.ls])
        self.progress_bar     = gui.QProgressBar(self)
        self.progress_bar.setRange(0,self.meas_total)
        self.progress_bar.setGeometry(0,self.ls*3,self.gw//2,self.ls)

        # sweep control
        self.button_pause  = queryButton("Pause" ,self,'',[self.gw//2,self.ls*1],self.pause )
        self.button_resume = queryButton("Resume",self,'',[self.gw//2,self.ls*2],self.resume)
        self.button_cancel = queryButton("Cancel",self,'',[self.gw//2,self.ls*3],self.cancel)
        self.checkbox_cancel = checkBox(self,"Confirm",   [self.gw//2 + 76, self.ls*3 - 3])

        # 'set graphs to automatic' button
        self.button_graph_auto = queryButton("Reset graph view",self,"",[0,self.ls*4],self.reset_graph_views)

        # completion readout
        self.label_complete_time = simpleText(self,"Completed at:",[self.gw//2+76+self.ls,self.ls*0,self.gw//2,self.ls])
        self.label_complete_rate = simpleText(self,"Average rate:",[self.gw//2+76+self.ls,self.ls*1,self.gw//2,self.ls])
        self.label_current_rate  = simpleText(self,"Current rate:",[self.gw//2+76+self.ls,self.ls*2,self.gw//2,self.ls])

        # data logging (data vault) details
        self.input_logname         = textInput(self,'',[self.gw+76+self.ls*2,0,self.ll,self.ls])
        self.input_logname.setPlaceholderText("Dataset name")
        
        self.button_add_comments   = queryButton("Add comment(s)"  ,self,'',[self.gw+76+self.ls*2,self.ls*1],self.add_comments)
        self.button_add_parameters = queryButton("Add parameter(s)",self,'',[self.gw+76+self.ls*2,self.ls*2],self.add_parameters)
        self.button_log_data       = queryButton("Write data set"  ,self,'',[self.gw+76+self.ls*2,self.ls*3],self.log_data)

        # colormap
        if self.kind == '2d':
            self.label_colormap    = simpleText(self,"Color map:",[self.ll+self.ls+self.gw+76+self.ls*2,0,64,self.ls])
            self.dropdown_colormap = simpleDropdown(self,["None","Custom"]+maps.keys(),[self.ll+self.ls+self.gw+self.ls*2+76+64,0,64,self.ls],self.change_colormap)
            self.button_custommap  = queryButton("Custom",self,'',[self.ll+self.ls+self.gw+76+self.ls*2,self.ls],self.cust_map)
        elif self.kind == '1d':
            self.label_colormap = self.dropdown_colormap = self.button_custommap = None

    def log_data(self):
        # [!!!!] add ability to determine folder
        location = ['','HZS14']

        if self.has_written:
            print("Error: data set has already been written. Note that comments and parameters can still be added.")
            return False

        if not (self.status == 'completed'):
            print("Error: cannot log data until dataset is completed.")
            return False
        dataset_name = self.input_logname.getValue()
        if dataset_name == '':
            print("Error: you must set the name of the data set before creating it.")
            return False

        if self.kind == '1d':
            name = self.det['custom_name'] if self.det['custom_name'] else self.det['xlabel']
            refset = self.graphs[self.graphs.keys()[0]].xdat
            try:
                xunit = str(refset[0].unit)
            except:
                xunit = 'unitless'
            independents = [[name,xunit]]
            print(xunit)
            
            dependents = [[setting.name,setting.unit] for setting in self.setting_details]


			

        if self.kind == '2d':
            # reference sets
            x_refset = self.graphs[self.graphs.keys()[0]].x_ref
            y_refset = self.graphs[self.graphs.keys()[0]].y_ref
            xnum     = self.graphs[self.graphs.keys()[0]].xnum
            ynum     = self.graphs[self.graphs.keys()[0]].ynum
            
            xname = self.det['fast_custom_name'] if self.det['fast_custom_name'] else self.det['xlabel']
            yname = self.det['slow_custom_name'] if self.det['slow_custom_name'] else self.det['ylabel']
            try:
                xunit = str(x_refset[0].unit)
            except:
                xunit = 'unitless'
            try:
                yunit = str(y_refset[0].unit)
            except:
                yunit = 'unitless'
            independents = [[xname,xunit],[yname,yunit]]
            #print(xunit,yunit)
            
            dependents = [[setting.name,setting.unit] for setting in self.setting_details]

            

        dataset_details = datasetDetails(dataset_name,location,independents,dependents)
        global log
        if log.active:
            print("Error: there is an active data set. Please wait until it has finished writing its data.")
            return False


        data = []
        for measurement in range(self.meas_total):
            if self.kind == '1d':
                data.append(
                    [float(refset[measurement])] + [float(self.graphs[det.ID].ydat[measurement]) for det in self.setting_details]
                    )
            if self.kind == '2d':
                x = measurement % xnum
                y = int((measurement - x) // (ynum))
                data.append(
                    [float(x_refset[x]),float(y_refset[y])] + [float(self.graphs[det.ID].colorplot.data[x][y]) for det in self.setting_details]
                    )
        self.dataset_location = location[:]
        
        #print(data)
        
        #print independents + dependents
        self.dsnum = log.make_dataset(dataset_name,location,independents,add_legend(dependents))
        log.dump_data(data)
        if len(self.comment_list):
            log.add_comments(self.comment_list)
            self.comment_list = []
        if len(self.parameter_list):
            log.add_parameters(self.parameter_list)
            self.parameter_list = []
        log.close_dataset()
        self.has_written = True
        
        
        
    def add_comments(self):
        commentbox = commentBoxWidget(self)

    def send_comments(self,comments):
        if not self.has_written:
            self.comment_list += comments
        else:
            global log
            log.add_comments_to_file(self.dataset_location,self.dsnum,comments)
    
    def add_parameters(self):
        parameterbox = parameterBoxWidget(self,self.parameter_names)

    def send_parameters(self,parameters):
        if not self.has_written:
            self.parameter_list += parameters
            self.parameter_names += [param[0] for param in parameters]
        else:
            global log
            log.add_parameters_to_file(self.dataset_location,self.dsnum,parameters)
            self.parameter_names += [param[0] for param in parameters]
            

    def cust_map(self):
        self.dropdown_colormap.setCurrentIndex(1) # Custom
        self.change_colormap()
        go = customMapWidget(self)

    def change_colormap(self):
        choice = str(self.dropdown_colormap.currentText())
        if choice == 'None':
            self.colormap = None
        elif choice == 'Custom':
            self.colormap = self.custom_map
        else:
            self.colormap = maps[choice]
        self.update_graphs()

    def add_data(self,x_datum=None,y_data=None,pos=None,yvalues=None):
        if self.kind == '1d':
            # x_datum is float
            # y_datum is dict {label:value,...}
            for label in self.graphs.keys():
                self.graphs[label].add_datum(x_datum,y_data[label])
        elif self.kind == '2d':
            # pos = [x,y]
            # yvalues is dict {label:value,...}
            for label in self.graphs.keys():
                self.graphs[label].colorplot.add_datum(pos[0],pos[1],yvalues[label])
        
    def update_graphs(self):
        for label in self.graphs.keys():
            if self.kind == '1d':
                self.graphs[label].update_plot()
            elif self.kind == '2d':
                self.graphs[label].colorplot.update_plot(self.colormap)
        self.label_stepsdone.setText("Measurements done: %i"%self.measurements_completed)
        self.progress_bar.setValue(self.measurements_completed)
        self.label_current_rate.setText("Current rate: %f"%self.current_rate)

    def reset_graph_views(self):
        if self.kind == '1d':
            for label in self.graphs.keys():
                self.graphs[label].plot.enableAutoRange()
        elif self.kind == '2d':
            for label in self.graphs.keys():
                self.graphs[label].colorplot.view.enableAutoRange()
                pass


    def update_tab_name(self):
        for tab_pos in range(self.parent.tabs.count()):
            if str(self.parent.tabs.tabText(tab_pos)) == str(self.name):
                newname = 'ID: %i (%s)'%(self.ID,self.status)
                self.parent.tabs.setTabText(tab_pos,newname)
                self.name = newname

    def pause(self):
        if self.status == 'running':
            self.status = 'paused'
            self.update_tab_name()
            self.was_paused=True

    def resume(self):
        if self.status == 'paused':
            self.status = 'running'
            self.update_tab_name()

    def cancel(self):
        if not self.checkbox_cancel.isChecked():
            return
        else:
            self.status='CANCELLED'
            self.parent.IDs.remove(self.ID)
            self.parent.sweepers.pop(self.ID)
            #remove tab
            for tab_pos in range(self.parent.tabs.count()):
                if str(self.parent.tabs.tabText(tab_pos)) == str(self.name):
                    self.parent.tabs.removeTab(tab_pos)
                    return

    def initialize_sweep(self,connection):
        if self.kind == '1d':
            swept = self.det['setting_swept']
            self.inputs[self.to_sweep]=self.xsetting
            connection.servers[swept[0]].select_device(swept[1])
            if len(self.inputs)>1:connection[swept[0]].settings[swept[2]](self.inputs)
            else:connection[swept[0]].settings[swept[2]](self.inputs[0])
        elif self.kind == '2d':
            fast_swept = self.det['fast_swept']
            slow_swept = self.det['slow_swept']
            self.inputs_fast[self.to_sweep_fast]=self.x_setting
            self.inputs_slow[self.to_sweep_slow]=self.y_setting
            
            connection.servers[fast_swept[0]].select_device(fast_swept[1])
            if len(self.inputs_fast)>1:connection[fast_swept[0]].settings[fast_swept[2]](self.inputs_fast)
            else:connection[fast_swept[0]].settings[fast_swept[2]](self.inputs_fast[0])

            connection.servers[slow_swept[0]].select_device(slow_swept[1])
            if len(self.inputs_slow)>1:connection[slow_swept[0]].settings[slow_swept[2]](self.inputs_slow)
            else:connection[slow_swept[0]].settings[slow_swept[2]](self.inputs_slow[0])

    def do_measurement(self,connection):
        '''Takes a measurement of all logged variables and sends the data to the graphs. Does not advance to the next step.'''
        if self.kind == '1d':
            yval = {}
            for setting in self.setting_details:
                connection.servers[setting.server].select_device(setting.device)
                n_entries = len(setting.inputs)
                if n_entries == 0: # if no inputs required:
                    value = connection.servers[setting.server].settings[setting.setting]() # call empty
                elif n_entries == 1: # if one input required
                    value = connection.servers[setting.server].settings[setting.setting](setting.inputs[0]) # call with single value
                else: # if more than one input required
                    value = connection.servers[setting.server].settings[setting.setting](setting.inputs)
                yval.update([[setting.ID,value]])
                
            if self.first_meas:
                self.first_meas = False
                units = {}
                for key in yval.keys():
                    try:
                        unit=str(yval[key].unit)
                    except:
                        unit='unitless'
                    units.update([[key,unit]])
                for setting in self.setting_details:
                    setting.unit = units[setting.ID]
                
            self.add_data(self.xsetting,yval)
            
        elif self.kind == '2d':
            values = {}
            for setting in self.setting_details:
                connection.servers[setting.server].select_device(setting.device)
                n_entries = len(setting.inputs)
                if n_entries == 0: # if no inputs required:
                    value = connection.servers[setting.server].settings[setting.setting]() # call empty
                elif n_entries == 1: # if one input required
                    value = connection.servers[setting.server].settings[setting.setting](setting.inputs[0]) # call with single value
                else: # if more than one input required
                    value = connection.servers[setting.server].settings[setting.setting](setting.inputs)
                values.update([[ setting.ID, value ]])

            if self.first_meas:
                self.first_meas = False
                units = {}
                for key in values.keys():
                    try:
                        unit=str(values[key].unit)
                    except:
                        unit='unitless'
                    units.update([[key,unit]])
                for setting in self.setting_details:
                    setting.unit = units[setting.ID]
                
            self.add_data(pos = [self.x_num,self.y_num],yvalues = values)

            
                

    def advance(self,connection,elapsed):
        ''' Advances the swept setting(s) one step '''

        if self.kind == '1d':
            step = self.stepsize
        elif self.kind == '2d':
            step = self.x_stepsize

        self.total_time  += elapsed        # increment total time elapsed
        self.current_rate = step / elapsed # update the current sweep rate stat
        completed = False

        if self.kind == '1d':
            self.xsetting += self.stepsize
            self.inputs[self.to_sweep] = self.xsetting
            swept = self.det['setting_swept']
            connection[swept[0]].select_device(swept[1])
            
            if len(self.inputs) > 1:
                connection[swept[0]].settings[swept[2]](self.inputs)
            else:
                connection[swept[0]].settings[swept[2]](self.inputs[0])
                
            self.measurements_completed += 1
            if self.measurements_completed >= 1 + self.det['steps']:
                completed = True

            if (self.np_time == 0.0) or (not self.was_paused):
                self.np_swept += self.stepsize; self.np_time += elapsed
            else:self.was_paused = False
                
        elif self.kind == '2d':
            self.measurements_completed += 1
            y_changed = False
            self.x_setting += self.x_stepsize # increment x setting
            self.x_num     += 1               # increment x number
            if self.x_num > self.det['xsteps']: # if x number exceeds row length
                self.x_setting = self.det['xstart'] # reset x setting
                self.x_num = 0                      # reset x number
                self.y_setting += self.y_stepsize   # increment y setting
                self.y_num     += 1                 # increment y number
                y_changed = True                    # y has changed

                if self.y_num > self.det['ysteps']: # sweep is completed
                    completed = True

            if not completed: # if not done, update x setting (it always changes)
                connection.servers[self.det['fast_swept'][0]].select_device(self.det['fast_swept'][1])
                self.inputs_fast[self.to_sweep_fast] = self.x_setting
                if len(self.inputs_fast)>1:connection.servers[self.det['fast_swept'][0]].settings[self.det['fast_swept'][2]](self.inputs_fast)
                else:connection.servers[self.det['fast_swept'][0]].settings[self.det['fast_swept'][2]](self.inputs_fast[0])
            if y_changed: # if y has changed, update y setting
                connection.servers[self.det['slow_swept'][0]].select_device(self.det['slow_swept'][1])
                self.inputs_slow[self.to_sweep_slow] = self.y_setting
                if len(self.inputs_slow)>1:connection.servers[self.det['slow_swept'][0]].settings[self.det['slow_swept'][2]](self.inputs_slow)
                else:connection.servers[self.det['slow_swept'][0]].settings[self.det['slow_swept'][2]](self.inputs_slow[0])
            self.current_delay = self.det['ydelay'] if y_changed else self.det['xdelay']
                    
            if ((self.np_time == 0.0) or (not self.was_paused)) and (self.current_delay == self.det['xdelay']):
                self.np_swept += self.x_stepsize
                self.np_time  += elapsed
            else:self.was_paused = False

        if completed:
            self.status = 'completed'
            self.update_tab_name()
            self.button_cancel.setText("Close")
            t=time.localtime()
            self.finished_time = t
            self.label_complete_time.setText("Completed at: %i/%i/%i %i:%i:%i"%(t.tm_mon,t.tm_mday,t.tm_year,t.tm_hour,t.tm_min,t.tm_sec))
        self.label_complete_rate.setText("Average rate: %f"%(self.np_swept / self.np_time))

        

class customMapWidget(gui.QDialog):
    def __init__(self,parent):
        super(customMapWidget,self).__init__(parent)
        self.parent = parent
        self.doUI()
    def doUI(self):
        self.setModal(True)
        self.grad = pg.GradientWidget(self)
        self.grad.move(0,0)
        self.grad.sigGradientChangeFinished.connect(self.change_gradient)
        self.show()
    def change_gradient(self):
        self.parent.custom_map = self.grad.colorMap()
        self.parent.change_colormap()
        self.parent.update_graphs()
    

class grapherWidget(gui.QMainWindow):
    def __init__(self,password):
        super(grapherWidget,self).__init__()        
        global log
        log = dataLogger(password)
        self.doUI()
    def doUI(self):
        self.tabs = gui.QTabWidget(self)
        self.IDs  = []
        self.sweepers = {}

##        self.add_sweeper(0,{'xlabel':'Test parameter','ylabels':['CHNL1','CHNL2'],'xrng':[0.0,1.0],})
##        self.timer = core.QTimer(self)
##        self.timer.setInterval(100)
##        self.timer.timeout.connect(self.timer_event)
##        self.timer.start()
##        self.x = 0.0
##        self.y1=0.0
##        self.y2=0.0
        
        self.setCentralWidget(self.tabs)
        self.resize(384*3+23*2,192*2+23*8)
        self.show()

    def add_sweeper(self,ID,details,status='running',kind='1d'):
        # details is a dictionary. It contains:
        # xlabel, ylabels, xrange, start_timestamp, start,stop,steps,delay,maxrate setting_swept, settings_measured, func_pause, func_resume, func_cancel ...

        self.IDs.append(ID)
        sweeper = sweepInstance(self,details,ID,status,'ID: %i (%s)'%(ID,status),kind)
        self.sweepers.update([[ID,sweeper]])
        self.tabs.addTab(sweeper,'ID: %i (%s)'%(ID,status))
            

##if __name__=='__main__':
##    app = gui.QApplication(sys.argv)
##    m=grapherWidget()
##    sys.exit(app.exec_())





























