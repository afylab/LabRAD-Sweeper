from PyQt4 import QtGui as gui, QtCore as core

class colorBox(gui.QWidget):
    def __init__(self,parent,geometry,color=[255,255,255]):
        super(colorBox,self).__init__(parent)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
        self.setColor(color)
    def setColor(self,color):
        col=gui.QColor(color[0],color[1],color[2])
        self.setStyleSheet("QWidget { background-color: %s }"%col.name())        

class checkBox(gui.QCheckBox):
    def __init__(self,parent,label,pos):
        super(checkBox,self).__init__(parent)
        self.setText(label)
        self.move(pos[0],pos[1])

class outputPanel(gui.QTextEdit):
    def __init__(self,parent,geometry):
        super(outputPanel,self).__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(gui.QTextEdit.NoWrap)
        self.font().setFamily('lucida console')
        self.font().setPointSize(10)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
    def writeTo(self,message):
        self.clear()
        self.insertPlainText(message)

class queryButton(gui.QPushButton):
    def __init__(self,name,parent,toolTip,pos,function):
        super(queryButton,self).__init__(name,parent)
        self.setToolTip(toolTip)
        self.resize(self.sizeHint())
        self.move(pos[0],pos[1])
        self.clicked.connect(function)

class textInput(gui.QLineEdit):
    def __init__(self,parent,toolTip,geometry,placeholder=None):
        super(textInput,self).__init__(parent)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
        if placeholder != None:
            self.setPlaceholderText(str(placeholder))
    def getValue(self):
        return str(self.text())

class intInput(gui.QLineEdit):
    def __init__(self,parent,rng,toolTip,geometry):
        super(intInput,self).__init__(parent)
        self.val = gui.QIntValidator(rng[0],rng[1],self)
        self.setValidator(self.val)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
    def getValue(self):
        try:
            return int(self.text())
        except:
            return(float("NaN"))

class floatInput(gui.QLineEdit):
    def __init__(self,parent,rng,dec,toolTip,geometry,placeholder=None):
        super(floatInput,self).__init__(parent)
        self.val = gui.QDoubleValidator(self)
        self.rng = rng
        self.val.setDecimals(dec)
        self.setValidator(self.val)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
        self.editingFinished.connect(self.enforce)
        if not (toolTip==None):
            self.setToolTip(toolTip)
        if not (placeholder == None):
            self.setPlaceholderText(placeholder)
    def enforce(self):
        #val = float(str(self.text()))
        #print(val)
        if float(str(self.text()))>self.rng[1]:
            self.setText(str(self.rng[1]))
        if float(str(self.text()))<self.rng[0]:
            self.setText(str(self.rng[0]))
    def getValue(self):
        try:
            return float(self.text())
        except:
            return(float("NaN"))

class simpleDropdown(gui.QComboBox):
    def __init__(self,parent,options,geometry,func):
        super(simpleDropdown,self).__init__(parent)
        for opt in options:
            self.addItem(opt)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
        self.currentIndexChanged.connect(func)

class simpleLabel(gui.QLabel):
    def __init__(self,parent,text,geometry,tt=None,color=None):
        super(simpleLabel,self).__init__(parent)
        #self.setGeometry(geometry)
        self.move(geometry[0],geometry[1])
        self.setText(text)
        #self.setToolTip(tt)

class simpleText(gui.QTextEdit):
    def __init__(self,parent,text,geometry,tt=None,color=None):
        super(simpleText,self).__init__(parent)
        self.insertPlainText(text)
        self.setGeometry(geometry[0],geometry[1],geometry[2],geometry[3])
        self.setReadOnly(True)
        self.setLineWrapMode(gui.QTextEdit.NoWrap)
        self.font().setFamily('lucida console')
        self.font().setPointSize(10)
        if not (tt==None):
            self.setToolTip(tt)
        if not (color==None):
            col=gui.QColor(color[0],color[1],color[2])
            self.setStyleSheet("QWidget { background-color: %s }"%col.name())
            
class rotText(gui.QWidget):
    def __init__(self,parent,text,geometry,rot):
        super(rotText,self).__init__(parent)
        self.setParent(parent)
        self.setMinimumSize(geometry[2],geometry[3])
        self.move(geometry[0],geometry[1])
        self.geo=geometry
        self.rot=rot
        self.text=text
        
        self.setVisible(True)
        self.show()
        self.update()
        self.repaint()
    def paintEvent(self,event):
        painter=gui.QPainter(self)
        painter.setPen(core.Qt.black)
        painter.translate(self.geo[0],self.geo[1])
        painter.rotate(self.rot)
        painter.drawText(0,0,self.text)
        painter.end()
    def setRot(self,rot):
        self.rot=rot

class rotLabelRaw(gui.QLabel):
    def __init__(self,parent,text,angle):
        super(rotLabelRaw,self).__init__(parent)
        self.setText(text)
        self.disp_text  = text
        self.disp_angle = angle
    def setDrawOrigin(self,pos):
        self.drawX=pos[0]
        self.drawY=pos[1]

    def paintEvent(self,event):
        painter = gui.QPainter(self)
        painter.setPen(core.Qt.black)
        painter.translate(self.drawX,self.drawY)
        painter.rotate(self.disp_angle)
        painter.drawText(0,0,self.disp_text)
        painter.end()

class rotLabel(gui.QWidget):
    def __init__(self,parent,textOrigin,angle,text,extension=96):
        super(rotLabel,self).__init__(parent)

        self.setGeometry(textOrigin[0]-extension,textOrigin[1]-extension,2*extension,2*extension)
        self.raw = rotLabelRaw(self,text,angle)
        print(self.raw.sizeHint())
        self.raw.setDrawOrigin([
            textOrigin[0]+extension-8,
            textOrigin[1]+extension-8,
            ])

        self.lay=gui.QHBoxLayout()
        self.lay.addWidget(self.raw)
        self.setLayout(self.lay)


class simpleList(gui.QListWidget):
    def __init__(self,parent,geometry,items,recur=None,sel_chg_func=None): # height for line-up is 18*len(items)
        super(simpleList,self).__init__(parent)
        self.move(geometry[0],geometry[1])
        self.resize(geometry[2],geometry[3])
        self.items = items
        for item in items:
            self.addItem(item)
        self.sel_chg_func = sel_chg_func
        self.recur = recur
        #if not (sel_chg_func == None):
        #    self.itemSelectionChanged.connect(sel_chg_func)
        
    def selectionChanged(self,cur,prev):
        if self.recur != None:
            self.sel_chg_func(self.recur)
    #def startDrag(self,actions):
    #    if self.recur != None:
    #        self.sel_chg_func(self.recur)
    def change_items(self,new):
        self.items = new
        self.clear()
        for item in new:
            self.addItem(item)
    def add_item(self,item):
        self.items.append(item)
        self.addItem(item)
    def remove_item(self,to_remove):
        new_items = []
        for item in self.items:
            if item != to_remove:new_items.append(item)
        self.change_items(list(new_items))
    def get_selected(self):
        if len(self.items)==0:return ""
        return self.items[self.currentRow()]

class selector(gui.QWidget):
    def __init__(self,parent,pos,height,column_width,contents):
        super(selector,self).__init__(parent)
        self.cont = contents
        self.cw = column_width
        self.height = height
        self.doUI()
        self.move(pos[0],pos[1])
        self.resize(column_width * self.recursion, height)
        
    def doUI(self):
        selected = self.cont
        done = False
        step = 0
        self.lists = {}
        #if len(self.cont.keys()) == 0:done=True
        while not done:
            if type(selected) == type([]):
                done = True
                if step==0:
                    self.lists.update([[step,simpleList(self,[step*self.cw,0,self.cw,self.height],selected,step,self.update_lists)]])
                else:
                    self.lists.update([[step,simpleList(self,[step*self.cw,0,self.cw,self.height],[],step,self.update_lists)]])
                step += 1
            elif type(selected) == type({}):
                if step==0:
                    self.lists.update([[step,simpleList(self,[step*self.cw,0,self.cw,self.height],sorted(selected.keys()),step,self.update_lists)]])
                else:
                    self.lists.update([[step,simpleList(self,[step*self.cw,0,self.cw,self.height],[],step,self.update_lists)]])
                step += 1
                selected = selected[sorted(selected.keys())[0]]
                
        self.recursion = step
                
    def update_lists(self,which):
        selected = self.cont
        done = False
        step = 0
        while not done:
            if type(selected)==type([]):
                done = True
                if step==which+1:
                    self.lists[step].setCurrentRow(-1)
                    self.lists[step].change_items(selected)
                if step > which+1:
                    self.lists[step].change_items([])
                    #print("blanking step %i"%step)
                step += 1
                
            elif type(selected)==type({}):
                if step==which+1:
                    self.lists[step].setCurrentRow(-1)
                    self.lists[step].change_items(sorted(selected.keys()))
                    #print("changing contents at recursion %i"%step)
                if step > which+1:
                    self.lists[step].change_items([])
                    #print("blanking step %i"%step)
                key = sorted(selected.keys())[self.lists[step].currentRow()]
                #print(key)
                selected = selected[key]
                step += 1

    def get_selection(self,level):
        row  = self.lists[level].currentRow()
        if row == -1:return None
        item = self.lists[level].items[row] 
        return item

    def get_selections(self):
        selections = []
        for n in range(self.recursion):
            try:
                selections.append(self.get_selection(n))
            except:
                return selections
        return selections









