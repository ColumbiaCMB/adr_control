
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.figure import Figure

from PyQt4.QtGui import *

class Superplot():
    # Defines a plot, contains the methods used to control and build one.
    def __init__(self,parent,control_buttons):
        # parent and control_button needed as arguments when initialized since connecting QObjects doesn't allow the passing of arguments.
        self.dpi = 72
        self.fig = Figure((9.1, 5.2), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.parent=parent
        self.canvas.setParent(self.parent)
        
        self.current_list=[None,None]
        self.subplotlist=[]
        self.control_buttons=control_buttons
        
        self.subplotlist.append([self.fig.add_subplot(211),self.current_list[0],control_buttons[0]])
        self.subplotlist.append([self.fig.add_subplot(212),self.current_list[1],control_buttons[1]])
            
    def draw(self):
        for subplot in self.subplotlist:
            if subplot[1] != None:
                subplot[0].cla()
                subplot[0].plot(subplot[1])
        self.canvas.draw()
            
    def plot_toggle1(self):
        # Plots different lists depending on what the control button orders.
        # This can be made more complex (like plotting T versus I)
        if self.control_buttons[0].currentText()=="None":
            self.subplotlist[0][1]=None
        elif self.control_buttons[0].currentText()=="Bridge Temperature":
            self.subplotlist[0][1]=self.parent.temp_list
        elif self.control_buttons[0].currentText()=="Bridge Setpoint":
            self.subplotlist[0][1]=self.parent.bridge_setpoint_list
        elif self.control_buttons[0].currentText()=="Magnet Current":
            self.subplotlist[0][1]=self.parent.magnet_current_list
            
    def plot_toggle2(self):
        # Two plot_toggles are needed, since QOBject.connect can't take arguments. Otherwise, this could easily be one method.
        if self.control_buttons[1].currentText()=="None":
            self.subplotlist[1][1]=None
        elif self.control_buttons[1].currentText()=="Bridge Temperature":
            self.subplotlist[1][1]=self.parent.temp_list
        elif self.control_buttons[1].currentText()=="Bridge Setpoint":
            self.subplotlist[1][1]=self.parent.bridge_setpoint_list
        elif self.control_buttons[1].currentText()=="Magnet Current":
            self.subplotlist[1][1]=self.parent.magnet_current_list
