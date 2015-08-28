from PyQt4 import QtGui as gui,QtCore as core
import sys,time

from widgets import queryButton,simpleText,textInput,simpleList

def format_comment(comment,nl,trail='...',delimiter=' - '):
    name = comment[0]
    if len(name) > nl:
        name = name[:nl-len(trail)]+trail
    elif len(name) < nl:
        name += ' ' * (nl - len(name))
    return name+delimiter+comment[1]

class commentBoxWidget(gui.QDialog):
    def __init__(self,parent,ls=23,ul=128,cl=384):
        super(commentBoxWidget,self).__init__(parent)
        self.parent = parent

        self.ls=ls # line spacing
        self.ul=ul # "user" length
        self.cl=cl # "comment" length

        self.name_display_length = 16

        self.comments = []

        self.doUI()

    def doUI(self):
        self.setModal(True)

        self.input_user    = textInput(self,'',[0      , 0, self.ul, self.ls],'user')
        self.input_comment = textInput(self,'',[self.ul, 0, self.cl, self.ls],'comment body')
        self.button_add    = queryButton("Add",self,'',[0,self.ls],self.add_comment)

        self.label_user    = simpleText(self,"User"   ,[0      , self.ls*3, self.ul        , self.ls  ])
        self.label_comment = simpleText(self,"Comment",[self.ul, self.ls*3, self.cl        , self.ls  ])

        self.list_comments = simpleList(self          ,[0      , self.ls*4, self.ul+self.cl, self.ls*4], [])
        self.list_comments.setFont(gui.QFont("Lucida Console",8))

        self.button_remove = queryButton('Remove selected', self, '', [0                 , self.ls*8],self.remove_selected)
        self.button_clear  = queryButton('Clear all'      , self, '', [self.ul-39        , self.ls*8],self.remove_all     )
        self.button_write  = queryButton('Write comments' , self, '', [self.ul+self.cl-84, self.ls*8],self.write_comments )

        self.setFixedSize(self.ul+self.cl,self.ls*9)
        self.setWindowTitle("Comment box")

        self.show()

    def add_comment(self):
        name = self.input_user.getValue()
        cont = self.input_comment.getValue()
        if not cont:return False
        if not name:name = 'anonymous'

        self.comments.append([name,cont])
        self.list_comments.add_item(format_comment([name,cont],self.name_display_length))
        self.input_comment.setText('')

    def remove_selected(self):
        num = self.list_comments.currentRow()
        if num < 0:return False
        items = list(self.list_comments.items)
        items.pop(num)
        self.comments.pop(num)
        self.list_comments.change_items(items)

    def remove_all(self):
        self.list_comments.change_items([])
        self.comments = []

    def write_comments(self):
        if len(self.comments):
            self.parent.send_comments(self.comments)
            self.remove_all()
            self.accept()






test = True
if __name__ == '__main__' and test:
    app=gui.QApplication(sys.argv)
    t = commentBoxWidget(None)
    sys.exit(app.exec_())
