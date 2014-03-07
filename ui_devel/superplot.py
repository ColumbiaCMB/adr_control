
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.figure import Figure

from PyQt4.QtGui import *

class Superplot():
    # Defines a plot, contains the methods used to control and build one.
    def __init__(self,parent,control_buttons):
        # parent and control_button needed as arguments when initialized since connecting QObjects doesn't allow the passing of arguments.
        self.dpi = 72
        #self.fig = Figure((9.1, 5.2), dpi=self.dpi)
        self.fig = Figure((12.0, 12.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.parent=parent
        self.canvas.setParent(self.parent)
        
        
        self.subplotlist=[]
        
        self.control_button_list=control_buttons
        
        self.current_list=[None,None]
        
        self.line1=None
        self.line2=None
        self.line_list=[self.line1,self.line2]
        
        self.axes1=self.fig.add_subplot(211)
        self.axes2=self.fig.add_subplot(212)
        self.axes_list=[self.axes1,self.axes2]
        
        self.subplotlist.append([self.axes1,self.current_list[0],self.control_button_list[0]])
        self.subplotlist.append([self.axes2,self.current_list[1],self.control_button_list[1]])
        
    def draw(self):
        for i in range(len(self.axes_list)):
            x=self.parent.time_list
            y=self.current_list[i]
            if y==None:
                break
            if self.line_list[i]:
                self.line_list[i].set_xdata(x)
                self.line_list[i].set_ydata(y)
            else:
                self.line_list[i],=self.axes_list[i].plot(x,y)
            self.axes_list[i].relim()
            self.axes_list[i].autoscale_view()
        self.canvas.draw()
        
    def plot_toggle1(self):
        # Plots different lists depending on what the control button orders.
        # This can be made more complex (like plotting T versus I)
        if self.control_button_list[0].currentText()=="Pause":
            self.current_list[0]=None
        elif self.control_button_list[0].currentText()=="Bridge Temperature":
            self.current_list[0]=self.parent.temp_list
        elif self.control_button_list[0].currentText()=="Magnet Current":
            self.current_list[0]=self.parent.magnet_current_list
    def plot_toggle2(self):
        # Plots different lists depending on what the control button orders.
        # This can be made more complex (like plotting T versus I)
        if self.control_button_list[1].currentText()=="Pause":
            self.current_list[1]=None
        elif self.control_button_list[1].currentText()=="Bridge Temperature":
            self.current_list[1]=self.parent.temp_list
        elif self.control_button_list[1].currentText()=="Magnet Current":
            self.current_list[1]=self.parent.magnet_current_list
