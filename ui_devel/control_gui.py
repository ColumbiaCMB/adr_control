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


class PlotDialog(QDialog,Ui_Form):
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900=Pyro4.Proxy("PYRONAME:sim900server")
        
        self.__app = qApp
        self.setupUi(self)
        self.setupTimer()
        
        
        self.dpi = 72
        self.fig = Figure((9.1, 5.2), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.plotLayout.insertWidget(0,self.canvas)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.axes = self.fig.add_subplot(211)
        self.axes = self.fig.add_subplot(212)
        
        
    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(500)
        
    def update(self):
    
        #Fetches values from sim900 and updates value boxes
        data = self.sim900.fetchDict()
        
        bridge_setpoint = data["bridge_temperature_setpoint"]
        self.bridge_setpoint_value.setText(str(bridge_setpoint))
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



def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
