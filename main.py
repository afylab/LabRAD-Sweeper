'''
LabRAD sweeper
main.py
All functionality is contained in the widgets (located in \components\)
Components:
    __init__.py             - exists to make the \components\ directory a package
    widgets.py              - contains some user-defined interface objects (dropdown lists, etc)
    widget_sweeper.py       - has most of the actual sweeper functionality. Takes measurements, performs and manages sweeps.
    widget_parameter_box.py - defines user interface for selecting parameters to pass to swept and recorded settings
    widget_grapher.py       - has the functionality to graph the data that are being collected
    widget_comment_box.py   - provides user interface for writing comments to saved data set
    logger.py               - has the functionality for saving collected data through data vault
    excluded_servers.py     - has a list of LabRAD servers that will be ignored by the sweeper
    colormaps.py            - has the list of available premade colormaps for 2-D graphing

'''

from PyQt4 import QtCore as core, QtGui as gui
import sys,math,time
from os import getenv


from components.widgets import simpleDropdown,simpleList,selector
from components.widget_sweeper import sweeperWidget
from components.widget_grapher import grapherWidget


class interface(gui.QMainWindow):
    def __init__(self,**args):
        super(interface,self).__init__()

        # connect to LabRAD
        self.connect()

        # create internal timer for managing timed events
        self.timer = core.QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.timer_event)
        self.timer.start()

        self.time = time.time()
        self.last_error_check = self.time

    def timer_event(self):
        """This function is called each time the internal timer times out.
           It updates everything that needs to be updated on a timer.
           These include: running any ongoing sweep, and checking for errors
           in new sweep creation."""

        # get the current time
        self.time=time.time()

        # If it's been more than a second since the last check, update the error readout in the new sweep creation tabs.
        if (self.time - self.last_error_check) > 1.0:
            self.cen.s1d.check_warnings()
            self.cen.s2d.check_warnings()
            self.last_error_check = self.time
        
        # manage all running sweeps
        for ID in self.grapher.IDs:
            if self.grapher.sweepers[ID].status == 'running':
                elapsed = self.time - self.grapher.sweepers[ID].time # time since last measurement

                # 1D graphs
                if self.grapher.sweepers[ID].kind=='1d':

                    # If time since last measurement exceeds measurement interval, perform a new measurement.
                    if elapsed >= (self.grapher.sweepers[ID].det['delay']/1000.0):

                        # reset time since last measurement
                        self.grapher.sweepers[ID].time = self.time

                        # x coordinant = the step that the sweep is currently on
                        xval = self.grapher.sweepers[ID].xsetting

                        # this will be populated by each setting that the sweep is recording
                        yval = {}

                        # take measurement
                        self.grapher.sweepers[ID].do_measurement(self.connection)

                        # set swept setting to the next value
                        self.grapher.sweepers[ID].advance(self.connection,elapsed)

                        # update the graph(s)
                        self.grapher.sweepers[ID].update_graphs()

                # 2D graphs
                elif self.grapher.sweepers[ID].kind == '2d':

                    # If time since last measurement exceeds measurement interval, perform a new measurement.
                    if elapsed >= (self.grapher.sweepers[ID].current_delay/1000.0):

                        # reset time since last measurement
                        self.grapher.sweepers[ID].time = self.time

                        # "xn" and "yn" are the x and y integer coordinants of the current position in the 2-D sweep
                        xn = self.grapher.sweepers[ID].x_num
                        yn = self.grapher.sweepers[ID].y_num

                        # again, "values" will be populated by the values of each recorded setting
                        values = {}

                        # take measurement
                        self.grapher.sweepers[ID].do_measurement(self.connection)

                        # advance
                        self.grapher.sweepers[ID].advance(self.connection,elapsed)
                    
                        # update graphs
                        self.grapher.sweepers[ID].update_graphs()

                    


        

    def connect(self):

        # check to see if the password has been set in the registry
        try:
            password = getenv('labradpassword')
            if password == None:
                print("Warning: environment variable 'labradpassword' has not been set yet")
                raise
            self.connection = labrad.connect(password = password)
            self.password = password
            self.doUI()
        except:
            print("Error: LabRAD is not running properly.")

        # otherwise, prompt user for password
        import labrad
        firstAttempt=True
        success=connect=False
        while not success:
            if firstAttempt:pwd,ok=gui.QInputDialog.getText(self,"Password","Enter LabRAD password")
            else:pwd,ok=gui.QInputDialog.getText(self,"Password","Something went wrong. Either thepassword\nwas incorrect or LabRAD isn't running.")
            try:
                self.connection = labrad.connect(password = str(pwd))
                success=True;connect=True
            except:
                if pwd=='exit':success=True
            firstAttempt=False
        if connect:
            self.password = str(pwd)
            self.doUI()
        else:
            gui.qApp.quit()

    def doUI(self):
        self.resize(1024+256,512+64)

        #Title
        self.setWindowTitle("Sweeper settings interface")
        
        #Menu bar
        self.menu = self.menuBar()
        self.menus={
            'program':self.menu.addMenu("&program"),
            'connect':self.menu.addMenu("&connect"),
        }

        action_grapher = gui.QAction(gui.QIcon("missingno.png"),"Show grapher",self)
        action_grapher.setShortcut("Ctrl+G")
        action_grapher.triggered.connect(self.open_grapher)
        self.menus['program'].addAction(action_grapher)

        self.cen = sweeperWidget(self,False)
        self.setCentralWidget(self.cen)

        self.grapher = grapherWidget(self.password)
        self.grapher.setWindowTitle("Grapher")

        self.show()

    def open_grapher(self):
        self.grapher.show()

    def sweep_start(self,kind):
        details = self.cen.get_details(kind)
        self.open_grapher()

        # select the lowest positive ID not currently in use
        # If there are not active IDs, then zero is available, so use it.
        if len(self.grapher.IDs)==0:
            ID=0
        # otherwise, take ID = 1 greater than the highest value currently used.
        else:
            ID = 1+max(self.grapher.IDs)

        # add required data to details, i.e. sweep settings
        if kind == '1d':
            details.update([
                ['xlabel' , details['setting_swept'][2]],
                ['ylabels', [st.rpartition('//')[2] for st in details['settings_read']]],
                ['xrng'   , [details['start'],details['stop']]],
                ['start_timestamp',time.localtime()],                
                ])
        elif kind=='2d':
            details.update([
                ['xlabel',details['fast_swept'][2]],
                ['ylabel',details['slow_swept'][2]],
                ['logged_labels',[st.rpartition('//')[2] for st in details['settings_read']]],
                ['start_timestamp',time.localtime()],
                ])
                

        self.grapher.add_sweeper(ID,details,kind=kind)
        self.grapher.sweepers[ID].initialize_sweep(self.connection) # moves the parameters to their start values


if __name__=='__main__':
    app = gui.QApplication(sys.argv)
    
    i = interface()
    sys.exit(app.exec_())
