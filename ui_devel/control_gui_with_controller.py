from gui import Ui_Form
from superplot import Superplot
import adr_controller
# Custom modules


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

class PlotDialog(QDialog,Ui_Form):
    # Connects GUI pieces to functions. Grabs data from sim900 and updates gui.
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900=Pyro4.Proxy("PYRONAME:sim900server")
        self.controller=adr_controller.AdrController(self.sim900)
        # Sets up sim900 pyro proxy and AdrController.
        
        
        self.__app = qApp
        self.setupUi(self)
        self.setupLists()
        self.setupTimer()
        
        self.plot=Superplot(self,[self.plotoptions,self.plotoptions2])
        self.plotLayout.insertWidget(0,self.plot.canvas)
        self.toolbar=NavigationToolbar(self.plot.canvas,self)
        self.navbar_layout.insertWidget(0,self.toolbar)
        # Needed for starting the plots.
        
        self.setupSlots()
           
    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(3000)
        
    def setupSlots(self):
        QObject.connect(self.bridge_setpoint_command_value,SIGNAL("editingFinished()"),self.set_bridge_setpoint)
        
        QObject.connect(self.regenerate_button,SIGNAL("clicked()"), self.controller.request_regenerate)
        QObject.connect(self.regulate_button,SIGNAL("clicked()"), self.controller.request_regulate)
        QObject.connect(self.stop_button,SIGNAL("clicked()"), self.controller.request_standby)
        
        QObject.connect(self.plotoptions,SIGNAL("activated(const QString&)"),self.plot.plot_toggle1)
        QObject.connect(self.plotoptions2,SIGNAL("activated(const QString&)"),self.plot.plot_toggle2)
        
    def setupLists(self):
        #Create lists in which bridge-temperature and bridge-setpoint values will be stored
        self.temp_list = []
        self.bridge_setpoint_list = []
        self.magnet_current_list=[]
        self.time_list=[]
        
    def update(self):
        data = self.sim900.fetchDict()
        
        bridge_setpoint = data['bridge_temperature_setpoint']
        #self.bridge_setpoint_value.setText(str(bridge_setpoint))
        temp_bridge = data['bridge_temp_value']
        self.temp_bridge_value.setText(str(temp_bridge))
        temp_3K = data['therm_temperature'][2]
        self.temp_3k_value.setText(str(temp_3K))
        temp_50K = data['therm_temperature'][0]
        self.temp_50k_value.setText(str(temp_50K))
        current = data['dvm_volts'][1]
        self.magnet_current_value.setText(str(current))
        voltage = data['dvm_volts'][0]
        self.magnet_voltage_value.setText(str(voltage))
        
        #Update Temperature and Setpoint Lists
        if len(self.temp_list) < 50:
            self.temp_list.append(temp_bridge)
        elif len(self.temp_list) >= 50:
            del self.temp_list[0]
            self.temp_list.append(temp_bridge)

        if len(self.bridge_setpoint_list) < 50:
            self.bridge_setpoint_list.append(bridge_setpoint)
        elif len(self.bridge_setpoint_list) >= 50:
            del self.bridge_setpoint_list[0]
            self.bridge_setpoint_list.append(bridge_setpoint)
            
        if len(self.magnet_current_list) < 50:
            self.magnet_current_list.append(current)
        elif len(self.magnet_current_list) >= 50:
            del self.magnet_current_list[0]
            self.magnet_current_list.append(current)
            
        if len(self.time_list) < 50:
            self.time_list.append(data["time"])
        elif len(self.time_list) >= 50:
            del self.time_list[0]
            self.time_list.append(data["time"])
            
        #Update plots by calling the draw function.
        self.plot.draw()
        
    def set_bridge_setpoint(self):
        self.controller.request_set_bridge_setpoint(self.bridge_setpoint_command_value.value())
        
def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
