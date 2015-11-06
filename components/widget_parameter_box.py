from PyQt4 import QtGui as gui,QtCore as core
import sys,time

from widgets import queryButton,simpleText,textInput,simpleList,floatInput

def force_length(string,length,trail='...',filler=' '):
    l = len(string)
    if l > length:
        return string[:length-len(trail)]+trail
    elif l < length:
        return string + filler * (length-l)
    else:
        return string

def format_parameter(parameter,nl,ul,delimeter):
    name  = parameter[0]
    units = parameter[1]
    return force_length(name,nl)+delimeter+force_length(units,ul)+delimeter+str(parameter[2])

class nameWarning(gui.QErrorMessage):
    """User to warn user when attempting to create two parametes with the same name"""
    def __init__(self,parent):
        super(nameWarning,self).__init__(parent)
        self.parent = parent
        self.doUI()
    def doUI(self):
        self.setWindowTitle("Name in use")
        self.showMessage("The parameter name entered is already in use (has been defined already.)")
        

class parameterBoxWidget(gui.QDialog):
    """User interface for creating parameters for a data set."""
    def __init__(self,parent,used_parameters,ls=23,nl=256,ul=128,vl=128):
        super(parameterBoxWidget,self).__init__(parent)
        self.parent = parent

        self.ls=ls # line spacing
        self.nl=nl # name  length
        self.ul=ul # units length
        self.vl=vl # value length
        
        self.name_display_length  = 35
        self.units_display_length = 16
        self.delimeter            = '  '

        self.pre_existing_parameters = used_parameters[:]
        self.used_parameters = used_parameters[:]
        self.parameters = []

        self.doUI()

    def doUI(self):
        self.setModal(True)

        nolimit = [-float('inf'),float('inf')]

        self.input_name  = textInput( self,'',[0              , 0, self.nl, self.ls],'Parameter name' )
        self.input_units = textInput( self,'',[self.nl        , 0, self.ul, self.ls],'Parameter units')
        self.input_value = floatInput(self,nolimit,8,'',[self.nl+self.ul, 0, self.vl, self.ls],'Parameter value')
        self.button_add  = queryButton("Add",self,'',[0,self.ls],self.add_parameter)

        self.label_name  = simpleText(self,"Parameter name" , [0              , self.ls*3, self.nl, self.ls])
        self.label_units = simpleText(self,"Parameter units", [self.nl        , self.ls*3, self.ul, self.ls])
        self.label_value = simpleText(self,"Parameter value", [self.nl+self.ul, self.ls*3, self.vl, self.ls])

        self.list_parameters = simpleList(self          ,[0      , self.ls*4, self.nl+self.ul+self.vl, self.ls*4], [])
        self.list_parameters.setFont(gui.QFont("Lucida Console",8))

        self.button_remove = queryButton('Remove selected'  , self, '', [0                         , self.ls*8],self.remove_selected)
        self.button_clear  = queryButton('Clear all'        , self, '', [self.nl-167               , self.ls*8],self.remove_all     )
        self.button_write  = queryButton('Write parameters' , self, '', [self.nl+self.ul+self.vl-92, self.ls*8],self.write_parameters )

        self.setFixedSize(self.nl+self.ul+self.vl,self.ls*9)
        self.setWindowTitle("Parameter box")

        self.show()

    def add_parameter(self):
        
        name  = self.input_name.getValue()
        units = self.input_units.getValue()
        value = self.input_value.getValue()

        if not all([name,units]):
            return False
        if str(value) == 'nan':
            return False

        if name in self.used_parameters:
            self.warn_name_used()
            return False

        self.parameters.append([name,units,value])
        self.list_parameters.add_item(format_parameter([name,units,value],self.name_display_length,self.units_display_length,self.delimeter))
        self.used_parameters.append(name)

    def remove_selected(self):
        num = self.list_parameters.currentRow()
        if num < 0:return False
        items = list(self.list_parameters.items)
        items.pop(num)
        popped = self.parameters.pop(num)
        self.list_parameters.change_items(items)
        self.used_parameters.remove(popped[0])

    def remove_all(self):
        self.list_parameters.change_items([])
        self.parameters = []
        self.used_parameters = self.pre_existing_parameters[:]

    def write_parameters(self):
        if len(self.parameters):
            self.parent.send_parameters(self.parameters)
            self.remove_all()
            self.accept()

    def warn_name_used(self):
        acc = nameWarning(self)

test = True
if __name__ == '__main__' and test:
    app=gui.QApplication(sys.argv)
    t = parameterBoxWidget(None,['a'])
    sys.exit(app.exec_())
