import gui
from superplot import Superplot
import adr_controller
import data_logger
import message_logger
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
import logging

import Pyro4

import sys


class PlotDialog(QDialog,gui.Ui_Form):
    # Connects GUI pieces to functions. Grabs data from sim900 and updates gui.
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900=Pyro4.Proxy("PYRONAME:sim900server")
        self.cryomech=Pyro4.Proxy("PYRONAME:cryomechserver")
        self.controller=adr_controller.AdrController(client=self.sim900,gui_input=True,gui_message_display=self.pass_to_logger)
        self.data_logger=data_logger.DataFile()
        self.message_logger=message_logger.MessageFile(method=self.push_message)
        # Sets up sim900 pyro proxy, AdrController, and data_logger - which records data in a netcdf format.
        
        self.last_sim900_timestamp=0
        self.last_cryomech_timestamp=0
        # Used to make sure dictionaries are fully populated before the GUI logs them.
        
        self.__app = qApp
        self.setupUi(self)
        self.setupLists()
        self.setupTimer()
        # Timer for update
        self.setupTimer2()
        # Timer for checking alerts from controller
        self.setupTimer3()
        # Timer for displaying queued messages from controller
        
        self.plot=Superplot(self)
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
        #QObject.connect(self.bridge_setpoint_command_value,SIGNAL("editingFinished()"),self.set_bridge_setpoint)
        
        QObject.connect(self.regenerate_button,SIGNAL("clicked()"), self.request_regenerate)
        QObject.connect(self.regulate_button,SIGNAL("clicked()"), self.request_regulate)
        QObject.connect(self.stop_button,SIGNAL("clicked()"), self.request_standby)
        
        QObject.connect(self.plotoptions,SIGNAL("activated(const QString&)"),self.plot_toggle1)
        QObject.connect(self.plotoptions2,SIGNAL("activated(const QString&)"),self.plot_toggle2)
        
    def setupLists(self):
        #Create lists in which bridge-temperature and bridge-setpoint values will be stored
        self.temp_list = []
        self.pid_setpoint_list = []
        self.magnet_current_list=[]
        self.time_list=[]
        self.message_queue=[]
        # This is for queued messages to the message_value box.
        
    def update(self):
        sim900_data = self.sim900.fetch_dict()
        if sim900_data['time']==self.last_sim900_timestamp:
            # Throws out the dictionary and ends if the timestamp hasn't changed.
            return
        else:
            self.last_sim900_timestamp=sim900_data['time']
            self.data_logger.update(sim900_data)
            
        cryomech_data=self.cryomech.fetch_dict()
        if cryomech_data['time']==self.last_cryomech_timestamp:
            return
        else:
            self.last_cryomech_timestamp=sim900_data['time']
            self.data_logger.update(cryomech_data)
        
        
        temp_bridge = sim900_data['bridge_temp_value']
        self.temp_bridge_value.setText(str(temp_bridge))
        temp_floating_diode_value = sim900_data['therm_temperature2']
        self.temp_floating_diode_value.setText(str(temp_floating_diode_value))
        temp_magnet_diode_value = sim900_data['therm_temperature1']
        self.temp_magnet_diode_value.setText(str(temp_magnet_diode_value))
        temp_50K = sim900_data['therm_temperature0']
        self.temp_50k_value.setText(str(temp_50K))
        current = sim900_data['dvm_volts1']
        self.magnet_current_value.setText(str(current))
        voltage = sim900_data['dvm_volts0']
        self.magnet_voltage_value.setText(str(voltage))
        
        self.bridge_overload_status_value.setText(str(sim900_data['bridge_overload_status']))
        self.bridge_autorange_gain_value.setText(str(sim900_data['bridge_autorange_gain']))
        
        self.pid_output_value.setText(str(sim900_data['pid_output_mon']))
        pid_setpoint = sim900_data['pid_setpoint']
        self.pid_setpoint_value.setText(str(pid_setpoint))
        self.pid_manual_output_value.setText(str(sim900_data['pid_manual_out']))
        if sim900_data['pid_manual_status'] == 1:
            self.pid_mode_value.setText('PID')
        if sim900_data['pid_manual_status'] == 0:
            self.pid_mode_value.setText('MAN')
            
        self.state_value.setText(self.controller.state)
        
        # Cryomech values
        self.temp_water_in_value.setText(str(cryomech_data['temp_water_in']))
        self.temp_water_out_value.setText(str(cryomech_data['temp_water_out']))
        self.temp_helium_value.setText(str(cryomech_data['temp_helium']))
        self.temp_oil_value.setText(str(cryomech_data['temp_oil']))
        self.avg_pressure_high_value.setText(str(cryomech_data['avg_pressure_high']))
        self.avg_pressure_low_value.setText(str(cryomech_data['avg_pressure_low']))
        
        #Update Temperature and Setpoint Lists
        if len(self.temp_list) < 500:
            self.temp_list.append(temp_bridge)
        elif len(self.temp_list) >= 500:
            del self.temp_list[0]
            self.temp_list.append(temp_bridge)

        if len(self.pid_setpoint_list) < 500:
            self.pid_setpoint_list.append(pid_setpoint)
        elif len(self.pid_setpoint_list) >= 500:
            del self.pid_setpoint_list[0]
            self.pid_setpoint_list.append(pid_setpoint)
            
        if len(self.magnet_current_list) < 500:
            self.magnet_current_list.append(current)
        elif len(self.magnet_current_list) >= 500:
            del self.magnet_current_list[0]
            self.magnet_current_list.append(current)
            
        if len(self.time_list) < 500:
            self.time_list.append(sim900_data["time"])
        elif len(self.time_list) >= 500:
            del self.time_list[0]
            self.time_list.append(sim900_data["time"])
            
        #Update plots by calling the draw function.
        
        if self.autoscale_x.isChecked():
            self.plot.autoscale_x=True
        else:
            self.plot.autoscale_x=False
        if self.autoscale_y.isChecked():
            self.plot.autoscale_y=True
        else:
            self.plot.autoscale_y=False
        self.plot.draw()
        
    def plot_toggle1(self, command):
        # Calls the plot_toggle method of the superplot with the correct command and index.
        self.plot.plot_toggle(command,0)
    def plot_toggle2(self, command):
        self.plot.plot_toggle(command,1)
        
### Methods that request actions from the controller. Connected to buttons. ###
        
    def request_regenerate(self):
        setpoint=self.setpoint_value.value()
        current=self.peak_current_value.value()
        rru=self.ramp_rate_up_value.value()
        rrd=self.ramp_rate_down_value.value()
        step=self.pid_step_value.value()
        dwell=self.dwell_time_value.value()
        pause=self.pause_time_value.value()
        self.controller.request_regenerate(pid_setpoint_goal=setpoint,peak_current=current, ramp_rate_up=rru, ramp_rate_down=rrd, pid_step=step, pause_time=pause, dwell_time=dwell)
        
    def request_regulate(self):
        setpoint=self.setpoint_value.value()
        step=self.pid_step_value.value()
        rru=self.ramp_rate_up_value.value()
        self.controller.request_regulate(pid_setpoint_goal=setpoint,pid_step=step, ramp_rate_up=rru)
        
    def request_standby(self):
        rrd=self.ramp_rate_down_value.value()
        self.controller.request_standby(ramp_down=rrd)
        
### Methods that deal with the controller requesting user input. ###
        
    def raise_message_box(self,msg):
        msg_box=QMessageBox()
        msg_box.setText(msg)
        msg_box.setModal(False)
        
        action_button=QPushButton('OK')
        action_button.clicked.connect(lambda: self.respond_to_controller(msg))
        action_button.setFocusPolicy(Qt.NoFocus)
        msg_box.addButton(action_button, QMessageBox.ActionRole)
        
        msg_box.exec_()
        
    def respond_to_controller(self,message):
        if message==self.controller.message_for_gui:
        # Makes sure the user is responding to the correct message.
            self.controller.gui_response=True
        
    def check_for_message(self):
        if self.controller.message_for_gui!=None:
            self.raise_message_box(self.controller.message_for_gui)
                
    def setupTimer2(self):
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.check_for_message)
        self.timer2.start(2000)
        
### Methods that deal with displaying messages from GUI (and logging them). ###
        
    def push_message(self,message):
        # Pushes messages to the message_queue
        self.message_queue.append(message)
        
    def display_message(self):
        # Grabs the first value in the message_queue and displays it on message_value
        if len(self.message_queue)>0:
            msg=self.message_queue.pop(0)
            self.message_value.append(msg)
        
    def setupTimer3(self):
        # Causes the display message method to trigger every 300 ms
        self.timer3=QTimer()
        self.timer3.timeout.connect(self.display_message)
        self.timer3.start(300)
        
    def pass_to_logger(self, message):
        self.message_logger.log(message)
        
    
        
def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
