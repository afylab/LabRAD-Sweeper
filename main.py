from PyQt4 import QtCore as core, QtGui as gui
import sys,math,time


from components.widgets import simpleDropdown,simpleList,selector
from components.widget_sweeper import sweeperWidget
from components.widget_grapher import grapherWidget

global sample_contents
sample_contents = {
    'l1':{'a':['1','2'],'b':['3','4']},
    'l2':{'c':['5','6'],'d':['7','8']},
    'l3':{'d':['9','0'],'e':['%','^']},
    }



class interface(gui.QMainWindow):
    def __init__(self,**args):
        super(interface,self).__init__()
        self.connect()
        #self.sweep_running=False        
        
        self.timer = core.QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.timer_event)
        self.timer.start()

        self.time = time.time()
        self.last_error_check = self.time

        #self.time = time.time()
        #self.times = []
        #self.num = 0

        ## connections
        # self.connection.sr_7280_lockin.select_device(0)
        # self.connection.ad5764_dcbox.select_device(0)

    def timer_event(self):
        self.time=time.time()

        #[!!!!] rotate label
        # self.cen.rl1.setRot(self.cen.rl1.rot + 0.1)
        #self.cen.rl1.repaint()

        # error checking
        if (self.time - self.last_error_check) > 1.0:
            self.cen.s1d.check_warnings()
            self.cen.s2d.check_warnings()
            self.last_error_check = self.time
        
        # 1D sweeps
        for ID in self.grapher.IDs:
            if self.grapher.sweepers[ID].status == 'running':
                elapsed = self.time - self.grapher.sweepers[ID].time # time since last measurement

                if self.grapher.sweepers[ID].kind=='1d':
                    if elapsed >= (self.grapher.sweepers[ID].det['delay']/1000.0): # do new one if this is longer than delay
                        self.grapher.sweepers[ID].time = self.time       # set time to current time

                        xval = self.grapher.sweepers[ID].xsetting
                        yval = {}

                        # take measurement
                        self.grapher.sweepers[ID].do_measurement(self.connection)

                        # set swept setting to the next value
                        self.grapher.sweepers[ID].advance(self.connection,elapsed)

                        # update the graph(s)
                        self.grapher.sweepers[ID].update_graphs()

                elif self.grapher.sweepers[ID].kind == '2d':

                    if elapsed >= (self.grapher.sweepers[ID].current_delay/1000.0):
                        self.grapher.sweepers[ID].time = self.time       # set time to current time

                        xn = self.grapher.sweepers[ID].x_num
                        yn = self.grapher.sweepers[ID].y_num
                        values = {}

                        # take measurement
                        self.grapher.sweepers[ID].do_measurement(self.connection)

                        # advance
                        self.grapher.sweepers[ID].advance(self.connection,elapsed)
                    
                        # update graphs
                        self.grapher.sweepers[ID].update_graphs()

                    


        

    def connect(self):
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

        #s=selector(self,[0,0],92,64,sample_contents)
        #self.setCentralWidget(s)

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

        # select ID
        if len(self.grapher.IDs)==0:
            ID=0
        else:
            ID = 1+max(self.grapher.IDs)

        # add required data to details
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
