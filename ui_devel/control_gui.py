from gui import Ui_Form

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
import numpy as np
import IPython
import time

import Pyro4

import sys

class superplot():
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

class PlotDialog(QDialog,Ui_Form):
    # Connects GUI pieces to functions. Grabs data from sim900 and updates gui.
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900=Pyro4.Proxy("PYRONAME:sim900server")
        
        self.__app = qApp
        self.setupUi(self)
        self.setupLists()
        self.setupTimer()
        
        self.plot=superplot(self,[self.plotoptions,self.plotoptions2])
        self.plotLayout.insertWidget(0,self.plot.canvas)
        
        self.toolbar=NavigationToolbar(self.plot.canvas,self)
        self.navbar_layout.insertWidget(0,self.toolbar)
        
        self.setupSlots()
           
    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
        
    def setupSlots(self):
        QObject.connect(self.bridge_setpoint_command_value,SIGNAL("editingFinished()"),self.set_bridge_setpoint)
        
        QObject.connect(self.regenerate_button,SIGNAL("clicked()"), self.regenerate)
        QObject.connect(self.regulate_button,SIGNAL("clicked()"), self.regulate)
        QObject.connect(self.stop_button,SIGNAL("clicked()"), self.stop)
        
        QObject.connect(self.plotoptions,SIGNAL("activated(const QString&)"),self.plot.plot_toggle1)
        QObject.connect(self.plotoptions2,SIGNAL("activated(const QString&)"),self.plot.plot_toggle2)
        
    def setupLists(self):
        #Create lists in which bridge-temperature and bridge-setpoint values will be stored
        self.temp_list = []
        self.bridge_setpoint_list = []
        self.magnet_current_list=[]
        
    def update(self):
        data = self.sim900.fetchDict()
        
        bridge_setpoint = data["bridge_temperature_setpoint"]
        #self.bridge_setpoint_value.setText(str(bridge_setpoint))
        temp_bridge = data["bridge_temp_value"]
        self.temp_bridge_value.setText(str(temp_bridge))
        temp_3K = data["therm_temperature"][2]
        self.temp_3k_value.setText(str(temp_3K))
        temp_50K = data["therm_temperature"][0]
        self.temp_50k_value.setText(str(temp_50K))
        current = data["dvm_volts"][1]
        self.magnet_current_value.setText(str(current))
        voltage = data["dvm_volts"][0]
        self.magnet_voltage_value.setText(str(voltage))
        
        #Update Temperature and Setpoint Lists
        if len(self.temp_list) < 500:
            self.temp_list.append(temp_bridge)
        elif len(self.temp_list) >= 500:
            del self.temp_list[0]
            self.temp_list.append(temp_bridge)

        if len(self.bridge_setpoint_list) < 500:
            self.bridge_setpoint_list.append(bridge_setpoint)
        elif len(self.bridge_setpoint_list) >= 500:
            del self.bridge_setpoint_list[0]
            self.bridge_setpoint_list.append(bridge_setpoint)
            
        if len(self.magnet_current_list) < 500:
            self.magnet_current_list.append(current)
        elif len(self.magnet_current_list) >= 500:
            del self.magnet_current_list[0]
            self.magnet_current_list.append(current)
            
        #Update plots by calling the draw function.
        self.plot.draw()
        
        
    def regenerate(self):
        #Changes the Bridge Setpoint
        self.sim900.regenerate()
    def regulate(self):
        #Changes the Bridge Setpoint
        self.sim900.regulate()
    def stop(self):
        #Changes the Bridge Setpoint
        self.sim900.stop()
    def set_bridge_setpoint(self):
        #Changes the Bridge Setpoint
        self.sim900.stop()
    
    def set_bridge_setpoint(self):
        #Changes the Bridge Setpoint
        self.sim900.setBridgeSetpoint(self.bridge_setpoint_command_value.value())
        
        
        
        
        
        
        
        
def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
