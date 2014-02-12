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

class subplot():
    # Defines a plot, contains the methods used to control and build one.
    def __init__(self,parent,control_button):
        # parent and control_button needed as arguments when initialized since connecting QObjects doesn't allow the passing of arguments.
        self.dpi = 72
        self.fig = Figure((9.1, 5.2), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.axes = self.fig.add_subplot(111)
        self.current_list=None
        self.parent=parent
        self.control_button=control_button
        self.canvas.setParent(self.parent)
        
    def draw(self):
        if self.current_list!=None:
            self.axes.cla()
            self.axes.plot(self.current_list)
            self.canvas.draw()
        
    def plot_toggle(self):
        # Plots different lists depending on what the control button orders.
        # This can be made more complex (like plotting T versus I)
        if self.control_button.currentText()=="None":
            self.current_list=None
        elif self.control_button.currentText()=="Bridge Temperature":
            self.current_list=self.parent.temp_list
        elif self.control_button.currentText()=="Bridge Setpoint":
            self.current_list=self.parent.bridge_setpoint_list
        elif self.control_button.currentText()=="Magnet Current":
            self.current_list=self.parent.magnet_current_list

class PlotDialog(QDialog,Ui_Form):
    # Connects GUI pieces to functions. Grabs data from sim900 and updates gui.
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900=Pyro4.Proxy("PYRONAME:sim900server")
        
        self.__app = qApp
        self.setupUi(self)
        self.setupLists()
        self.setupTimer()
        
        self.plot1=subplot(self,self.plotoptions)
        self.plotLayout.insertWidget(0,self.plot1.canvas)
        
        self.plot2=subplot(self,self.plotoptions2)
        self.plotLayout_2.insertWidget(0,self.plot2.canvas)
        
        self.setupSlots()
           
    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(500)
        
    def setupSlots(self):
        QObject.connect(self.plotoptions,SIGNAL("activated(const QString&)"),self.plot1.plot_toggle)
        QObject.connect(self.plotoptions2,SIGNAL("activated(const QString&)"),self.plot2.plot_toggle)
        
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
        self.plot1.draw()
        self.plot2.draw()
        
        
        
        
        
        
        
        
def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
