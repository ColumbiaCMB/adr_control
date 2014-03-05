import gui
from superplot import Superplot
import adr_controller
import data_logger
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
import threading

import Pyro4

import sys

class PlotDialog(QDialog,gui.Ui_Form):
    # Connects GUI pieces to functions. Grabs data from sim900 and updates gui.
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900=Pyro4.Proxy("PYRONAME:sim900server")
        self.controller=adr_controller.AdrController(client=self.sim900,gui_input=True)
        self.data_logger=data_logger.DataFile()
        # Sets up sim900 pyro proxy and AdrController.
        
        self.__app = qApp
        self.setupUi(self)
        self.setupLists()
        self.setupTimer()
        self.setupTimer2()
        
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
        
        QObject.connect(self.regenerate_button,SIGNAL("clicked()"), self.request_regenerate)
        QObject.connect(self.regulate_button,SIGNAL("clicked()"), self.request_regulate)
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
        data = self.sim900.fetch_dict()
        self.data_logger.update(data)
        
        bridge_setpoint = data['bridge_temperature_setpoint']
        #self.bridge_setpoint_value.setText(str(bridge_setpoint))
        temp_bridge = data['bridge_temp_value']
        self.temp_bridge_value.setText(str(temp_bridge))
        temp_3K = data['therm_temperature2']
        self.temp_3k_value.setText(str(temp_3K))
        temp_50K = data['therm_temperature0']
        self.temp_50k_value.setText(str(temp_50K))
        current = data['dvm_volts1']
        self.magnet_current_value.setText(str(current))
        voltage = data['dvm_volts0']
        self.magnet_voltage_value.setText(str(voltage))
        
        self.pid_output_value.setText(str(data['pid_output_mon']))
        self.pid_setpoint_value.setText(str(data['pid_setpoint']))
        self.pid_manual_output_value.setText(str(data['pid_manual_out']))
        if data['pid_manual_status'] == 1:
            self.pid_mode_value.setText('PID')
        if data['pid_manual_status'] == 0:
            self.pid_mode_value.setText('MAN')
        
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
        
    def request_regenerate(self):
        self.controller.request_regenerate(3.0)
        
    def request_regulate(self):
        self.controller.request_regulate(3.0)
        
    def set_bridge_setpoint(self):
        #self.controller.request_set_bridge_setpoint(self.bridge_setpoint_command_value.value())
        pass
        
    def raise_message_box(self,msg):
        msg_box=QMessageBox()
        msg_box.setText(msg)
        msg_box.setModal(False)
        
        action_button=QPushButton('OK')
        action_button.clicked.connect(self.respond_to_controller)
        test_button=msg_box.addButton(action_button, QMessageBox.ActionRole)
        #cancel_button=msg_box.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        
        msg_box.exec_()
        
    def respond_to_controller(self):
        self.controller.gui_response=True
        
    def check_for_message(self):
        print 'check for controller message'
        if self.controller.message_for_gui!=None:
            'controller message found'
            self.raise_message_box(self.controller.message_for_gui)
                
    def setupTimer2(self):
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.check_for_message)
        self.timer2.start(1000)
        
def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
